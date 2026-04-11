"""Guardrail Loader — Phase 4.5 Stabilization.

Bridging the gap between defense synthesis (`MEMORY.md`) and the live session.
At the start of a campaign, the target LLM's scoped guardrails are loaded
from the `MemoryIndex` and structurally injected into the configuration.
"""

from __future__ import annotations

import hashlib
import logging

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_assets import append_guardrails_to_system_prompt
from redthread.memory.index import MemoryIndex
from redthread.models import CampaignConfig

logger = logging.getLogger(__name__)


class GuardrailLoader:
    """Dynamically loads and injects targeted guardrails into a campaign.
    
    Guardrails are scoped by `target_model` and the base `system_prompt`.
    """

    def __init__(self, settings: RedThreadSettings, memory_index: MemoryIndex | None = None) -> None:
        self.settings = settings
        self.memory = memory_index or MemoryIndex(settings)

    def _compute_prompt_hash(self, prompt: str) -> str:
        return hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()[:16]

    def get_scoped_clauses(self, target_model: str, base_system_prompt: str) -> list[str]:
        """Fetch all validated guardrail clauses from MEMORY.md for this scope."""
        prompt_hash = self._compute_prompt_hash(base_system_prompt)
        return self.memory.load_scoped_guardrails(target_model, prompt_hash)

    def inject_guardrails(self, config: CampaignConfig) -> CampaignConfig:
        """Return a new CampaignConfig with guardrails appended to target_system_prompt.
        
        If no guardrails match the current target model and base system prompt,
        returns the original config unmodified.
        """
        clauses = self.get_scoped_clauses(self.settings.target_model, config.target_system_prompt)
        prompt_hash = self._compute_prompt_hash(config.target_system_prompt)

        if not clauses:
            logger.info("🛡️ GuardrailLoader | No active guardrails found for target scope.")
            self._log_audit_event(self.settings.target_model, prompt_hash, [])
            return config

        logger.info(
            "🛡️ GuardrailLoader | Injected %d active guardrail(s) into target system prompt.",
            len(clauses)
        )
        self._log_audit_event(self.settings.target_model, prompt_hash, clauses)

        injected_prompt = append_guardrails_to_system_prompt(config.target_system_prompt, clauses)
        return config.model_copy(update={"target_system_prompt": injected_prompt})

    def _log_audit_event(self, target_model: str, prompt_hash: str, clauses: list[str]) -> None:
        """Write a structured audit event to logs/guardrail_audit.jsonl."""
        import json
        from datetime import datetime, timezone

        audit_path = self.settings.log_dir / "guardrail_audit.jsonl"
        self.settings.log_dir.mkdir(parents=True, exist_ok=True)

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_model": target_model,
            "prompt_hash": prompt_hash,
            "action": "INJECT" if clauses else "SKIP",
            "clauses_count": len(clauses),
            "clauses": clauses,
        }
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
