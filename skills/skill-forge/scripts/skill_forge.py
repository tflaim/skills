#!/usr/bin/env python3
"""Self-contained helper for validation-gated Skill Forge runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MODES = {"quality", "compression", "exploratory"}
STATUSES = {"Found", "Accepted", "Promoted", "Compressed", "Rejected"}
MANIFEST_SCHEMA = "skill-forge-run-v1"
SCORE_SCHEMA = "skill-forge-score-v1"
ADEQUACY_SCHEMA = "skill-forge-validation-adequacy-v1"
RECEIPT_SCHEMA = "skill-forge-candidate-receipt-v1"
DECISION_SCHEMA = "skill-forge-decision-v1"


class SkillForgeError(Exception):
    """Raised for invalid or incomparable run evidence."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SkillForgeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: str | Path) -> Any:
    try:
        with Path(path).expanduser().open(encoding="utf-8") as handle:
            return json.load(handle, object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as exc:
        raise SkillForgeError(f"cannot read JSON {path}: {exc}") from exc


def iter_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    try:
        with Path(path).expanduser().open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line, object_pairs_hook=reject_duplicate_keys)
                except json.JSONDecodeError as exc:
                    raise SkillForgeError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
                if not isinstance(value, dict):
                    raise SkillForgeError(f"JSONL row at {path}:{line_number} must be an object")
                yield value
    except OSError as exc:
        raise SkillForgeError(f"cannot read JSONL {path}: {exc}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def payload_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_hash(path: str | Path) -> str:
    try:
        return hashlib.sha256(Path(path).expanduser().read_bytes()).hexdigest()
    except OSError as exc:
        raise SkillForgeError(f"cannot read file {path}: {exc}") from exc


def write_json_new(path: str | Path, value: Any) -> None:
    target = Path(path).expanduser()
    if target.exists():
        raise SkillForgeError(f"refusing to overwrite existing artifact: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SkillForgeError(f"{field} must be a non-empty string")
    return value.strip()


def require_sha256(value: Any, field: str) -> str:
    parsed = require_string(value, field)
    if not re.fullmatch(r"[0-9a-f]{64}", parsed):
        raise SkillForgeError(f"{field} must be a lowercase SHA-256 digest")
    return parsed


def require_tags(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if value is None and allow_empty:
        return []
    if not isinstance(value, list) or (not allow_empty and not value):
        raise SkillForgeError(f"{field} must be a list of non-empty strings")
    if any(not isinstance(tag, str) or not tag.strip() for tag in value):
        raise SkillForgeError(f"{field} must be a list of non-empty strings")
    tags = [tag.strip() for tag in value]
    if len(tags) != len(set(tags)):
        raise SkillForgeError(f"{field} contains duplicate tags")
    return sorted(tags)


def parse_nonnegative_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise SkillForgeError(f"{field} must be a finite non-negative number")
    parsed = float(value)
    if parsed < 0:
        raise SkillForgeError(f"{field} must be a finite non-negative number")
    return parsed


def parse_nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SkillForgeError(f"{field} must be a non-negative integer")
    return value


def normalize_cases(rows: Iterable[dict[str, Any]], run_id: str, validation_pct: int) -> dict[str, list[dict[str, Any]]]:
    if validation_pct <= 0 or validation_pct >= 100:
        raise SkillForgeError("validation-pct must be greater than 0 and less than 100")
    raw = list(rows)
    if not raw:
        raise SkillForgeError("cases file must contain at least one case")
    explicit = ["split" in row for row in raw]
    if any(explicit) and not all(explicit):
        raise SkillForgeError("cases must either all declare split or all use deterministic splitting")
    seen: set[str] = set()
    result = {"train": [], "validation": []}
    for index, row in enumerate(raw):
        case_id = require_string(row.get("id"), f"cases[{index}].id")
        if case_id in seen:
            raise SkillForgeError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        prompt = require_string(row.get("prompt"), f"cases[{index}].prompt")
        normalized = dict(row)
        normalized["id"] = case_id
        normalized["prompt"] = prompt
        normalized["tags"] = require_tags(row.get("tags"), f"cases[{index}].tags")
        if all(explicit):
            split = row.get("split")
            if split not in result:
                raise SkillForgeError(f"cases[{index}].split must be train or validation")
        else:
            bucket = int(hashlib.sha256(f"{run_id}:{case_id}".encode()).hexdigest()[:8], 16) % 100
            split = "validation" if bucket < validation_pct else "train"
        normalized["split"] = split
        result[split].append(normalized)
    if not result["train"] or not result["validation"]:
        raise SkillForgeError("run requires non-empty train and validation splits")
    return result


def normalize_test_commitments(rows: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        case_id = require_string(row.get("id"), f"test commitments[{index}].id")
        if case_id in seen:
            raise SkillForgeError(f"duplicate locked-test case id: {case_id}")
        seen.add(case_id)
        normalized.append({
            "id": case_id,
            "commitment_sha256": require_sha256(
                row.get("commitment_sha256"),
                f"test commitments[{index}].commitment_sha256",
            ),
        })
    if not normalized:
        raise SkillForgeError("locked-test commitments must contain at least one case")
    return normalized


def command_init_run(args: argparse.Namespace) -> int:
    skill = Path(args.skill).expanduser().resolve()
    if not skill.is_file():
        raise SkillForgeError(f"skill does not exist: {skill}")
    run_dir = Path(args.run_dir).expanduser().resolve()
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SkillForgeError(f"run directory must be new or empty: {run_dir}")
    run_id = args.run_id or hashlib.sha256(f"{skill}:{file_hash(skill)}".encode()).hexdigest()[:16]
    splits = normalize_cases(iter_jsonl(args.cases), run_id, args.validation_pct)
    test_commitments = normalize_test_commitments(iter_jsonl(args.test_commitments))
    visible_ids = {row["id"] for rows in splits.values() for row in rows}
    duplicate_ids = sorted(visible_ids & {row["id"] for row in test_commitments})
    if duplicate_ids:
        raise SkillForgeError(f"case ids overlap visible and locked splits: {', '.join(duplicate_ids)}")
    run_dir.mkdir(parents=True, exist_ok=True)
    split_hashes: dict[str, str] = {}
    split_case_ids: dict[str, list[str]] = {}
    for split, rows in splits.items():
        write_jsonl(run_dir / "cases" / f"{split}.jsonl", rows)
        split_hashes[split] = payload_hash(rows)
        split_case_ids[split] = [row["id"] for row in rows]
    write_jsonl(run_dir / "cases" / "test-commitments.jsonl", test_commitments)
    split_hashes["test"] = payload_hash(test_commitments)
    split_case_ids["test"] = [row["id"] for row in test_commitments]
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "run_id": run_id,
        "mode": args.mode,
        "skill_path": str(skill),
        "skill_sha256": file_hash(skill),
        "split_sha256": split_hashes,
        "split_case_ids": split_case_ids,
        "limits": {
            "max_edits": args.max_edits,
            "max_edit_chars": args.max_edit_chars,
            "max_total_changed_chars": args.max_total_changed_chars,
        },
    }
    manifest["manifest_sha256"] = payload_hash(manifest)
    write_json_new(run_dir / "manifest.json", manifest)
    for name, content in (
        ("results.tsv", "candidate\tsplit\tscore\tmax_score\tmandatory_failures\tstatus\n"),
        ("changelog.md", "# Changelog\n"),
        ("rejected-edits.jsonl", ""),
    ):
        (run_dir / name).write_text(content, encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def load_run(run_dir: str | Path) -> tuple[Path, dict[str, Any]]:
    root = Path(run_dir).expanduser().resolve()
    manifest = load_json(root / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise SkillForgeError(f"manifest must use {MANIFEST_SCHEMA}")
    claimed = manifest.get("manifest_sha256")
    bare = dict(manifest)
    bare.pop("manifest_sha256", None)
    if claimed != payload_hash(bare):
        raise SkillForgeError("manifest hash is invalid")
    for split in ("train", "validation"):
        rows = list(iter_jsonl(root / "cases" / f"{split}.jsonl"))
        if payload_hash(rows) != manifest["split_sha256"].get(split):
            raise SkillForgeError(f"{split} split differs from the manifest")
        ids = [require_string(row.get("id"), f"{split}.id") for row in rows]
        if ids != manifest["split_case_ids"].get(split):
            raise SkillForgeError(f"{split} case ids differ from the manifest")
    test_commitments = normalize_test_commitments(iter_jsonl(root / "cases" / "test-commitments.jsonl"))
    if payload_hash(test_commitments) != manifest["split_sha256"].get("test"):
        raise SkillForgeError("locked-test commitments differ from the manifest")
    test_ids = [row["id"] for row in test_commitments]
    if test_ids != manifest["split_case_ids"].get("test"):
        raise SkillForgeError("locked-test case ids differ from the manifest")
    all_ids = [item for ids in manifest["split_case_ids"].values() for item in ids]
    if len(all_ids) != len(set(all_ids)):
        raise SkillForgeError("case ids must be unique across all splits")
    return root, manifest


def frontmatter_end(text: str) -> int:
    if not text.startswith("---\n"):
        return 0
    end = text.find("\n---\n", 4)
    return end + 5 if end >= 0 else 0


def command_apply_edits(args: argparse.Namespace) -> int:
    root, manifest = load_run(args.run_dir)
    source = Path(args.skill).expanduser().resolve()
    text = source.read_text(encoding="utf-8")
    if file_hash(source) != manifest["skill_sha256"]:
        raise SkillForgeError("source skill does not match the run baseline")
    patch = load_json(args.edits)
    if not isinstance(patch, dict) or patch.get("base_sha256") != manifest["skill_sha256"]:
        raise SkillForgeError("edit file must bind to the baseline skill hash")
    edits = patch.get("edits")
    if not isinstance(edits, list) or not edits:
        raise SkillForgeError("edits must be a non-empty list")
    limits = manifest["limits"]
    if len(edits) > limits["max_edits"]:
        raise SkillForgeError("edit count exceeds run limit")
    targets: set[str] = set()
    total_changed = 0
    ranges: list[tuple[int, int]] = []
    replacements: list[tuple[int, int, str]] = []
    for index, edit in enumerate(edits):
        if not isinstance(edit, dict) or edit.get("op") != "replace":
            raise SkillForgeError(f"edits[{index}] must be an exact replace operation")
        target = edit.get("target")
        if not isinstance(target, str) or not target:
            raise SkillForgeError(f"edits[{index}].target must be a non-empty exact string")
        replacement = edit.get("replacement")
        if not isinstance(replacement, str):
            raise SkillForgeError(f"edits[{index}].replacement must be a string")
        if target in targets:
            raise SkillForgeError("patch targets must be unique")
        targets.add(target)
        if text.count(target) != 1:
            raise SkillForgeError(f"patch target must occur exactly once: {target[:80]!r}")
        start = text.index(target)
        end = start + len(target)
        if not args.allow_frontmatter_edits and start < frontmatter_end(text):
            raise SkillForgeError("frontmatter edits require --allow-frontmatter-edits")
        if any(start < prior_end and prior_start < end for prior_start, prior_end in ranges):
            raise SkillForgeError("patch targets overlap")
        changed = len(target) + len(replacement)
        if changed > limits["max_edit_chars"]:
            raise SkillForgeError("an edit exceeds max-edit-chars")
        total_changed += changed
        ranges.append((start, end))
        replacements.append((start, end, replacement))
    if total_changed > limits["max_total_changed_chars"]:
        raise SkillForgeError("patch exceeds max-total-changed-chars")
    candidate = text
    for start, end, replacement in sorted(replacements, reverse=True):
        candidate = candidate[:start] + replacement + candidate[end:]
    out = Path(args.out).expanduser().resolve()
    if out.exists():
        raise SkillForgeError(f"refusing to overwrite candidate: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(candidate, encoding="utf-8")
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "run_id": manifest["run_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "base_sha256": manifest["skill_sha256"],
        "candidate_sha256": file_hash(out),
        "edit_count": len(edits),
        "total_changed_chars": total_changed,
    }
    write_json_new(str(out) + ".receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


@dataclass(frozen=True)
class Score:
    split: str
    skill_sha256: str
    evaluator_sha256: str
    score: float
    max_score: float
    mandatory_failures: int
    infrastructure_failures: int
    cases: tuple[tuple[str, float, float, int], ...]


def parse_score(
    payload: Any,
    manifest: dict[str, Any],
    expected_split: str,
    expected_skill_sha256: str,
) -> Score:
    if not isinstance(payload, dict) or payload.get("schema_version") != SCORE_SCHEMA:
        raise SkillForgeError(f"score file must use {SCORE_SCHEMA}")
    if payload.get("split") != expected_split:
        raise SkillForgeError(f"score file must be for {expected_split}")
    if payload.get("run_id") != manifest["run_id"]:
        raise SkillForgeError("score file does not match the run id")
    if payload.get("manifest_sha256") != manifest["manifest_sha256"]:
        raise SkillForgeError("score file does not match the run manifest")
    skill_sha256 = require_sha256(payload.get("skill_sha256"), "skill_sha256")
    if skill_sha256 != expected_skill_sha256:
        raise SkillForgeError("score file does not match the expected skill")
    evaluator_sha256 = require_sha256(payload.get("evaluator_sha256"), "evaluator_sha256")
    rows = payload.get("cases")
    if not isinstance(rows, list) or not rows:
        raise SkillForgeError("score cases must be a non-empty list")
    expected_ids = manifest["split_case_ids"][expected_split]
    parsed: list[tuple[str, float, float, int]] = []
    case_infrastructure: list[int] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise SkillForgeError(f"score cases[{index}] must be an object")
        case_id = require_string(row.get("id"), f"score cases[{index}].id")
        score = parse_nonnegative_number(row.get("score"), f"score cases[{index}].score")
        maximum = parse_nonnegative_number(row.get("max_score"), f"score cases[{index}].max_score")
        failures = parse_nonnegative_int(row.get("mandatory_failures"), f"score cases[{index}].mandatory_failures")
        infrastructure = parse_nonnegative_int(
            row.get("infrastructure_failures", 0),
            f"score cases[{index}].infrastructure_failures",
        )
        if maximum <= 0 or score > maximum:
            raise SkillForgeError(f"score cases[{index}] has an invalid score range")
        parsed.append((case_id, score, maximum, failures))
        case_infrastructure.append(infrastructure)
    ids = [row[0] for row in parsed]
    if ids != expected_ids or len(ids) != len(set(ids)):
        raise SkillForgeError(f"score cases do not match frozen {expected_split} cases")
    total = sum(row[1] for row in parsed)
    maximum = sum(row[2] for row in parsed)
    failures = sum(row[3] for row in parsed)
    claimed_total = parse_nonnegative_number(payload.get("score"), "score")
    claimed_maximum = parse_nonnegative_number(payload.get("max_score"), "max_score")
    claimed_failures = parse_nonnegative_int(payload.get("mandatory_failures"), "mandatory_failures")
    infrastructure = sum(case_infrastructure)
    claimed_infrastructure = parse_nonnegative_int(payload.get("infrastructure_failures", 0), "infrastructure_failures")
    if not math.isclose(total, claimed_total) or not math.isclose(maximum, claimed_maximum) or failures != claimed_failures or infrastructure != claimed_infrastructure:
        raise SkillForgeError("aggregate score fields do not match per-case results")
    return Score(
        expected_split,
        skill_sha256,
        evaluator_sha256,
        total,
        maximum,
        failures,
        infrastructure,
        tuple(parsed),
    )


def validate_comparable(current: Score, candidate: Score) -> None:
    if current.infrastructure_failures or candidate.infrastructure_failures:
        raise SkillForgeError("infrastructure failures invalidate score evidence")
    if current.split != candidate.split:
        raise SkillForgeError("score splits do not match")
    if current.evaluator_sha256 != candidate.evaluator_sha256:
        raise SkillForgeError("score evaluators do not match")
    if [row[0] for row in current.cases] != [row[0] for row in candidate.cases]:
        raise SkillForgeError("score case ids do not match")
    if [row[2] for row in current.cases] != [row[2] for row in candidate.cases]:
        raise SkillForgeError("score maximums do not match")
    if not math.isclose(current.max_score, candidate.max_score):
        raise SkillForgeError("score maximums do not match")


def check_validation_adequacy(train_payload: Any, root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    train = parse_score(train_payload, manifest, "train", manifest["skill_sha256"])
    if train.mandatory_failures:
        raise SkillForgeError("baseline train evidence has mandatory failures")
    train_cases = {row["id"]: row for row in iter_jsonl(root / "cases" / "train.jsonl")}
    failure_ids = [case_id for case_id, score, maximum, _ in train.cases if score < maximum]
    untagged = [case_id for case_id in failure_ids if not train_cases[case_id].get("tags")]
    if untagged:
        raise SkillForgeError(f"failed train cases require tags: {', '.join(untagged)}")
    failure_tags = sorted({tag for case_id in failure_ids for tag in train_cases[case_id].get("tags", [])})
    validation_tags = sorted({tag for row in iter_jsonl(root / "cases" / "validation.jsonl") for tag in row.get("tags", [])})
    missing = sorted(set(failure_tags) - set(validation_tags))
    return {
        "schema_version": ADEQUACY_SCHEMA,
        "run_id": manifest["run_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "adequate": not missing,
        "train_failure_case_ids": failure_ids,
        "train_failure_tags": failure_tags,
        "validation_tags": validation_tags,
        "missing_tags": missing,
        "train_score_sha256": payload_hash(train_payload),
    }


def command_check_validation(args: argparse.Namespace) -> int:
    root, manifest = load_run(args.run_dir)
    result = check_validation_adequacy(load_json(args.train_score), root, manifest)
    write_json_new(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["adequate"] else 2


def validate_receipt(receipt: Any, manifest: dict[str, Any], candidate_skill: Path) -> None:
    if not isinstance(receipt, dict) or receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise SkillForgeError(f"candidate receipt must use {RECEIPT_SCHEMA}")
    expected = {
        "run_id": manifest["run_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "base_sha256": manifest["skill_sha256"],
        "candidate_sha256": file_hash(candidate_skill),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise SkillForgeError(f"candidate receipt does not match {field}")


def command_decide(args: argparse.Namespace) -> int:
    root, manifest = load_run(args.run_dir)
    if args.mode and args.mode != manifest["mode"]:
        raise SkillForgeError("mode does not match the run manifest")
    mode = manifest["mode"]
    current_skill = Path(args.current_skill).expanduser().resolve()
    candidate_skill = Path(args.candidate_skill).expanduser().resolve()
    if file_hash(current_skill) != manifest["skill_sha256"]:
        raise SkillForgeError("current skill does not match the run baseline")
    receipt_payload = load_json(args.candidate_receipt)
    validate_receipt(receipt_payload, manifest, candidate_skill)
    current_payload = load_json(args.current)
    candidate_payload = load_json(args.candidate)
    candidate_sha256 = file_hash(candidate_skill)
    current = parse_score(current_payload, manifest, "validation", manifest["skill_sha256"])
    candidate = parse_score(candidate_payload, manifest, "validation", candidate_sha256)
    validate_comparable(current, candidate)
    if current.mandatory_failures:
        raise SkillForgeError("baseline validation evidence has mandatory failures")
    adequacy_payload = load_json(args.validation_adequacy)
    recomputed = check_validation_adequacy(load_json(args.train_score), root, manifest)
    if adequacy_payload != recomputed:
        raise SkillForgeError("validation adequacy artifact failed recomputation")
    if mode != "exploratory" and not recomputed["adequate"]:
        raise SkillForgeError("validation does not cover observed train failure tags")
    train_current = parse_score(load_json(args.train_score), manifest, "train", manifest["skill_sha256"])
    train_candidate = parse_score(load_json(args.candidate_train_score), manifest, "train", candidate_sha256)
    validate_comparable(train_current, train_candidate)
    if train_candidate.mandatory_failures:
        raise SkillForgeError("candidate train evidence has mandatory failures")
    if mode != "exploratory":
        current_train_cases = {row[0]: row for row in train_current.cases}
        regressed_failures = [
            case_id
            for case_id, score, maximum, _ in train_candidate.cases
            if current_train_cases[case_id][1] < maximum and score < current_train_cases[case_id][1]
        ]
        if regressed_failures:
            raise SkillForgeError(
                "candidate regressed on original train failures: " + ", ".join(regressed_failures)
            )
    status = "Rejected"
    reason = "candidate did not satisfy the selected mode"
    validation_delta = candidate.score - current.score
    test_delta: float | None = None
    if candidate.mandatory_failures:
        reason = "candidate has mandatory validation failures"
    elif mode == "exploratory":
        if train_candidate and not train_candidate.mandatory_failures and train_candidate.score > train_current.score:
            status, reason = "Found", "train evidence improved; exploratory runs do not accept candidates"
    elif mode == "quality":
        if validation_delta > 0:
            status, reason = "Accepted", "strict held-out validation improvement"
        elif validation_delta == 0 and train_candidate and train_candidate.score > train_current.score:
            status, reason = "Found", "train improved but validation tied"
        else:
            reason = "no strict held-out validation improvement"
    elif mode == "compression":
        if validation_delta >= 0 and candidate_skill.stat().st_size < current_skill.stat().st_size:
            status, reason = "Compressed", "validation held and prompt shrank"
        elif validation_delta > 0:
            status, reason = "Accepted", "validation improved but prompt did not shrink"
        else:
            reason = "compression did not preserve validation while shrinking the prompt"
    if args.test_current or args.test_candidate:
        if not args.test_current or not args.test_candidate:
            raise SkillForgeError("both locked-test scores are required")
        test_current = parse_score(
            load_json(args.test_current),
            manifest,
            "test",
            manifest["skill_sha256"],
        )
        test_candidate = parse_score(load_json(args.test_candidate), manifest, "test", candidate_sha256)
        validate_comparable(test_current, test_candidate)
        if test_current.mandatory_failures:
            raise SkillForgeError("baseline locked-test evidence has mandatory failures")
        test_delta = test_candidate.score - test_current.score
        if status == "Accepted" and mode == "quality" and test_candidate.mandatory_failures == 0 and test_delta >= 0:
            status, reason = "Promoted", "validation improved and locked test did not regress"
        elif status == "Accepted" and mode == "quality":
            reason = (
                "validation improved but locked test has mandatory failures; candidate remains accepted"
                if test_candidate.mandatory_failures
                else "validation improved but locked test regressed; candidate remains accepted"
            )
        elif status == "Compressed" and (test_candidate.mandatory_failures or test_delta < 0):
            status, reason = "Rejected", "compression candidate regressed on locked test"
    decision = {
        "schema_version": DECISION_SCHEMA,
        "run_id": manifest["run_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "mode": mode,
        "status": status,
        "reason": reason,
        "validation_delta": validation_delta,
        "test_delta": test_delta,
        "prompt_bytes_delta": candidate_skill.stat().st_size - current_skill.stat().st_size,
        "current_skill_sha256": file_hash(current_skill),
        "candidate_skill_sha256": file_hash(candidate_skill),
        "current_validation_sha256": payload_hash(current_payload),
        "candidate_validation_sha256": payload_hash(candidate_payload),
        "validation_adequacy_sha256": payload_hash(adequacy_payload),
        "candidate_receipt_sha256": payload_hash(receipt_payload),
    }
    decision["decision_sha256"] = payload_hash(decision)
    write_json_new(args.out, decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if status in {"Accepted", "Promoted", "Compressed"} else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Self-contained Skill Forge helper")
    commands = parser.add_subparsers(dest="command", required=True)
    init_run = commands.add_parser("init-run", help="Create a deterministic run and frozen splits")
    init_run.add_argument("--skill", required=True)
    init_run.add_argument("--cases", required=True)
    init_run.add_argument("--test-commitments", required=True)
    init_run.add_argument("--run-dir", required=True)
    init_run.add_argument("--mode", required=True, choices=sorted(MODES))
    init_run.add_argument("--run-id")
    init_run.add_argument("--validation-pct", type=int, default=20)
    init_run.add_argument("--max-edits", type=int, default=4)
    init_run.add_argument("--max-edit-chars", type=int, default=2000)
    init_run.add_argument("--max-total-changed-chars", type=int, default=4000)
    init_run.set_defaults(func=command_init_run)
    apply_edits = commands.add_parser("apply-edits", help="Apply exact baseline-bound replacements")
    apply_edits.add_argument("--skill", required=True)
    apply_edits.add_argument("--edits", required=True)
    apply_edits.add_argument("--out", required=True)
    apply_edits.add_argument("--run-dir", required=True)
    apply_edits.add_argument("--allow-frontmatter-edits", action="store_true")
    apply_edits.set_defaults(func=command_apply_edits)
    check = commands.add_parser("check-validation", help="Check validation coverage of observed train failures")
    check.add_argument("--run-dir", required=True)
    check.add_argument("--train-score", required=True)
    check.add_argument("--out", required=True)
    check.set_defaults(func=command_check_validation)
    decide = commands.add_parser("decide", help="Write a deterministic status decision")
    decide.add_argument("--mode", choices=sorted(MODES))
    decide.add_argument("--run-dir", required=True)
    decide.add_argument("--current", required=True)
    decide.add_argument("--candidate", required=True)
    decide.add_argument("--current-skill", required=True)
    decide.add_argument("--candidate-skill", required=True)
    decide.add_argument("--candidate-receipt", required=True)
    decide.add_argument("--validation-adequacy", required=True)
    decide.add_argument("--train-score", required=True)
    decide.add_argument("--candidate-train-score", required=True)
    decide.add_argument("--test-current")
    decide.add_argument("--test-candidate")
    decide.add_argument("--out", required=True)
    decide.set_defaults(func=command_decide)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (SkillForgeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
