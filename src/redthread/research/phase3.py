"""Phase 3 scheduling and git-backed evaluation workflow."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from redthread.config.settings import RedThreadSettings
from redthread.research.git_ops import GitWorkspaceManager
from redthread.research.history import ObjectiveHistoryAnalyzer
from redthread.research.models import PhaseThreeProposal, PhaseThreeSession, ResearchLaneConfig
from redthread.research.objectives import ensure_config
from redthread.research.runtime import apply_runtime_overrides
from redthread.research.supervisor import PhaseTwoResearchHarness


class PhaseThreeHarness:
    """Add dynamic scheduling and safe git accept/reject control."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.settings = apply_runtime_overrides(settings, root)
        self.root = root
        self.autoresearch_dir = root / "autoresearch"
        self.config_path = self.autoresearch_dir / "config.json"
        self.session_path = self.autoresearch_dir / "session.json"
        self.proposals_dir = self.autoresearch_dir / "proposals"
        self.config = ensure_config(self.config_path)
        self.git = GitWorkspaceManager(root)

    def start_session(self, tag: str) -> PhaseThreeSession:
        """Create a dedicated autoresearch branch from a clean starting point."""
        self.git.ensure_clean()
        base_commit = self.git.head_commit()
        branch = self.git.create_branch(tag)
        session = PhaseThreeSession(tag=tag, branch=branch, base_commit=base_commit)
        self._write_json(self.session_path, session.model_dump(mode="json"))
        return session

    async def run_cycle(self, baseline_first: bool) -> PhaseThreeProposal:
        """Run one Phase 3 cycle with dynamic objective selection."""
        session = self._load_session()
        ranked = ObjectiveHistoryAnalyzer(self.autoresearch_dir / "results.tsv").rank()
        ranked_slugs = [item.slug for item in ranked]
        self.config.lane_configs = self._dynamic_lanes(ranked_slugs)
        self._write_json(self.config_path, self.config.model_dump(mode="json"))

        supervisor = PhaseTwoResearchHarness(self.settings, self.root)
        cycle = await supervisor.run_cycle(baseline_first=baseline_first)
        proposal = PhaseThreeProposal(
            proposal_id=f"proposal-{uuid4().hex[:8]}",
            session_tag=session.tag,
            accepted=cycle.accepted,
            recommended_action="accept" if cycle.accepted else "reject",
            rationale=cycle.rationale,
            cycle=cycle,
            started_at=cycle.started_at,
            completed_at=cycle.completed_at,
        )
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(
            self.proposals_dir / f"{proposal.proposal_id}.json",
            proposal.model_dump(mode="json"),
        )
        return proposal

    def accept_latest(self, message: str | None = None) -> str:
        """Commit current changes for the latest accepted proposal."""
        proposal = self._latest_proposal()
        if proposal.recommended_action != "accept":
            raise RuntimeError("Latest Phase 3 proposal is not accepted.")
        commit_message = message or f"autoresearch: accept {proposal.proposal_id} [{proposal.cycle.winning_lane}]"
        commit = self.git.commit_all(commit_message)
        session = self._load_session()
        session.base_commit = commit
        self._write_json(self.session_path, session.model_dump(mode="json"))
        return commit

    def reject_latest(self) -> str:
        """Reset the worktree back to the session base commit."""
        proposal = self._latest_proposal()
        session = self._load_session()
        self.git.hard_reset(session.base_commit)
        return proposal.proposal_id

    def _dynamic_lanes(self, ranked_slugs: list[str]) -> list[ResearchLaneConfig]:
        """Build Phase 3 lane assignments from history-aware slug ranking."""
        default_experiment = [objective.slug for objective in self.config.experiment_objectives]
        offense = self._pick(ranked_slugs, default_experiment, count=2)
        remaining = [slug for slug in default_experiment if slug not in offense]
        regression = self._pick(ranked_slugs, remaining or default_experiment, count=2)
        control = [objective.slug for objective in self.config.benchmark_objectives]
        return [
            ResearchLaneConfig(lane="offense", source="experiment", objective_slugs=offense),
            ResearchLaneConfig(lane="regression", source="experiment", objective_slugs=regression),
            ResearchLaneConfig(lane="control", source="benchmark", objective_slugs=control),
        ]

    def _pick(self, ranked_slugs: list[str], pool: list[str], count: int) -> list[str]:
        ordered = [slug for slug in ranked_slugs if slug in pool]
        for slug in pool:
            if slug not in ordered:
                ordered.append(slug)
        return ordered[:count]

    def _latest_proposal(self) -> PhaseThreeProposal:
        proposals = sorted(self.proposals_dir.glob("proposal-*.json"))
        if not proposals:
            raise RuntimeError("No Phase 3 proposals found.")
        return PhaseThreeProposal.model_validate(json.loads(proposals[-1].read_text(encoding="utf-8")))

    def _load_session(self) -> PhaseThreeSession:
        if not self.session_path.exists():
            raise RuntimeError("No active Phase 3 session. Run the start command first.")
        return PhaseThreeSession.model_validate(json.loads(self.session_path.read_text(encoding="utf-8")))

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
