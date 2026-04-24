"""
persistent_memory.py
A JSON-file-backed AgentMemory that:
  - Loads all previously learned Q-SQL pairs from memory_store.json on startup
  - Auto-saves every new successful tool usage to disk immediately
  - Wraps DemoAgentMemory so search/retrieval still works in RAM
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from vanna.capabilities.agent_memory import (
    AgentMemory,
    TextMemory,
    TextMemorySearchResult,
    ToolMemory,
    ToolMemorySearchResult,
)
from vanna.core.tool import ToolContext
from vanna.integrations.local.agent_memory import DemoAgentMemory

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STORE_PATH = os.path.join(BASE_DIR, "memory_store.json")


class PersistentAgentMemory(AgentMemory):
    """
    AgentMemory that persists tool-usage memories to a JSON file.

    On startup:
      - Loads all previously saved ToolMemory entries from `store_path`
      - Injects them into an in-memory DemoAgentMemory for fast similarity search

    On every new save_tool_usage call:
      - Delegates to DemoAgentMemory (RAM)
      - Appends the new entry to the JSON file immediately

    Text memories are NOT persisted (they are transient session context).
    """

    def __init__(self, store_path: str = DEFAULT_STORE_PATH, max_items: int = 10_000):
        self._demo = DemoAgentMemory(max_items=max_items)
        self._store_path = store_path
        self._file_lock = asyncio.Lock()
        self._loaded = False

    # ── Private helpers ────────────────────────────────────────────────────

    def _read_store(self) -> list[dict]:
        """Read the JSON store from disk. Returns [] if missing/corrupt."""
        if not os.path.exists(self._store_path):
            return []
        try:
            with open(self._store_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read memory store %s: %s", self._store_path, exc)
            return []

    def _append_to_store(self, entry: dict) -> None:
        """Append a single ToolMemory dict to the JSON file (thread-safe via lock)."""
        records = self._read_store()
        records.append(entry)
        with open(self._store_path, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, ensure_ascii=False)

    # ── Startup ────────────────────────────────────────────────────────────

    async def load_from_disk(self) -> int:
        """
        Load persisted memories into RAM.
        Call this once at application startup (e.g. in FastAPI lifespan).
        Returns the number of memories loaded.
        """
        if self._loaded:
            return 0

        records = self._read_store()
        loaded = 0

        # We need a dummy context to satisfy the DemoAgentMemory.save_tool_usage signature
        dummy_ctx = _DummyToolContext()

        for rec in records:
            try:
                await self._demo.save_tool_usage(
                    question=rec["question"],
                    tool_name=rec["tool_name"],
                    args=rec["args"],
                    context=dummy_ctx,  # type: ignore[arg-type]
                    success=rec.get("success", True),
                    metadata=rec.get("metadata", {}),
                )
                loaded += 1
            except Exception as exc:
                logger.warning("Skipping corrupt memory record: %s", exc)

        self._loaded = True
        logger.info("PersistentAgentMemory: loaded %d memories from %s", loaded, self._store_path)
        return loaded

    # ── AgentMemory interface ──────────────────────────────────────────────

    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save to RAM and persist to disk."""
        # Save to in-memory store (handles deduplication / FIFO eviction)
        await self._demo.save_tool_usage(
            question=question,
            tool_name=tool_name,
            args=args,
            context=context,
            success=success,
            metadata=metadata,
        )

        # Persist to disk (only successful usages are worth keeping)
        if success:
            entry = {
                "memory_id": str(uuid.uuid4()),
                "question": question,
                "tool_name": tool_name,
                "args": args,
                "success": success,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
            }
            async with self._file_lock:
                self._append_to_store(entry)
            logger.debug("PersistentAgentMemory: saved '%s' to disk", question)

    async def save_text_memory(self, content: str, context: ToolContext) -> TextMemory:
        """Text memories are in-RAM only (transient)."""
        return await self._demo.save_text_memory(content, context)

    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None,
    ) -> List[ToolMemorySearchResult]:
        return await self._demo.search_similar_usage(
            question, context,
            limit=limit,
            similarity_threshold=similarity_threshold,
            tool_name_filter=tool_name_filter,
        )

    async def search_text_memories(
        self,
        query: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[TextMemorySearchResult]:
        return await self._demo.search_text_memories(
            query, context, limit=limit, similarity_threshold=similarity_threshold
        )

    async def get_recent_memories(
        self, context: ToolContext, limit: int = 10
    ) -> List[ToolMemory]:
        return await self._demo.get_recent_memories(context, limit)

    async def get_recent_text_memories(
        self, context: ToolContext, limit: int = 10
    ) -> List[TextMemory]:
        return await self._demo.get_recent_text_memories(context, limit)

    async def delete_text_memory(self, context: ToolContext, memory_id: str) -> bool:
        return await self._demo.delete_text_memory(context, memory_id)

    async def delete_by_id(self, context: ToolContext, memory_id: str) -> bool:
        deleted = await self._demo.delete_by_id(context, memory_id)
        if deleted:
            # Remove from disk too
            async with self._file_lock:
                records = self._read_store()
                records = [r for r in records if r.get("memory_id") != memory_id]
                with open(self._store_path, "w", encoding="utf-8") as fh:
                    json.dump(records, fh, indent=2, ensure_ascii=False)
        return deleted

    async def clear_memories(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None,
    ) -> int:
        count = await self._demo.clear_memories(context, tool_name, before_date)
        # Sync disk: if clearing all, just wipe the file
        if tool_name is None and before_date is None:
            async with self._file_lock:
                with open(self._store_path, "w", encoding="utf-8") as fh:
                    json.dump([], fh)
        return count

    # ── Convenience ───────────────────────────────────────────────────────

    @property
    def store_path(self) -> str:
        return self._store_path

    def count_on_disk(self) -> int:
        """Return how many records are currently stored in the JSON file."""
        return len(self._read_store())


# ── Internal helper ────────────────────────────────────────────────────────

class _DummyToolContext:
    """Minimal stand-in for ToolContext used during disk-load seeding."""
    user = None
    conversation_id = "load-from-disk"
    request_id = "load-from-disk"
    agent_memory = None
    metadata: Dict[str, Any] = {}
    observability_provider = None
