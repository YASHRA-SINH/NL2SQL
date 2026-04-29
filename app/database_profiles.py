import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import psycopg2
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MEMORY_DIR = os.path.join(PROJECT_ROOT, "memory_store")


@dataclass(frozen=True)
class DatabaseProfile:
    id: str
    name: str
    description: str
    domain: str
    dialect: str
    host: str
    port: str
    user: str
    password: str | None
    database: str
    schema: str = "public"
    accent: str = "teal"

    @property
    def memory_path(self) -> str:
        return os.path.join(MEMORY_DIR, f"{self.id}.json")


def _env(prefix: str, key: str, default: str | None = None) -> str | None:
    return os.getenv(f"{prefix}_{key}", os.getenv(f"PG_{key}", default))


def _sales_env(key: str, default: str | None = None) -> str | None:
    # Database name must not silently fall back to PG_DATABASE, or the sales
    # profile can accidentally point at the clinic database.
    if key == "DATABASE":
        return os.getenv("SALES_PG_DATABASE", default)
    if key == "SCHEMA":
        return os.getenv("SALES_PG_SCHEMA", default)
    return os.getenv(f"SALES_PG_{key}", os.getenv(f"PG_{key}", default))


DATABASE_PROFILES: dict[str, DatabaseProfile] = {
    "clinic": DatabaseProfile(
        id="clinic",
        name="Clinic PostgreSQL Database",
        description="Clinical operations data for patients, doctors, appointments, treatments, and invoices.",
        domain="clinic",
        dialect="postgres",
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE", "clinic"),
        schema=os.getenv("PG_SCHEMA", "public"),
        accent="teal",
    ),
    "sales": DatabaseProfile(
        id="sales",
        name="Sales PostgreSQL Database",
        description="Sales, customer, product, order, payment, and support analytics data.",
        domain="sales",
        dialect="postgres",
        host=_sales_env("HOST", "localhost") or "localhost",
        port=_sales_env("PORT", "5432") or "5432",
        user=_sales_env("USER", "postgres") or "postgres",
        password=_sales_env("PASSWORD"),
        database=_sales_env("DATABASE", "sales") or "sales",
        schema=_sales_env("SCHEMA", "public") or "public",
        accent="indigo",
    ),
}

DEFAULT_DATABASE_ID = os.getenv("DEFAULT_DATABASE_ID", "clinic")


def get_profile(database_id: str | None = None) -> DatabaseProfile:
    profile_id = database_id or DEFAULT_DATABASE_ID
    if profile_id not in DATABASE_PROFILES:
        raise KeyError(f"Unknown database profile: {profile_id}")
    return DATABASE_PROFILES[profile_id]


def list_profiles() -> list[DatabaseProfile]:
    return list(DATABASE_PROFILES.values())


def connect(profile: DatabaseProfile):
    return psycopg2.connect(
        host=profile.host,
        port=profile.port,
        user=profile.user,
        password=profile.password,
        dbname=profile.database,
    )


@lru_cache(maxsize=32)
def introspect_database(database_id: str) -> dict[str, Any]:
    profile = get_profile(database_id)
    with connect(profile) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    EXISTS (
                        SELECT 1
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.table_schema = kcu.table_schema
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                          AND tc.table_schema = c.table_schema
                          AND tc.table_name = c.table_name
                          AND kcu.column_name = c.column_name
                    ) AS is_primary_key
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema = c.table_schema
                 AND t.table_name = c.table_name
                WHERE c.table_schema = %s
                  AND t.table_type = 'BASE TABLE'
                ORDER BY c.table_name, c.ordinal_position
                """,
                (profile.schema,),
            )
            rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = %s
                ORDER BY tc.table_name, kcu.column_name
                """,
                (profile.schema,),
            )
            fk_rows = cur.fetchall()

            table_names = sorted({row[0] for row in rows})
            row_counts: dict[str, int | None] = {}
            for table_name in table_names:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{profile.schema}"."{table_name}"')
                    row_counts[table_name] = cur.fetchone()[0]
                except Exception:
                    row_counts[table_name] = None

    tables: dict[str, dict[str, Any]] = {}
    for table_name, column_name, data_type, is_nullable, column_default, is_pk in rows:
        table = tables.setdefault(
            table_name,
            {
                "name": table_name,
                "description": "",
                "row_count": row_counts.get(table_name),
                "columns": [],
                "foreign_keys": [],
            },
        )
        table["columns"].append(
            {
                "name": column_name,
                "type": data_type,
                "nullable": is_nullable == "YES",
                "default": column_default,
                "primary_key": bool(is_pk),
            }
        )

    for table_name, column_name, foreign_table, foreign_column in fk_rows:
        if table_name in tables:
            tables[table_name]["foreign_keys"].append(
                {
                    "column": column_name,
                    "references_table": foreign_table,
                    "references_column": foreign_column,
                }
            )

    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "domain": profile.domain,
        "dialect": profile.dialect,
        "database": profile.database,
        "schema": profile.schema,
        "accent": profile.accent,
        "tables": list(tables.values()),
        "suggestions": get_suggestions(profile.id, list(tables.values())),
    }


def get_suggestions(database_id: str, tables: list[dict[str, Any]] | None = None) -> list[str]:
    if database_id == "clinic":
        return [
            "How many patients do we have?",
            "Show monthly revenue trend",
            "Which doctor has the most appointments?",
            "Show top 5 patients by total amount billed",
            "What are the most common treatments?",
            "How many invoices are unpaid or overdue?",
        ]
    if database_id == "sales":
        return [
            "What is total revenue by month?",
            "Show top 10 customers by lifetime revenue",
            "Which product categories sell the most?",
            "What is the average order value by sales channel?",
            "Show unpaid or failed payments by month",
            "Which sales reps closed the most revenue?",
        ]

    table_names = [table["name"] for table in tables or []]
    if not table_names:
        return ["What tables are available in this database?"]
    return [
        f"How many rows are in {table_names[0]}?",
        "Show the largest tables by row count",
        "Summarize this database schema",
    ]


def build_schema_prompt(database_id: str) -> str:
    metadata = introspect_database(database_id)
    lines = [
        "IMPORTANT DATABASE CONTEXT:",
        f"- Active database profile: {metadata['name']} ({metadata['database']})",
        f"- SQL dialect: PostgreSQL",
        f"- Schema: {metadata['schema']}",
        "",
        "AVAILABLE TABLES AND COLUMNS:",
    ]

    for table in metadata["tables"]:
        column_parts = []
        for column in table["columns"]:
            suffix = " primary key" if column["primary_key"] else ""
            column_parts.append(f"{column['name']} {column['type']}{suffix}")
        lines.append(f"- {table['name']} ({', '.join(column_parts)})")
        for fk in table["foreign_keys"]:
            lines.append(
                f"  FK: {table['name']}.{fk['column']} -> "
                f"{fk['references_table']}.{fk['references_column']}"
            )

    domain_rules = _domain_sql_rules(database_id)
    if domain_rules:
        lines.extend(["", "CANONICAL BUSINESS DEFINITIONS:", *domain_rules])

    lines.extend(
        [
            "",
            "SQL GENERATION RULES:",
            "1. Generate read-only SELECT queries only.",
            "2. When using GROUP BY, every non-aggregated SELECT column must appear in GROUP BY.",
            "3. Prefer explicit JOINs using the foreign keys above.",
            "4. Use COALESCE around nullable aggregates, especially SUM and AVG.",
            "5. Use COUNT(*) for row counts and COUNT(column) only when intentionally counting non-null values.",
            "6. Add a sensible LIMIT for broad row-listing requests.",
            "7. For ambiguous business words like best, top, most, or sells most, ask for clarification unless the metric is explicit.",
            "8. Keep SQL stable for repeat questions: use the canonical definitions and join paths above.",
            "",
            "ERROR CORRECTION RULES:",
            "1. Fix only the failing SQL; do not change the user's intent.",
            "2. If an aggregate returns NULL unexpectedly, wrap it in COALESCE and check the join path.",
            "3. If a join creates duplicate totals, aggregate at the correct grain in a subquery before joining.",
            "",
            "SUMMARY RULES:",
            "1. Summaries must state concrete observations from the result rows.",
            "2. Do not use filler phrases like additional analysis can be performed.",
            "3. Mention warnings when results are empty or NULL-heavy.",
            "",
            "CRITICAL VISUALIZATION RULES:",
            "1. Time series must use a line chart.",
            "2. Rankings and category comparisons must use a bar chart.",
            "3. Shares or composition may use pie only for 8 or fewer categories.",
            "4. Correlation charts are allowed only when the user explicitly asks for correlation or relationship.",
            "5. Do not use heatmaps for revenue by month, category rankings, or simple aggregations.",
            "6. When visualizing data, use the pandas dataframe variable `df` from the previous SQL query.",
            "7. Do not read CSV files or invent external datasets.",
        ]
    )
    return "\n".join(lines)


def _domain_sql_rules(database_id: str) -> list[str]:
    if database_id == "sales":
        return [
            "- Revenue = SUM(order_items.quantity * order_items.unit_price * (1 - order_items.discount_pct)).",
            "- Sales revenue queries must join orders -> order_items and filter orders.status IN ('completed', 'processing') unless the user asks otherwise.",
            "- Product category analysis must join products -> order_items -> orders.",
            "- Sales rep revenue must join sales_reps -> orders -> order_items.",
            "- Customer revenue can use customers.lifetime_value for lifetime ranking, or orders -> order_items for period-specific revenue.",
            "- Payment status analysis should use payments directly and not infer payment success from orders.status.",
            "- If the user says sells most without a metric, ask whether they mean revenue, units sold, or order count.",
        ]
    if database_id == "clinic":
        return [
            "- Clinic revenue = SUM(invoices.total_amount), and collected amount = SUM(invoices.paid_amount).",
            "- Outstanding amount = SUM(invoices.total_amount - invoices.paid_amount).",
            "- Doctor appointment counts must join doctors -> appointments.",
            "- Treatment analysis must join appointments -> treatments when doctor or patient context is needed.",
            "- Patient billing analysis must join patients -> invoices.",
        ]
    return []
