import re
from typing import Optional

import pandas as pd
from vanna.capabilities.sql_runner import RunSqlToolArgs, SqlRunner
from vanna.core.tool import ToolContext


BLOCKED_SQL = re.compile(
    r"\b(ALTER|CREATE|DELETE|DROP|GRANT|INSERT|REINDEX|REVOKE|TRUNCATE|UPDATE|VACUUM)\b",
    re.IGNORECASE,
)


class ReadOnlyPostgresRunner(SqlRunner):
    """PostgreSQL SQL runner with guardrails for NL2SQL analytics use."""

    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: Optional[str],
        port: str | int = 5432,
        statement_timeout_ms: int = 20_000,
    ):
        try:
            import psycopg2
            import psycopg2.extras

            self.psycopg2 = psycopg2
        except Exception as exc:
            raise ImportError("psycopg2 package is required.") from exc

        self.connection_params = {
            "host": host,
            "port": int(port),
            "database": database,
            "user": user,
            "password": password,
        }
        self.statement_timeout_ms = statement_timeout_ms

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        sql = args.sql.strip()
        first_word = sql.split(None, 1)[0].upper() if sql else ""
        if first_word not in {"SELECT", "WITH"} or BLOCKED_SQL.search(sql):
            raise ValueError("Only read-only SELECT queries are allowed for database profiles.")

        conn = self.psycopg2.connect(**self.connection_params)
        cursor = conn.cursor(cursor_factory=self.psycopg2.extras.RealDictCursor)
        try:
            conn.autocommit = False
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SET LOCAL statement_timeout = %s", (self.statement_timeout_ms,))
            cursor.execute(sql)
            rows = cursor.fetchall()
            conn.rollback()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([dict(row) for row in rows])
        finally:
            cursor.close()
            conn.close()

