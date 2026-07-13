#!/usr/bin/env python3
"""Validate cumulative matched-pair evidence for a skill-grinder experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


MANIFEST_HEADER = [
    "split", "input_id", "input_sha256", "sample", "criterion", "criterion_sha256",
]
LEDGER_HEADER = ["experiment", *MANIFEST_HEADER, "verdict", "evidence"]
RESAMPLE_HEADER = ["experiment", "resample_batch", *MANIFEST_HEADER, "verdict", "evidence"]
VERDICTS = {"SAME", "BETTER", "WORSE"}


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_decision_contract(path: Path) -> dict[str, object]:
    if not path.is_file():
        fail(f"missing decision contract: {path}")
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid decision contract JSON in {path}: {exc}")
    if not isinstance(contract, dict):
        fail(f"decision contract must be an object: {path}")
    if not isinstance(contract.get("inputs"), dict) or not contract["inputs"]:
        fail(f"decision contract inputs must be a nonempty object: {path}")
    if not isinstance(contract.get("criteria"), dict) or not contract["criteria"]:
        fail(f"decision contract criteria must be a nonempty object: {path}")
    samples = contract.get("samples_per_input")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 1:
        fail(f"decision contract samples_per_input must be a positive integer: {path}")
    cap = contract.get("allowed_resample_count")
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
        fail(f"decision contract allowed_resample_count must be a nonnegative integer: {path}")
    for field in ("optimization_gate", "validation_gate", "noise_band_calculation"):
        if not isinstance(contract.get(field), dict) or not contract[field]:
            fail(f"decision contract {field} must be a nonempty object: {path}")
    checks = contract.get("mandatory_checks")
    if not isinstance(checks, list) or not checks or any(not isinstance(item, str) or not item.strip() for item in checks):
        fail(f"decision contract mandatory_checks must be a nonempty string list: {path}")
    threshold = contract.get("material_regression_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(float(threshold)) or threshold < 0:
        fail(f"decision contract material_regression_threshold must be a finite nonnegative number: {path}")
    if not isinstance(contract.get("disagreement_rule"), str) or not contract["disagreement_rule"].strip():
        fail(f"decision contract disagreement_rule must be a nonempty string: {path}")
    return contract


def read_tsv(path: Path, header: list[str], *, allow_empty: bool = False) -> list[dict[str, str]]:
    if not path.is_file():
        fail(f"missing TSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != header:
            fail(f"invalid header in {path}: expected {header}, got {reader.fieldnames}")
        rows = list(reader)
    if not rows and not allow_empty:
        fail(f"no data rows in {path}")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        fail(f"row has the wrong number of columns in {path}")
    return rows


def positive_int(value: str, field: str, path: Path) -> int:
    try:
        parsed = int(value)
    except ValueError:
        fail(f"{field} is not an integer in {path}: {value}")
    if parsed < 1:
        fail(f"{field} must be positive in {path}: {value}")
    return parsed


def pair_key(row: dict[str, str], path: Path) -> tuple[str, str, str, int, str, str]:
    for field in MANIFEST_HEADER:
        value = row[field]
        if not value.strip():
            fail(f"blank {field} in {path}")
        if value != value.strip():
            fail(f"noncanonical whitespace in {field} in {path}: {value!r}")
    if row["split"] not in {"optimization", "validation"}:
        fail(f"invalid split in {path}: {row['split']}")
    for field in ("input_sha256", "criterion_sha256"):
        if len(row[field]) != 64 or any(character not in "0123456789abcdef" for character in row[field]):
            fail(f"invalid SHA-256 in {field} in {path}: {row[field]}")
    return (
        row["split"], row["input_id"], row["input_sha256"],
        positive_int(row["sample"], "sample", path), row["criterion"], row["criterion_sha256"],
    )


def verify_manifest_contract(rows: list[dict[str, str]], contract: dict[str, object]) -> None:
    inputs = contract["inputs"]
    criteria = contract["criteria"]
    assert isinstance(inputs, dict) and isinstance(criteria, dict)
    input_hashes: dict[str, str] = {}
    for input_id, definition in inputs.items():
        if not isinstance(definition, dict) or definition.get("split") not in {"optimization", "validation"} or len(definition) < 2:
            fail(f"decision contract input {input_id} must declare optimization or validation split")
        input_hashes[input_id] = payload_sha256(definition)
    criterion_hashes: dict[str, str] = {}
    mechanical_criteria = 0
    for criterion, definition in criteria.items():
        if not isinstance(definition, dict) or not isinstance(definition.get("applicable_inputs"), list):
            fail(f"decision contract criterion {criterion} must declare applicable_inputs")
        applicable = definition["applicable_inputs"]
        if not applicable or any(item not in inputs for item in applicable) or len(applicable) != len(set(applicable)):
            fail(f"decision contract criterion {criterion} has invalid applicable_inputs")
        for field in ("question", "pass", "fail", "applicability"):
            if not isinstance(definition.get(field), str) or not definition[field].strip():
                fail(f"decision contract criterion {criterion} requires nonempty {field}")
        verification = definition.get("verification")
        if (
            not isinstance(verification, (str, dict))
            or not verification
            or (isinstance(verification, str) and not verification.strip())
        ):
            fail(f"decision contract criterion {criterion} requires verification")
        criterion_type = definition.get("type")
        if criterion_type not in {"MECHANICAL", "LLM-JUDGED"}:
            fail(f"decision contract criterion {criterion} type must be MECHANICAL or LLM-JUDGED")
        if criterion_type == "MECHANICAL":
            mechanical_criteria += 1
        criterion_hashes[criterion] = payload_sha256(definition)
    if mechanical_criteria == 0:
        fail("decision contract requires at least one MECHANICAL criterion")
    for input_id in inputs:
        if not any(input_id in definition["applicable_inputs"] for definition in criteria.values()):
            fail(f"decision contract input has no applicable criterion: {input_id}")
    for row in rows:
        input_id = row["input_id"]
        criterion = row["criterion"]
        if input_id not in inputs:
            fail(f"manifest input is absent from decision contract: {input_id}")
        if criterion not in criteria:
            fail(f"manifest criterion is absent from decision contract: {criterion}")
        if row["input_sha256"] != input_hashes[input_id]:
            fail(f"manifest input commitment differs from decision contract: {input_id}")
        if row["criterion_sha256"] != criterion_hashes[criterion]:
            fail(f"manifest criterion commitment differs from decision contract: {criterion}")
    expected = {
        (
            definition["split"], input_id, input_hashes[input_id], sample,
            criterion, criterion_hashes[criterion],
        )
        for input_id, definition in inputs.items()
        for sample in range(1, int(contract["samples_per_input"]) + 1)
        for criterion, criterion_definition in criteria.items()
        if input_id in criterion_definition["applicable_inputs"]
    }
    actual = {pair_key(row, Path("pair-manifest.tsv")) for row in rows}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        fail(json.dumps({"manifest_contract_missing": missing, "manifest_contract_extra": extra}, sort_keys=True))


def check_manifest_commitment(path: Path, manifest_sha256: str) -> None:
    if not path.exists():
        fail(f"missing manifest commitment: {path}")
    committed = path.read_text(encoding="utf-8").strip()
    if committed != manifest_sha256:
        fail(
            f"manifest differs from frozen commitment in {path}: "
            f"expected {committed}, got {manifest_sha256}"
        )


def create_manifest_commitment(path: Path, manifest_sha256: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(manifest_sha256 + "\n")
    except FileExistsError:
        check_manifest_commitment(path, manifest_sha256)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-commitment", required=True, type=Path)
    parser.add_argument("--decision-contract", required=True, type=Path)
    parser.add_argument("--decision-contract-commitment", required=True, type=Path)
    parser.add_argument("--commit-manifest", action="store_true")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--resample-ledger", type=Path)
    parser.add_argument("--experiment", type=int)
    args = parser.parse_args()

    contract = load_decision_contract(args.decision_contract)
    decision_contract_sha256 = sha256(args.decision_contract)
    manifest_rows = read_tsv(args.manifest, MANIFEST_HEADER)
    manifest_sha256 = sha256(args.manifest)
    manifest_keys = [pair_key(row, args.manifest) for row in manifest_rows]
    verify_manifest_contract(manifest_rows, contract)
    if len(set(manifest_keys)) != len(manifest_keys):
        fail("duplicate pair key in manifest")
    expected = set(manifest_keys)
    if args.commit_manifest:
        if args.ledger or args.resample_ledger or args.experiment is not None:
            fail("--commit-manifest cannot be combined with ledger validation")
        create_manifest_commitment(args.decision_contract_commitment, decision_contract_sha256)
        create_manifest_commitment(args.manifest_commitment, manifest_sha256)
        print(json.dumps({
            "decision_contract_sha256": decision_contract_sha256,
            "manifest_sha256": manifest_sha256,
            "rows": len(manifest_rows),
            "status": "COMMITTED",
        }, sort_keys=True))
        return
    if args.ledger is None or args.resample_ledger is None or args.experiment is None:
        fail("validation requires --ledger, --resample-ledger, and --experiment")
    if args.experiment < 1:
        fail("experiment must be a positive integer")
    check_manifest_commitment(args.decision_contract_commitment, decision_contract_sha256)
    check_manifest_commitment(args.manifest_commitment, manifest_sha256)

    by_experiment: dict[int, list[dict[str, str]]] = {}
    seen: set[tuple[int, str, str, str, int, str, str]] = set()
    for row in read_tsv(args.ledger, LEDGER_HEADER):
        experiment = positive_int(row["experiment"], "experiment", args.ledger)
        pair = pair_key(row, args.ledger)
        if row["verdict"] not in VERDICTS:
            fail(f"invalid verdict in {args.ledger}: {row['verdict']}")
        if not row["evidence"].strip():
            fail(f"blank evidence in {args.ledger}")
        key = (experiment, *pair)
        if key in seen:
            fail(f"duplicate ledger key: {key}")
        seen.add(key)
        by_experiment.setdefault(experiment, []).append(row)

    expected_experiments = set(range(1, args.experiment + 1))
    if set(by_experiment) != expected_experiments:
        fail(f"ledger experiments {sorted(by_experiment)} do not equal expected cumulative experiments {sorted(expected_experiments)}")

    for experiment, rows in sorted(by_experiment.items()):
        actual = {pair_key(row, args.ledger) for row in rows}
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra or len(rows) != len(manifest_rows):
            fail(json.dumps({
                "experiment": experiment,
                "missing": missing,
                "extra": extra,
                "expected_rows": len(manifest_rows),
                "actual_rows": len(rows),
            }, sort_keys=True))

    resample_rows = read_tsv(args.resample_ledger, RESAMPLE_HEADER, allow_empty=True)
    seen_resamples: set[tuple[int, int, str, str, str, int, str, str]] = set()
    resample_batches: set[tuple[int, int]] = set()
    resample_pairs: dict[tuple[int, int], set[tuple[str, str, str, int, str, str]]] = {}
    for row in resample_rows:
        experiment = positive_int(row["experiment"], "experiment", args.resample_ledger)
        batch = positive_int(row["resample_batch"], "resample_batch", args.resample_ledger)
        if experiment > args.experiment:
            fail(f"resample ledger contains future experiment {experiment}")
        pair = pair_key(row, args.resample_ledger)
        if pair not in expected:
            fail(f"resample row is not in the frozen manifest: {pair}")
        if row["verdict"] not in VERDICTS:
            fail(f"invalid verdict in {args.resample_ledger}: {row['verdict']}")
        if not row["evidence"].strip():
            fail(f"blank evidence in {args.resample_ledger}")
        key = (experiment, batch, *pair)
        if key in seen_resamples:
            fail(f"duplicate resample ledger key: {key}")
        seen_resamples.add(key)
        resample_batches.add((experiment, batch))
        resample_pairs.setdefault((experiment, batch), set()).add(pair)

    resample_cap = int(contract["allowed_resample_count"])
    for experiment in sorted({experiment for experiment, _ in resample_batches}):
        batches = sorted(batch for candidate, batch in resample_batches if candidate == experiment)
        expected_batches = list(range(1, len(batches) + 1))
        if batches != expected_batches:
            fail(f"resample batches for experiment {experiment} must be contiguous from 1: {batches}")
        if len(batches) > resample_cap:
            fail(
                f"resample batches for experiment {experiment} exceed decision-contract cap "
                f"{resample_cap}: {batches}"
            )
    for batch_key, actual_pairs in sorted(resample_pairs.items()):
        groups = {(pair[0], pair[1], pair[2], pair[4], pair[5]) for pair in actual_pairs}
        required_pairs = {
            pair for pair in expected
            if (pair[0], pair[1], pair[2], pair[4], pair[5]) in groups
        }
        if actual_pairs != required_pairs:
            fail(json.dumps({
                "incomplete_resample_batch": list(batch_key),
                "missing": sorted(required_pairs - actual_pairs),
            }, sort_keys=True))

    selected = by_experiment[args.experiment]
    verdicts = Counter(row["verdict"] for row in selected)
    print(json.dumps({
        "decision_contract_sha256": decision_contract_sha256,
        "experiment": args.experiment,
        "ledger_sha256": sha256(args.ledger),
        "manifest_sha256": manifest_sha256,
        "resample_batches": [f"{experiment}:{batch}" for experiment, batch in sorted(resample_batches)],
        "resample_ledger_sha256": sha256(args.resample_ledger),
        "resample_rows": len(resample_rows),
        "rows": len(selected),
        "resample_cap": resample_cap,
        "status": "EVIDENCE_VALID",
        "validated_experiments": sorted(by_experiment),
        "verdicts": {verdict: verdicts[verdict] for verdict in sorted(VERDICTS)},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
