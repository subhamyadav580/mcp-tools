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
    List all available Elasticsearch indexes.
    """
    indices = es.cat.indices(format="json")
    return [item['index'] for item in indices]

@mcp.tool()
async def get_index_mapping(index_name: str):
    """
    Fetch the field mapping of an Elasticsearch index.
    Always call this before search_on_index to understand the available fields and their types,
    so you can build an accurate query DSL.

    Args:
        index_name: The name of the index for which to fetch mapping.

    Returns a dict of field names and their types (e.g. keyword, text, integer, nested).
    """
    mapping = es.indices.get_mapping(index=index_name)
    properties = mapping[index_name]["mappings"].get("properties", {})
    return {field: meta.get("type", "object/nested") for field, meta in properties.items()}


@mcp.tool()
async def search_on_index(index_name: str, query: dict = None):
    """
    Execute an Elasticsearch query on a specific index and return matching documents.

    Args:
        index_name: The name of the index to search.
        query: A valid Elasticsearch query DSL dict. 

    Returns the raw Elasticsearch response including hits, scores, and _source documents.
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

