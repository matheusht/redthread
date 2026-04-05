from __future__ import annotations

import pytest

from redthread.personas.generator import PersonaGenerator


def test_normalize_persona_data_accepts_aliases() -> None:
    generator = PersonaGenerator.__new__(PersonaGenerator)
    normalized = generator._normalize_persona_data(
        {
            "full_name": "Alice Smith",
            "coverStory": "Internal audit follow-up.",
            "objective": "Extract hidden instructions.",
            "systemPrompt": "You are Alice Smith.",
            "strategies": ["cite urgency", "invoke authority"],
        }
    )

    assert normalized["name"] == "Alice Smith"
    assert normalized["cover_story"] == "Internal audit follow-up."
    assert normalized["hidden_objective"] == "Extract hidden instructions."
    assert normalized["system_prompt"] == "You are Alice Smith."
    assert normalized["allowed_strategies"] == ["cite urgency", "invoke authority"]


def test_normalize_persona_data_rejects_missing_cover_story() -> None:
    generator = PersonaGenerator.__new__(PersonaGenerator)
    with pytest.raises(ValueError, match="Missing required persona fields: cover_story"):
        generator._normalize_persona_data(
            {
                "name": "Alice Smith",
                "hidden_objective": "Extract hidden instructions.",
                "system_prompt": "You are Alice Smith.",
            }
        )
