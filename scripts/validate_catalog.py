#!/usr/bin/env python3
"""Deterministic public-catalog, CLI-listing, and install checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXPECTED = {
    "baton", "deslop", "expert-review", "explain-system", "pr-preflight",
    "pr-review-feedback", "security-review", "skill-forge", "skill-grinder", "vet-idea",
}
GROUPS = {
    "Software delivery": ["pr-preflight", "pr-review-feedback", "security-review"],
    "Thinking and review": ["vet-idea", "expert-review", "explain-system"],
    "Agent operations": ["baton", "skill-grinder", "skill-forge"],
    "Writing": ["deslop"],
}
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".txt"}
FORBIDDEN_TEXT = {
    "Care" + " AI": "company-specific product",
    "Go" + "Daddy": "company identifier",
    "gd" + "corp": "company identifier",
    "skillopt" + "-framework": "private sibling dependency",
    "pre-" + "grinder": "backup snapshot name",
    "public-" + "eval": "local evaluation directory",
    "domain-routed-" + "intent-analyzer": "local component identifier",
}
FORBIDDEN_NAMES = {".DS_Store", "__pycache__"}
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BUNDLED_PATH = re.compile(r"(?<![\w/])((?:scripts|references|assets)/[A-Za-z0-9_./-]+)")


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        fail(f"{path}: unclosed YAML frontmatter")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([a-zA-Z0-9_-]+):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def validate_static(root: Path) -> None:
    skill_dirs = {path.parent.name: path.parent for path in (root / "skills").glob("*/SKILL.md")}
    if set(skill_dirs) != EXPECTED:
        fail(f"expected skills {sorted(EXPECTED)}, found {sorted(skill_dirs)}")
    config = json.loads((root / "skills.sh.json").read_text(encoding="utf-8"))
    if config.get("$schema") != "https://skills.sh/schemas/skills.sh.schema.json":
        fail("skills.sh.json has the wrong schema")
    actual_groups = {group.get("title"): group.get("skills") for group in config.get("groupings", [])}
    if actual_groups != GROUPS:
        fail(f"skills.sh.json groups differ from the catalog contract: {actual_groups}")
    grouped = [skill for skills in actual_groups.values() for skill in skills]
    if len(grouped) != len(set(grouped)) or set(grouped) != EXPECTED:
        fail("skills.sh.json must group each expected skill exactly once")

    for name, directory in sorted(skill_dirs.items()):
        fields = parse_frontmatter(directory / "SKILL.md")
        if fields.get("name") != name:
            fail(f"{directory}: frontmatter name must match directory")
        if not fields.get("description"):
            fail(f"{directory}: missing frontmatter description")
        metadata = directory / "agents" / "openai.yaml"
        if metadata.exists():
            metadata_text = metadata.read_text(encoding="utf-8")
            if not metadata_text.startswith("interface:\n"):
                fail(f"{metadata}: must use the interface mapping")
            for key in ("display_name:", "short_description:", "default_prompt:"):
                if key not in metadata_text:
                    fail(f"{metadata}: missing {key}")

    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        lower_name = path.name.lower()
        if (
            path.name in FORBIDDEN_NAMES
            or path.suffix == ".pyc"
            or lower_name.endswith((".bak", ".orig", "~"))
            or ".pre-" in lower_name
            or "backup" in lower_name
        ):
            fail(f"forbidden generated or backup file: {path.relative_to(root)}")
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"/(?:Users|home)/[^/\s]+", text) or re.search(r"[A-Za-z]:\\Users\\", text):
            fail(f"{path.relative_to(root)} contains a machine-specific home path")
        if ("/" + "Projects" + "/") in text:
            fail(f"{path.relative_to(root)} contains a local project path")
        for needle, label in FORBIDDEN_TEXT.items():
            if needle.lower() in text.lower():
                fail(f"{path.relative_to(root)} contains {label}: {needle}")

    for skill_dir in skill_dirs.values():
        for source in skill_dir.rglob("*.md"):
            text = source.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(text):
                clean = target.split("#", 1)[0].strip()
                if not clean or clean.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                resolved = (source.parent / clean).resolve()
                try:
                    resolved.relative_to(skill_dir.resolve())
                except ValueError:
                    fail(f"{source.relative_to(root)} has an escaping internal link: {target}")
                if not resolved.exists():
                    fail(f"{source.relative_to(root)} has broken internal link: {target}")
            if source.name == "SKILL.md":
                for target in BUNDLED_PATH.findall(text):
                    clean = target.rstrip(".,:;)")
                    if not (skill_dir / clean).exists():
                        fail(f"{source.relative_to(root)} references missing bundled path: {clean}")


def validate_list_output(path: Path) -> None:
    text = ANSI.sub("", path.read_text(encoding="utf-8"))
    match = re.search(r"Found\s+(\d+)\s+skills", text)
    if not match or int(match.group(1)) != len(EXPECTED):
        fail("skills CLI did not report exactly ten skills")
    listed = set(re.findall(r"^│\s{4}([a-z0-9-]+)\s*$", text, re.MULTILINE))
    if listed != EXPECTED:
        fail(f"skills CLI listed {sorted(listed)}, expected {sorted(EXPECTED)}")


def validate_install(home: Path) -> None:
    canonical_root = home / ".agents" / "skills"
    canonical = {path.name for path in canonical_root.iterdir() if path.is_dir()}
    if canonical != EXPECTED:
        fail(f"canonical install has {sorted(canonical)}, expected {sorted(EXPECTED)}")
    claude_root = home / ".claude" / "skills"
    for skill in EXPECTED:
        link = claude_root / skill
        if not link.is_symlink():
            fail(f"Claude install is not a symlink: {link}")
        if link.resolve() != (canonical_root / skill).resolve():
            fail(f"Claude symlink does not target canonical copy: {link}")
    lock_path = home / ".agents" / ".skill-lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid global skill lock: {exc}")
    if set(lock.get("skills", {})) != EXPECTED:
        fail("global skill lock does not contain exactly the installed catalog")
    for skill, entry in lock["skills"].items():
        if not entry.get("source") or not entry.get("skillFolderHash"):
            fail(f"lock entry for {skill} cannot support update checks")


def validate_known_validator_warning(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not str(payload.get("skill_dir", "")).endswith("/skills/skill-grinder"):
        fail("validator warning exception is only valid for skill-grinder")
    warnings = [result for result in payload.get("results", []) if result.get("level") == "warning"]
    if payload.get("errors") != 0 or len(warnings) != 1:
        fail("skill-grinder must have zero validator errors and exactly one known warning")
    warning = warnings[0]
    if (
        warning.get("category") != "Tokens"
        or warning.get("file") != "SKILL.md"
        or "spec recommends < 5000" not in warning.get("message", "")
    ):
        fail(f"unexpected skill-grinder validator warning: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--list-output", type=Path)
    parser.add_argument("--home", type=Path)
    parser.add_argument("--validator-json", type=Path)
    args = parser.parse_args()
    try:
        validate_static(args.root.resolve())
        if args.list_output:
            validate_list_output(args.list_output)
        if args.home:
            validate_install(args.home.resolve())
        if args.validator_json:
            validate_known_validator_warning(args.validator_json)
    except (ValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"catalog validation failed: {exc}", file=sys.stderr)
        return 1
    print("catalog validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
