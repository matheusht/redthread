"""Unit tests for safe string formatting in gepa_defense_candidate (Issue #100)."""

from __future__ import annotations

import ast

from redthread.research.gepa_defense_candidate import _assignment, render_defense_assets_candidate


def test_assignment_standard_string() -> None:
    code = _assignment("VAR", "Hello world")
    parsed = ast.parse(code)
    assert len(parsed.body) == 1
    assert isinstance(parsed.body[0], ast.Assign)
    assert "Hello world" in code


def test_assignment_invalid_escape_fallback() -> None:
    # An invalid unicode escape sequence like \\U123 without 8 hex digits causes SyntaxError in normal strings
    raw_val = "Special pattern \\U123 and \\x not hex"
    code = _assignment("VAR", raw_val)
    parsed = ast.parse(code)
    assert len(parsed.body) == 1
    # Check that execution/ast evaluation recovers the exact string
    executed: dict[str, str] = {}
    exec(code, {}, executed)
    assert executed["VAR"] == raw_val


def test_assignment_with_triple_quotes() -> None:
    raw_val = 'Some text with """ triple quotes """ inside'
    code = _assignment("VAR", raw_val)
    parsed = ast.parse(code)
    assert len(parsed.body) == 1
    executed: dict[str, str] = {}
    exec(code, {}, executed)
    assert executed["VAR"].strip() == raw_val


def test_render_candidate_preserves_syntax() -> None:
    before = 'DEFENSE_ARCHITECT_SYSTEM_PROMPT = """original"""\nDEFENSE_ARCHITECT_USER_TEMPLATE = """user"""\n'
    after = render_defense_assets_candidate(
        before,
        {"DEFENSE_ARCHITECT_SYSTEM_PROMPT": 'New prompt with \\U123 and """ quotes'},
    )
    ast.parse(after)
    executed: dict[str, str] = {}
    exec(after, {}, executed)
    assert "New prompt" in executed["DEFENSE_ARCHITECT_SYSTEM_PROMPT"]
