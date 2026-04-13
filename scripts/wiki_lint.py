#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "docs" / "wiki"
INDEX = WIKI / "index.md"
LOG = WIKI / "log.md"
IGNORE = {INDEX, LOG, WIKI / "SCHEMA.md"}

REQUIRED_KEYS = {
    "title",
    "type",
    "status",
    "summary",
    "source_of_truth",
    "updated_by",
    "updated_at",
}


def md_files() -> list[Path]:
    return sorted(p for p in WIKI.rglob("*.md") if p.is_file())


def parse_frontmatter(text: str) -> tuple[set[str], bool]:
    if not text.startswith("---\n"):
        return set(), False
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return set(), False
    header = parts[0].splitlines()[1:]
    keys: set[str] = set()
    for line in header:
        if not line.strip() or line.lstrip().startswith("-"):
            continue
        if ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys, True


def substantive_page(path: Path) -> bool:
    if path in IGNORE:
        return False
    return True


def check_frontmatter(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    keys, ok = parse_frontmatter(text)
    if not ok:
        errors.append(f"{path.relative_to(ROOT)}: missing or malformed YAML frontmatter")
        return
    missing = sorted(REQUIRED_KEYS - keys)
    if missing:
        errors.append(
            f"{path.relative_to(ROOT)}: missing frontmatter keys: {', '.join(missing)}"
        )


def check_index_references(paths: list[Path], errors: list[str]) -> None:
    index_text = INDEX.read_text(encoding="utf-8")
    for path in paths:
        rel = path.relative_to(WIKI).as_posix()
        if path.name == "README.md":
            continue
        if rel not in index_text:
            errors.append(f"docs/wiki/index.md: missing link to {rel}")


def check_log_exists(errors: list[str]) -> None:
    if not LOG.exists():
        errors.append("docs/wiki/log.md: missing")
        return
    text = LOG.read_text(encoding="utf-8").strip()
    if not text.startswith("# Wiki Log"):
        errors.append("docs/wiki/log.md: expected '# Wiki Log' heading")


def check_readmes(paths: list[Path], errors: list[str]) -> None:
    expected = {
        WIKI / "entities" / "README.md",
        WIKI / "concepts" / "README.md",
        WIKI / "decisions" / "README.md",
        WIKI / "research" / "README.md",
        WIKI / "systems" / "README.md",
        WIKI / "timelines" / "README.md",
    }
    missing = sorted(p.relative_to(ROOT).as_posix() for p in expected if p not in paths)
    for item in missing:
        errors.append(f"{item}: missing family README")


def main() -> int:
    if not WIKI.exists():
        print("docs/wiki/: missing")
        return 1

    paths = md_files()
    errors: list[str] = []

    check_log_exists(errors)
    check_readmes(paths, errors)

    for path in paths:
        if substantive_page(path):
            check_frontmatter(path, errors)

    substantive = [p for p in paths if substantive_page(p)]
    check_index_references(substantive, errors)

    if errors:
        print("wiki-lint: FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("wiki-lint: OK")
    print(f"checked {len(paths)} markdown files under docs/wiki")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
