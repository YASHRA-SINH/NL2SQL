"""Profile-aware Vanna agent exports for internal app modules."""

from .agent_manager import agent_manager
from .database_profiles import DEFAULT_DATABASE_ID

_default_bundle = agent_manager.get_bundle(DEFAULT_DATABASE_ID)

agent = _default_bundle.agent
agent_memory = _default_bundle.memory


if __name__ == "__main__":
    print("[OK] Vanna profile-aware agent initialized successfully!")
    print(f"     Default profile : {_default_bundle.profile.id}")
    print(f"     Database        : PostgreSQL ({_default_bundle.profile.database})")
    print(f"     Memory          : {_default_bundle.profile.memory_path}")
