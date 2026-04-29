import os
from dataclasses import dataclass

from dotenv import load_dotenv
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.system_prompt.default import DefaultSystemPromptBuilder
from vanna.core.user import RequestContext, User, UserResolver
from vanna.integrations.openai import OpenAILlmService
from vanna.tools import RunSqlTool, VisualizeDataTool

from .database_profiles import DatabaseProfile, build_schema_prompt, get_profile, list_profiles
from .persistent_memory import PersistentAgentMemory
from .read_only_postgres_runner import ReadOnlyPostgresRunner

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Please add it to your .env file: GROQ_API_KEY=gsk_..."
    )


llm_service = OpenAILlmService(
    model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    api_key=GROQ_API_KEY,
    base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
)


class DefaultUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        database_id = request_context.metadata.get("database_id", "default")
        return User(
            id="default_user",
            username=f"{database_id}_user",
            email=f"user@{database_id}.local",
            group_memberships=["admin", "user"],
        )


class ProfileSystemPromptBuilder(DefaultSystemPromptBuilder):
    def __init__(self, database_id: str):
        super().__init__()
        self.database_id = database_id

    async def build_system_prompt(self, user, tools):
        base_prompt = await super().build_system_prompt(user, tools)
        return base_prompt + "\n\n" + build_schema_prompt(self.database_id)


@dataclass
class AgentBundle:
    profile: DatabaseProfile
    agent: Agent
    memory: PersistentAgentMemory


class AgentManager:
    def __init__(self):
        self._bundles: dict[str, AgentBundle] = {}

    def get_bundle(self, database_id: str | None = None) -> AgentBundle:
        profile = get_profile(database_id)
        if profile.id not in self._bundles:
            self._bundles[profile.id] = self._create_bundle(profile)
        return self._bundles[profile.id]

    def _create_bundle(self, profile: DatabaseProfile) -> AgentBundle:
        sql_runner = ReadOnlyPostgresRunner(
            host=profile.host,
            database=profile.database,
            user=profile.user,
            password=profile.password,
            port=profile.port,
            statement_timeout_ms=int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "20000")),
        )
        memory = PersistentAgentMemory(store_path=profile.memory_path, max_items=1000)
        tool_registry = ToolRegistry()
        tool_registry.register_local_tool(RunSqlTool(sql_runner=sql_runner), access_groups=["admin", "user"])
        tool_registry.register_local_tool(VisualizeDataTool(), access_groups=["admin", "user"])

        agent = Agent(
            llm_service=llm_service,
            tool_registry=tool_registry,
            user_resolver=DefaultUserResolver(),
            agent_memory=memory,
            config=AgentConfig(
                max_tool_iterations=10,
                stream_responses=False,
                auto_save_conversations=True,
                temperature=0.0,
            ),
            system_prompt_builder=ProfileSystemPromptBuilder(profile.id),
        )
        return AgentBundle(profile=profile, agent=agent, memory=memory)

    async def load_all_memory(self) -> dict[str, int]:
        loaded = {}
        for profile in list_profiles():
            bundle = self.get_bundle(profile.id)
            loaded[profile.id] = await bundle.memory.load_from_disk()
        return loaded

    def memory_counts(self) -> dict[str, int]:
        return {
            profile.id: self.get_bundle(profile.id).memory.count_on_disk()
            for profile in list_profiles()
        }


agent_manager = AgentManager()
