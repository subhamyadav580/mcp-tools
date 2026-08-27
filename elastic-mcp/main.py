from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from es_client import ElasticsearchClient



mcp = FastMCP("Elastic Search MCP Server", host="0.0.0.0", port=8001)


es = ElasticsearchClient().get_client()

res = es.info()

@mcp.tool()
async def list_es_indices():
    """
    List every index in this Elasticsearch cluster.

    Call this first when you don't already know the index name to search — e.g. to find
    a service's log index before using get_index_mapping and search_on_index on it.

    Returns:
        Index names as a list of strings. Includes system/internal indices (names
        starting with ".") alongside application indices.
    """
    indices = es.cat.indices(format="json")
    return [item['index'] for item in indices]

@mcp.tool()
async def get_index_mapping(index_name: str):
    """
    Fetch the field mapping of an Elasticsearch index.

    Always call this before search_on_index — guessing field names/types produces
    queries that silently match nothing (Elasticsearch doesn't error on unknown fields).

    Args:
        index_name: Name of the index to inspect (from list_es_indices).

    Returns:
        Dict of field name to its Elasticsearch type (e.g. "keyword", "text", "long",
        "date"). A value of "object/nested" means the field has no explicit type set
        (a nested/object field) — inspect it further with a query if you need its shape.
    """
    mapping = es.indices.get_mapping(index=index_name)
    properties = mapping[index_name]["mappings"].get("properties", {})
    return {field: meta.get("type", "object/nested") for field, meta in properties.items()}


@mcp.tool()
async def search_on_index(index_name: str, query: dict = None):
    """
    Execute an Elasticsearch query on a specific index and return matching documents.

    Call get_index_mapping(index_name) first if you haven't already, so the query
    references real field names/types instead of guessing.

    Args:
        index_name: Name of the index to search (from list_es_indices).
        query: A full Elasticsearch query DSL body, e.g.
            {"query": {"match": {"level": "ERROR"}}, "sort": [{"@timestamp": "desc"}], "size": 20}.
            Include "size" yourself to limit results — Elasticsearch's own default (10) applies
            if omitted, with no additional truncation on top of that.

    Returns:
        The raw Elasticsearch search response: `hits.total` (match count), `hits.hits`
        (each with `_score` and the matched document under `_source`), and any
        aggregations if the query included them.
    """
    if not query:
        raise ValueError("query is required. Call get_index_mapping() first to see available fields, then retry with a valid Elasticsearch query DSL dict.")
    data = es.search(index=index_name, body=query)
    return data

def main():
    # Initialize and run the server
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

