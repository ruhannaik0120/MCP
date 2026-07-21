"""Service layer exports for the MCP server.

This package exposes the orchestrated service entry points used by MCP tools.
It should not contain transport-specific code.
"""

# region Imports and module setup
from services.query_service import QueryService, get_query_service
# endregion Imports and module setup


# region Class: LazyQueryService
class _LazyQueryService:
    """Resolve the cached service only when a tool is actually invoked.

    Delayed construction lets startup configuration finish first and lets a
    profile switch discard the old connector before the next request.
    """

    # region Function: Getattr
    def __getattr__(self, name: str):
        """Forward attribute access to the current cached QueryService."""

        return getattr(get_query_service(), name)
    # endregion Function: Getattr
# endregion Class: LazyQueryService


query_service = _LazyQueryService()
