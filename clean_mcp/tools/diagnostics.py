"""Configuration diagnostics MCP tool."""

from services import query_service
from services.runtime_state import runtime_lock


# region Function: Config diagnostics
def config_diagnostics() -> dict:
    """Return a safe summary of the active runtime configuration."""

    with runtime_lock:
        return query_service.config_diagnostics().to_dict()
# endregion Function: Config diagnostics
