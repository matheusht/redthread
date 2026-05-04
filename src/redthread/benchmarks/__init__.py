"""Benchmark fixture helpers for RedThread."""

from redthread.benchmarks.artifacts import (
    BenchmarkArtifactError,
    BenchmarkArtifactWriteResult,
    write_benchmark_report_artifact,
)
from redthread.benchmarks.campaigns import BenchmarkCampaignDraft, build_benchmark_campaign_draft
from redthread.benchmarks.dry_run import (
    BenchmarkDryRunError,
    BenchmarkDryRunReport,
    build_jailbreak_corpus_dry_run_report,
)
from redthread.benchmarks.hints import (
    BenchmarkHintProfile,
    build_fixture_hint_profile,
    build_fixture_hint_profiles,
)
from redthread.benchmarks.jailbreak_fixtures import (
    JAILBREAK_FIXTURE_SCHEMA_VERSION,
    JailbreakBenchmarkFixture,
    JailbreakFixtureError,
    load_jailbreak_fixture_file,
    load_jailbreak_fixture_pack,
)
from redthread.benchmarks.jailbreakbench import (
    jailbreakbench_fixture_pack_data,
    load_jailbreakbench_fixtures,
)
from redthread.benchmarks.live_replay_gate import (
    LIVE_REPLAY_ACKNOWLEDGEMENT,
    LIVE_REPLAY_DEFERRED_MESSAGE,
    BenchmarkLiveReplayGatePlan,
    build_live_replay_gate_plan,
)
from redthread.benchmarks.material_review import (
    MaterialImportResult,
    MaterialReviewError,
    approve_fixture_for_replay,
    import_reviewed_material,
)
from redthread.benchmarks.material_vault import (
    BENCHMARK_MATERIAL_ROOT_ENV,
    MATERIAL_MANIFEST_SCHEMA_VERSION,
    BenchmarkMaterialManifest,
    MaterialVaultError,
    benchmark_material_root,
    load_material_manifest,
    resolve_reviewed_material,
)
from redthread.benchmarks.material_verify import (
    BenchmarkMaterialVerification,
    verify_benchmark_material_manifest,
)
from redthread.benchmarks.models import (
    BenchmarkEvidenceMode,
    BenchmarkLane,
    BenchmarkNotScoredReason,
    BenchmarkPromotionImpact,
    BenchmarkRunMode,
    BenchmarkScorecard,
    BenchmarkScoreDimension,
)
from redthread.benchmarks.prompt_materials import (
    PromptMaterial,
    PromptMaterialError,
    load_prompt_material,
    load_replay_seed_prompts,
)
from redthread.benchmarks.regression_handoff import (
    BenchmarkRegressionCaseSummary,
    BenchmarkRegressionHandoffArtifact,
    BenchmarkRegressionHandoffError,
    BenchmarkRegressionSkip,
    build_benchmark_regression_handoff,
    write_benchmark_regression_handoff_artifact,
)
from redthread.benchmarks.replay import (
    ApprovedBenchmarkReplayBundle,
    BenchmarkReplayError,
    LocalBenchmarkTarget,
    run_approved_jailbreak_replay,
    run_approved_jailbreak_replay_with_regression_handoff,
)
from redthread.benchmarks.reports import (
    BenchmarkRunReport,
    BenchmarkVerdictSummary,
    build_benchmark_run_report,
)
from redthread.benchmarks.run_context import (
    BenchmarkRunContext,
    BenchmarkRunContextError,
    apply_benchmark_fixture_context,
)
from redthread.benchmarks.scoring import (
    SCORE_DIMENSION_WEIGHTS,
    build_unscored_scorecard,
    evidence_mode_score_cap,
    score_confirmed_benchmark,
)
from redthread.benchmarks.spiritual_spell import (
    load_spiritual_spell_fixtures,
    spiritual_spell_fixture_pack_data,
)

__all__ = [
    "BenchmarkArtifactError",
    "BenchmarkArtifactWriteResult",
    "BenchmarkCampaignDraft",
    "BenchmarkDryRunError",
    "BenchmarkDryRunReport",
    "BENCHMARK_MATERIAL_ROOT_ENV",
    "MATERIAL_MANIFEST_SCHEMA_VERSION",
    "BenchmarkHintProfile",
    "BenchmarkMaterialManifest",
    "BenchmarkEvidenceMode",
    "BenchmarkLane",
    "BenchmarkLiveReplayGatePlan",
    "BenchmarkMaterialVerification",
    "BenchmarkNotScoredReason",
    "BenchmarkPromotionImpact",
    "BenchmarkRunMode",
    "BenchmarkScorecard",
    "BenchmarkScoreDimension",
    "ApprovedBenchmarkReplayBundle",
    "BenchmarkRegressionCaseSummary",
    "BenchmarkRegressionHandoffArtifact",
    "BenchmarkRegressionHandoffError",
    "BenchmarkRegressionSkip",
    "BenchmarkReplayError",
    "BenchmarkRunContext",
    "BenchmarkRunContextError",
    "BenchmarkRunReport",
    "BenchmarkVerdictSummary",
    "JAILBREAK_FIXTURE_SCHEMA_VERSION",
    "PromptMaterial",
    "PromptMaterialError",
    "JailbreakBenchmarkFixture",
    "JailbreakFixtureError",
    "LIVE_REPLAY_ACKNOWLEDGEMENT",
    "LIVE_REPLAY_DEFERRED_MESSAGE",
    "LocalBenchmarkTarget",
    "MaterialImportResult",
    "MaterialReviewError",
    "MaterialVaultError",
    "SCORE_DIMENSION_WEIGHTS",
    "build_benchmark_campaign_draft",
    "build_benchmark_regression_handoff",
    "build_jailbreak_corpus_dry_run_report",
    "build_benchmark_run_report",
    "apply_benchmark_fixture_context",
    "approve_fixture_for_replay",
    "benchmark_material_root",
    "build_unscored_scorecard",
    "build_fixture_hint_profile",
    "build_fixture_hint_profiles",
    "build_live_replay_gate_plan",
    "evidence_mode_score_cap",
    "import_reviewed_material",
    "jailbreakbench_fixture_pack_data",
    "run_approved_jailbreak_replay",
    "run_approved_jailbreak_replay_with_regression_handoff",
    "load_jailbreak_fixture_file",
    "load_material_manifest",
    "load_jailbreak_fixture_pack",
    "load_jailbreakbench_fixtures",
    "load_prompt_material",
    "load_replay_seed_prompts",
    "resolve_reviewed_material",
    "load_spiritual_spell_fixtures",
    "score_confirmed_benchmark",
    "spiritual_spell_fixture_pack_data",
    "verify_benchmark_material_manifest",
    "write_benchmark_regression_handoff_artifact",
    "write_benchmark_report_artifact",
]
