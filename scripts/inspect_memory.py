import asyncio
import sys

from app.agent_manager import agent_manager
from vanna.core.tool import ToolContext
from vanna.core.user import User

async def inspect_memory():
    database_id = sys.argv[1] if len(sys.argv) > 1 else "clinic"
    bundle = agent_manager.get_bundle(database_id)
    agent_memory = bundle.memory

    # 1. Load from disk
    print(f"Loading persistent memory for {database_id}...")
    loaded_count = await agent_memory.load_from_disk()
    print(f"Loaded {loaded_count} memories from disk.")
    
    # 2. Setup context to query it
    ctx = ToolContext(
        user=User(id="admin", username="admin", group_memberships=["admin"]),
        conversation_id="inspect-session",
        request_id="inspect-request",
        agent_memory=agent_memory
    )
    
    # 3. Retrieve and print
    print("\n--- Current Agent Memories ---")
    memories = await agent_memory.get_recent_memories(ctx, limit=50)
    
    if not memories:
        print("No memories found. Run the matching seed script first.")
    
    for i, m in enumerate(memories, 1):
        print(f"[{i}] Question: {m.question}")
        print(f"    SQL: {m.args.get('sql')}\n")

if __name__ == "__main__":
    asyncio.run(inspect_memory())
