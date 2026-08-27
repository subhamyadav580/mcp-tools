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
    List all tables in the public schema.
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
    Execute a read-only SQL query and return the first row.

    Notes:
    - Only SELECT and WITH queries are allowed.
    - INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE are forbidden.
    - Parameterized queries are recommended.

    Example:
        SELECT * FROM users WHERE id = :user_id

    Params:
        {"user_id": 1}
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
    Execute a read-only SQL query and return all rows.

    Notes:
    - Only SELECT and WITH queries are allowed.
    - INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE are forbidden.
    - Parameterized queries are recommended.

    Example:
        SELECT * FROM users WHERE status = :status

    Params:
        {"status": "ACTIVE"}
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

