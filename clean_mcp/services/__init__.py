"""Service layer exports for the MCP server.

This package exposes the orchestrated service entry points used by MCP tools.
It should not contain transport-specific code.
"""

from services.query_service import QueryService, get_query_service


class _LazyQueryService:
    def __getattr__(self, name: str):
        return getattr(get_query_service(), name)


query_service = _LazyQueryService()
