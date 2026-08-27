import logging
import re
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from client import db_instance

logger = logging.getLogger(__name__)

mcp = FastMCP("Database MCP Server", host="0.0.0.0", port=8000)


FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "merge",
    "replace",
    "execute",
    "call",
    "vacuum",
    "analyze",
    "refresh",
}


def validate_query(query: str) -> None:
    """
    Validate SQL query before execution.

    Rules:
    - Only SELECT and WITH queries are allowed.
    - Multiple statements are forbidden.
    - DDL/DML operations are forbidden.
    """

    cleaned = query.strip().lower()

    # Remove SQL comments
    cleaned = re.sub(r'--.*?$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Allow only SELECT or WITH
    if not (
        cleaned.startswith("select")
        or cleaned.startswith("with")
    ):
        raise ValueError(
            "Only SELECT and WITH queries are allowed."
        )

    # Block multiple statements
    stripped = cleaned.rstrip(";").strip()

    if ";" in stripped:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    # Check forbidden keywords
    words = set(re.findall(r"\b[a-z_]+\b", cleaned))

    blocked = words.intersection(FORBIDDEN_KEYWORDS)

    if blocked:
        raise ValueError(
            f"Forbidden SQL operation detected: {', '.join(sorted(blocked))}"
        )


@mcp.tool()
async def list_tables() -> List[str]:
    """
    List all tables in the database's public schema.

    Call this first if you don't already know which table holds the data you need —
    it's the entry point for exploring an unfamiliar database before writing queries.

    Returns:
        Table names, alphabetically sorted. Empty list if the schema has no tables.
    """
    session = db_instance.get_session()

    try:
        logger.info("Fetching list of tables")

        result = session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        )

        return [row[0] for row in result.fetchall()]

    except SQLAlchemyError:
        logger.exception("Database error while listing tables")
        raise

    finally:
        session.close()

@mcp.tool()
async def fetch_one(
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Execute a read-only SQL query and return only its first matching row.

    Use this when you expect at most one row (e.g. looking up a record by id) — it's
    cheaper than fetch_all and avoids pulling back rows you don't need.

    Notes:
    - Only SELECT and WITH queries are allowed; DML/DDL keywords (INSERT, UPDATE,
      DELETE, DROP, ALTER, TRUNCATE, CREATE, ...) and multi-statement queries are
      rejected with a ValueError before anything runs against the database.
    - Prefer parameterized queries (`:name` placeholders + `params`) over string-building
      values into the query text — safer, and avoids type/quoting mistakes.

    Args:
        query: A SELECT or WITH statement, e.g. "SELECT * FROM users WHERE id = :user_id".
        params: Bind parameters referenced in the query, e.g. {"user_id": 1}. Omit if the
            query has no placeholders.

    Returns:
        The first matching row as a dict of column name to value, or None if no row matched.
    """

    validate_query(query)

    session = db_instance.get_session()

    try:
        logger.info("Executing fetch_one query")

        result = session.execute(
            text(query),
            params or {},
        )

        row = result.mappings().first()

        return dict(row) if row else None

    except SQLAlchemyError:
        logger.exception("Database fetch_one error")
        raise

    finally:
        session.close()


@mcp.tool()
async def fetch_all(
    query: str,
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query and return every matching row.

    Use LIMIT in the query itself for anything that could return a large result set —
    this returns the full result with no automatic truncation.

    Notes:
    - Only SELECT and WITH queries are allowed; DML/DDL keywords (INSERT, UPDATE,
      DELETE, DROP, ALTER, TRUNCATE, CREATE, ...) and multi-statement queries are
      rejected with a ValueError before anything runs against the database.
    - Prefer parameterized queries (`:name` placeholders + `params`) over string-building
      values into the query text — safer, and avoids type/quoting mistakes.

    Args:
        query: A SELECT or WITH statement, e.g. "SELECT * FROM users WHERE status = :status".
        params: Bind parameters referenced in the query, e.g. {"status": "ACTIVE"}. Omit if
            the query has no placeholders.

    Returns:
        Every matching row as a dict of column name to value. Empty list if none matched.
    """

    validate_query(query)

    session = db_instance.get_session()

    try:
        logger.info("Executing fetch_all query")

        result = session.execute(
            text(query),
            params or {},
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    except SQLAlchemyError:
        logger.exception("Database fetch_all error")
        raise

    finally:
        session.close()

def main():
    # Initialize and run the server
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

