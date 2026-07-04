"""Configuration diagnostics MCP tool."""

from services import query_service


def config_diagnostics() -> dict:
    """Return a safe summary of the active runtime configuration."""

    return query_service.config_diagnostics().to_dict()
