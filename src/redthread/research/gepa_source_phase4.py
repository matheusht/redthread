"""Phase 4 GEPA source-lane spike orchestration."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

from redthread.config.settings import RedThreadSettings
from redthread.research.gepa_adapter import _require_gepa
from redthread.research.gepa_source_adapter import (
    SourceGEPAAdapter,
    SourceTemplateSelectionRunner,
    build_source_optimize_kwargs,
)
from redthread.research.gepa_source_candidate import (
    seed_source_candidate,
    source_candidate_family,
    template_by_family,
)
from redthread.research.objectives import ensure_config
from redthread.research.source_mutation_worker import SourceMutationWorker
from redthread.research.workspace import ResearchWorkspace


class OptimizeFn(Protocol):
    """Callable matching ``gepa.optimize`` for test injection."""

    def __call__(self, **kwargs: Any) -> Any: ...


def run_source_mutation_spike(
    settings: RedThreadSettings,
    root: Path,
    *,
    reflection_lm: str,
    max_metric_calls: int,
    train_slugs: Sequence[str] = (),
    val_slugs: Sequence[str] = (),
    seed: int = 0,
    optimize_fn: OptimizeFn | None = None,
) -> dict[str, Any]:
    """Run hidden GEPA selection, then apply one bounded Phase 5 source patch."""
    _ = settings
    workspace = ResearchWorkspace(root)
    workspace.ensure_layout()
    config = ensure_config(workspace.runtime_config_path, workspace.template_config_path)
    trainset = _select(config.experiment_objectives, train_slugs)
    valset = _select(config.benchmark_objectives, val_slugs)
    seed_candidate = seed_source_candidate()
    runner = SourceTemplateSelectionRunner(root, workspace)
    adapter = SourceGEPAAdapter(runner)
    kwargs = build_source_optimize_kwargs(
        seed_candidate,
        trainset,
        adapter=adapter,
        reflection_lm=reflection_lm,
        max_metric_calls=max_metric_calls,
        valset=valset,
        seed=seed,
    )
    result = (optimize_fn or _require_gepa().optimize)(**kwargs)
    best_candidate = getattr(result, "best_candidate", seed_candidate)
    family = source_candidate_family(best_candidate)
    template = template_by_family(family)
    worker = SourceMutationWorker(
        root,
        template_selector=lambda _ranked, _templates: template,
        mutation_phase="phase4_gepa_source",
    )
    applied = worker.generate_and_apply([])
    payload = {
        "phase": "gepa_phase4_source_lane",
        "best_candidate": best_candidate,
        "mutation_candidate_id": applied.candidate_id,
        "mutation_family": applied.mutation_family,
        "touched_files": applied.touched_files,
        "forward_patch_ref": applied.forward_patch_path,
        "reverse_patch_ref": applied.reverse_patch_path,
        "apply_status": applied.apply_status,
        "max_metric_calls": max_metric_calls,
        "total_metric_calls": getattr(result, "total_metric_calls", None),
        "gepa_result": result.to_dict() if hasattr(result, "to_dict") else None,
        "promotion_status": "not_promoted",
    }
    out_path = workspace.gepa_dir / "phase4_source_spike.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["summary_ref"] = str(out_path)
    return payload


def _select(objectives: list[Any], slugs: Sequence[str]) -> list[Any]:
    if not slugs:
        return objectives
    wanted = set(slugs)
    selected = [objective for objective in objectives if objective.slug in wanted]
    missing = wanted - {objective.slug for objective in selected}
    if missing:
        raise ValueError(f"unknown objective slug(s): {sorted(missing)}")
    return selected
