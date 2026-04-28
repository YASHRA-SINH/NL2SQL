"""
vanna_setup.py
Sets up the full Vanna 2.0 Agent with:
  - Groq LLM (llama-3.3-70b-versatile) via OpenAI-compatible service
  - SqliteRunner pointing at clinic.db
  - ToolRegistry with RunSqlTool, VisualizeDataTool, memory tools
  - DemoAgentMemory for learning
  - A simple default UserResolver
"""

import os
from dotenv import load_dotenv

# ── Vanna 2.0 imports ───────────────────────────────────────────────────────
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext

from vanna.tools import RunSqlTool, VisualizeDataTool


from vanna.integrations.postgres import PostgresRunner
from vanna.integrations.openai import OpenAILlmService          # Groq is OpenAI-compatible
from persistent_memory import PersistentAgentMemory

# ── Load environment variables ──────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Please add it to your .env file: GROQ_API_KEY=gsk_..."
    )

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE", "clinic")

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 1. LLM Service (Groq via OpenAI-compatible API) ────────────────────────
llm_service = OpenAILlmService(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# ── 2. SQL Runner ──────────────────────────────────────────────────────────
sql_runner = PostgresRunner(
    host=PG_HOST,
    database=PG_DATABASE,
    user=PG_USER,
    password=PG_PASSWORD,
    port=PG_PORT
)

# ── 3. Agent Memory ────────────────────────────────────────────────────────
agent_memory = PersistentAgentMemory(max_items=1000)


# ── 4. Tool Registry ───────────────────────────────────────────────────────
tool_registry = ToolRegistry()

# Core tools – accessible to all users
tool_registry.register_local_tool(
    RunSqlTool(sql_runner=sql_runner),
    access_groups=["admin", "user"],
)

tool_registry.register_local_tool(
    VisualizeDataTool(),
    access_groups=["admin", "user"],
)




# ── 5. User Resolver (simple default user) ──────────────────────────────────
class DefaultUserResolver(UserResolver):
    """Always resolves to a default 'clinic_user' with admin + user groups."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="default_user",
            username="clinic_user",
            email="user@clinic.local",
            group_memberships=["admin", "user"],
        )


user_resolver = DefaultUserResolver()


# ── 6. Agent Configuration ─────────────────────────────────────────────────
agent_config = AgentConfig(
    max_tool_iterations=10,
    stream_responses=False,          # simpler for FastAPI JSON endpoints
    auto_save_conversations=True,
    temperature=0.0,
)


# ── 7. Assemble the Agent ──────────────────────────────────────────────────
from vanna.core.system_prompt.default import DefaultSystemPromptBuilder

class ClinicSystemPromptBuilder(DefaultSystemPromptBuilder):
    async def build_system_prompt(self, user, tools):
        base_prompt = await super().build_system_prompt(user, tools)
        schema = """
        IMPORTANT DATABASE SCHEMA:
        You must only query the following tables and columns:
        - patients (id, first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
        - doctors (id, name, specialization, department, phone)
        - appointments (id, patient_id, doctor_id, appointment_date, status, notes)
        - treatments (id, appointment_id, treatment_name, cost, duration_minutes)
        - invoices (id, patient_id, invoice_date, total_amount, paid_amount, status)

        CRITICAL POSTGRESQL RULES:
        1. When using GROUP BY, every column in your SELECT clause must either be an aggregate function (like COUNT, SUM) or appear in the GROUP BY clause.
        2. DO NOT GROUP BY an ID while selecting a name without also grouping by the name.

        CRITICAL VISUALIZATION RULES:
        1. When visualizing data, you MUST use the pandas dataframe variable `df` that is already loaded in memory from the previous SQL query.
        2. DO NOT write code that attempts to read from a CSV file (e.g. `pd.read_csv('invoices.csv')`). The data is already in `df`.
        """
        return base_prompt + "\n" + schema

agent = Agent(
    llm_service=llm_service,
    tool_registry=tool_registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    config=agent_config,
    system_prompt_builder=ClinicSystemPromptBuilder(),
)


# ── Quick self-test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[OK] Vanna 2.0 Agent initialised successfully!")
    print(f"     LLM model : llama-3.3-70b-versatile (Groq)")
    print(f"     Database  : PostgreSQL ({PG_DATABASE})")
    print(f"     Memory    : PersistentAgentMemory (max_items=1000)")

    import asyncio

    async def _check():
        tools = await tool_registry.list_tools()
        print(f"     Tools     : {', '.join(tools)}")

    asyncio.run(_check())
