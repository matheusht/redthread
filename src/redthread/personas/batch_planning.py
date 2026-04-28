"""Batch planning helpers for prompting-layer persona diversity."""

from __future__ import annotations

from collections.abc import Mapping

from redthread.personas.prompt_layers import PromptingLayerProfile


def prompting_layer_profiles_for_batch(
    profile: PromptingLayerProfile | None,
    count: int,
    layer_weights: Mapping[str, float] | None = None,
) -> list[PromptingLayerProfile | None]:
    """Distribute enabled prompting layers across a persona batch.

    The input profile is metadata-only. This helper never loads prompt bodies. If
    only one persona is requested, it receives the full profile. For larger
    batches, enabled layers are spread across personas so the batch covers the
    profile without forcing every persona to use every layer.
    """
    if count <= 0:
        return []
    if profile is None or profile.is_empty:
        return [profile] * count

    layers = _weighted_layer_sequence(profile.enabled_layers, layer_weights)
    if count == 1 or len(layers) <= 1:
        return [profile] * count

    buckets: list[list[str]] = [[] for _ in range(count)]
    for index, layer in enumerate(layers):
        buckets[index % count].append(layer)
    for index, bucket in enumerate(buckets):
        if not bucket:
            bucket.append(layers[index % len(layers)])

    return [_profile_with_layers(profile, bucket) for bucket in buckets]


def _weighted_layer_sequence(
    layers: list[str],
    layer_weights: Mapping[str, float] | None,
) -> list[str]:
    if not layer_weights:
        return layers
    weighted: list[str] = []
    for layer in sorted(layers, key=lambda item: (-layer_weights.get(item, 1.0), item)):
        repeats = max(1, round(layer_weights.get(layer, 1.0)))
        weighted.extend([layer] * repeats)
    return weighted or layers


def _profile_with_layers(
    base: PromptingLayerProfile,
    enabled_layers: list[str],
) -> PromptingLayerProfile:
    enabled = set(enabled_layers)
    return PromptingLayerProfile(
        plain_language="plain_language" in enabled,
        strategic_distraction="strategic_distraction" in enabled,
        narrative_embedding="narrative_embedding" in enabled,
        persona_modulation="persona_modulation" in enabled,
        guardrail_rebuttal_resilience="guardrail_rebuttal_resilience" in enabled,
        reasoning_boundary_pressure="reasoning_boundary_pressure" in enabled,
        source_fixture_ids=base.source_fixture_ids,
        raw_prompt_loaded=False,
        raw_prompt_policy=base.raw_prompt_policy,
    )
