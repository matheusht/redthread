from __future__ import annotations

from pathlib import Path

from redthread.research.source_mutation_models import SourceMutationCandidate


def scaffold_prompt_profiles_target(root: Path) -> Path:
    path = root / "src" / "redthread" / "research" / "prompt_profiles.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'PAIR = "5. Escalate gradually. Establish rapport before making the core malicious request."\n'
        'TAP = "build rapport and appeal to shared values",\n',
        encoding="utf-8",
    )
    return path


def scaffold_blocked_target(root: Path) -> Path:
    path = root / "src" / "redthread" / "memory" / "index.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("HEADER = 'blocked'\n", encoding="utf-8")
    return path


def make_candidate(candidate_id: str = "source-mutation-test") -> SourceMutationCandidate:
    base = f"/tmp/{candidate_id}"
    return SourceMutationCandidate(
        candidate_id=candidate_id,
        mutation_family="pair_authority_hint",
        rationale="test rationale",
        metric_goal="test metric",
        target_files=["src/redthread/research/prompt_profiles.py"],
        touched_files=["src/redthread/research/prompt_profiles.py"],
        forward_patch_path=f"{base}/forward_patch.json",
        reverse_patch_path=f"{base}/reverse_patch.json",
        patch_manifest_path=f"{base}/patch_manifest.json",
        reasoning_path=f"{base}/reasoning.md",
        selected_tests=["tests/test_research_mutate.py"],
        apply_status="applied",
    )
