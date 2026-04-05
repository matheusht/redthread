"""Research workspace paths for tracked templates and untracked runtime state."""

from __future__ import annotations

import shutil
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.research.objectives import ensure_config
from redthread.research.prompt_profiles import load_prompt_profiles


class ResearchWorkspace:
    """Owns the autoresearch template/runtime directory layout."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.base_dir = root / "autoresearch"
        self.templates_dir = self.base_dir / "templates"
        self.runtime_dir = self.base_dir / "runtime"
        self.template_config_path = self.templates_dir / "config.json"
        self.template_prompt_profiles_path = self.templates_dir / "prompt_profiles.json"
        self.runtime_config_path = self.runtime_dir / "config.json"
        self.prompt_profiles_path = self.runtime_dir / "prompt_profiles.json"
        self.results_path = self.runtime_dir / "results.tsv"
        self.session_path = self.runtime_dir / "session.json"
        self.proposals_dir = self.runtime_dir / "proposals"
        self.mutation_state_path = self.runtime_dir / "mutation_state.json"
        self.mutations_dir = self.runtime_dir / "mutations"
        self.checkpoints_dir = self.runtime_dir / "checkpoints"
        self.baseline_registry_path = self.runtime_dir / "baseline_registry.json"
        self.promotions_dir = self.runtime_dir / "promotions"
        self.research_memory_dir = self.runtime_dir / "research_memory"
        self.daemon_state_path = self.runtime_dir / "daemon_state.json"
        self.heartbeat_path = self.runtime_dir / "heartbeat.json"
        self.session_lock_path = self.runtime_dir / "session_lock.json"
        self.failure_log_path = self.runtime_dir / "failure_log.jsonl"

    def ensure_layout(self) -> None:
        """Create tracked templates and migrate legacy runtime files if present."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.mutations_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.promotions_dir.mkdir(parents=True, exist_ok=True)
        self.research_memory_dir.mkdir(parents=True, exist_ok=True)

        if not self.template_config_path.exists():
            legacy_config = self.base_dir / "config.json"
            if legacy_config.exists():
                shutil.copy2(legacy_config, self.template_config_path)
            else:
                ensure_config(self.template_config_path)
        if not self.template_prompt_profiles_path.exists():
            legacy_profiles = self.base_dir / "prompt_profiles.json"
            if legacy_profiles.exists():
                shutil.copy2(legacy_profiles, self.template_prompt_profiles_path)
            else:
                load_prompt_profiles(self.template_prompt_profiles_path)

        self._migrate_legacy_file(self.base_dir / "results.tsv", self.results_path)
        self._migrate_legacy_file(self.base_dir / "session.json", self.session_path)
        self._migrate_legacy_file(self.base_dir / "prompt_profiles.json", self.prompt_profiles_path)
        self._migrate_legacy_file(self.base_dir / "mutation_state.json", self.mutation_state_path)
        self._migrate_legacy_dir(self.base_dir / "proposals", self.proposals_dir)
        self._migrate_legacy_dir(self.base_dir / "mutations", self.mutations_dir)

        if not self.runtime_config_path.exists():
            shutil.copy2(self.template_config_path, self.runtime_config_path)
        if not self.prompt_profiles_path.exists():
            shutil.copy2(self.template_prompt_profiles_path, self.prompt_profiles_path)

    def research_settings(self, settings: RedThreadSettings) -> RedThreadSettings:
        """Return a settings copy scoped to research-only runtime state."""
        self.ensure_layout()
        return settings.model_copy(
            update={
                "memory_dir": self.research_memory_dir,
                "research_runtime_dir": self.runtime_dir,
            }
        )

    def clean_runtime(self) -> None:
        """Delete runtime artifacts while keeping tracked templates intact."""
        if self.runtime_dir.exists():
            shutil.rmtree(self.runtime_dir)
        self.ensure_layout()

    def proposal_path(self, proposal_id: str) -> Path:
        """Return the artifact path for one proposal."""
        return self.proposals_dir / f"{proposal_id}.json"

    def proposal_memory_snapshot_path(self, proposal_id: str) -> Path:
        """Return the proposal-scoped research memory snapshot path."""
        return self.proposals_dir / f"memory-snapshot-{proposal_id}.json"

    def mutation_candidate_dir(self, candidate_id: str) -> Path:
        """Return the artifact directory for one mutation candidate."""
        return self.mutations_dir / candidate_id

    def mutation_candidate_path(self, candidate_id: str) -> Path:
        """Return the candidate metadata path for one source mutation."""
        return self.mutation_candidate_dir(candidate_id) / "candidate.json"

    def mutation_manifest_path(self, candidate_id: str) -> Path:
        """Return the manifest path for one source mutation."""
        return self.mutation_candidate_dir(candidate_id) / "patch_manifest.json"

    def mutation_reasoning_path(self, candidate_id: str) -> Path:
        """Return the reasoning path for one source mutation."""
        return self.mutation_candidate_dir(candidate_id) / "reasoning.md"

    def mutation_forward_patch_path(self, candidate_id: str) -> Path:
        """Return the forward patch artifact path for one source mutation."""
        return self.mutation_candidate_dir(candidate_id) / "forward_patch.json"

    def mutation_reverse_patch_path(self, candidate_id: str) -> Path:
        """Return the reverse patch artifact path for one source mutation."""
        return self.mutation_candidate_dir(candidate_id) / "reverse_patch.json"

    def promotion_dir_for(self, promotion_id: str) -> Path:
        """Return the artifact directory for one promotion run."""
        return self.promotions_dir / promotion_id

    def promotion_manifest_path(self, promotion_id: str) -> Path:
        """Return the manifest path for one promotion run."""
        return self.promotion_dir_for(promotion_id) / "promotion_manifest.json"

    def promotion_validation_path(self, promotion_id: str) -> Path:
        """Return the validation path for one promotion run."""
        return self.promotion_dir_for(promotion_id) / "promotion_validation.json"

    def promotion_result_path(self, promotion_id: str) -> Path:
        """Return the final result path for one promotion run."""
        return self.promotion_dir_for(promotion_id) / "promotion_result.json"

    def promotion_checkpoint_path(self, promotion_id: str) -> Path:
        """Return the resumable checkpoint path for one promotion run."""
        return self.promotion_dir_for(promotion_id) / "promotion_checkpoint.json"

    def _migrate_legacy_file(self, source: Path, target: Path) -> None:
        if source.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))

    def _migrate_legacy_dir(self, source: Path, target: Path) -> None:
        if source.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
