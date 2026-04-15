"""Runtime mode labels used in transcripts, CLI output, and reports."""

from __future__ import annotations

from redthread.config.settings import RedThreadSettings

SEALED_DRY_RUN = "sealed_dry_run"
LIVE_PROVIDER = "live_provider"


def campaign_runtime_mode(settings: RedThreadSettings) -> str:
    """Return the effective campaign execution mode label."""
    return SEALED_DRY_RUN if settings.dry_run else LIVE_PROVIDER


def telemetry_runtime_mode(settings: RedThreadSettings) -> str:
    """Return the telemetry execution mode label for one campaign."""
    if settings.dry_run:
        return "skipped_in_dry_run"
    return "live_provider"
