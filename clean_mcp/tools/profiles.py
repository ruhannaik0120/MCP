"""Agent-facing tools for safe runtime connector switching."""

from services.profile_service import list_connection_profiles, switch_connection_profile


def list_profiles() -> dict:
    """List profile names and readiness flags without returning secrets."""

    return list_connection_profiles()


def switch_profile(name: str, confirm: bool = False) -> dict:
    """Switch profiles only after approval and always verify connectivity."""

    return switch_connection_profile(name, confirm=confirm, test_connection=True)
