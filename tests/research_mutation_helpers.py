from __future__ import annotations

from pathlib import Path

from redthread.research.source_mutation_models import SourceMutationCandidate


def scaffold_defense_assets_target(root: Path) -> Path:
    source = Path(__file__).resolve().parents[1] / "src" / "redthread" / "core" / "defense_assets.py"
    path = root / "src" / "redthread" / "core" / "defense_assets.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def scaffold_prompt_profiles_target(root: Path) -> Path:
    path = root / "src" / "redthread" / "research" / "prompt_profiles.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'PAIR = "5. Escalate gradually. Establish rapport before making the core malicious request."\n'
        'TAP = "build rapport and appeal to shared values",\n',
        encoding="utf-8",
    )
    return path


def scaffold_source_mutation_targets(root: Path) -> None:
    scaffold_prompt_profiles_target(root)
    targets = {
        root / "src" / "redthread" / "core" / "pair.py":
            'PROMPT = "5. Escalate gradually. Establish rapport before making the core malicious request."\n',
        root / "src" / "redthread" / "core" / "tap.py":
            'STRATEGY = "build rapport and appeal to shared values",\n',
        root / "src" / "redthread" / "core" / "crescendo.py":
            'RETRY = "Generate a different approach for turn {turn_number}. Try a new angle."\n',
        root / "src" / "redthread" / "core" / "mcts.py":
            'RULE = "2. Apply the specified strategy naturally within your cover story."\n',
        root / "src" / "redthread" / "personas" / "generator.py":
            'LINE = "5. **allowed_strategies** — a list of 3-5 short, concrete conversational tactics"\n',
    }
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def scaffold_blocked_target(root: Path) -> Path:
    path = root / "src" / "redthread" / "memory" / "index.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("HEADER = 'blocked'\n", encoding="utf-8")
    return path


def make_candidate(
    candidate_id: str = "source-mutation-test",
    mutation_phase: str = "phase5",
) -> SourceMutationCandidate:
    base = f"/tmp/{candidate_id}"
    return SourceMutationCandidate(
        candidate_id=candidate_id,
        mutation_phase=mutation_phase,
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
