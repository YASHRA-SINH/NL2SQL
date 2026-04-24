import asyncio
from vanna_setup import agent_memory
from vanna.core.tool import ToolContext
from vanna.core.user import User

async def inspect_memory():
    # 1. Load from disk
    print("Loading persistent memory...")
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
        print("No memories found. Run `python seed_memory.py` first.")
    
    for i, m in enumerate(memories, 1):
        print(f"[{i}] Question: {m.question}")
        print(f"    SQL: {m.args.get('sql')}\n")

if __name__ == "__main__":
    asyncio.run(inspect_memory())
