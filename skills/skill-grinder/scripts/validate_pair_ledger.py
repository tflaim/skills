#!/usr/bin/env python3
"""Validate cumulative matched-pair evidence for a skill-grinder experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


MANIFEST_HEADER = ["split", "input_id", "sample", "criterion"]
LEDGER_HEADER = ["experiment", *MANIFEST_HEADER, "verdict", "evidence"]
VERDICTS = {"SAME", "BETTER", "WORSE"}


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path: Path, header: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        fail(f"missing TSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != header:
            fail(f"invalid header in {path}: expected {header}, got {reader.fieldnames}")
        rows = list(reader)
    if not rows:
        fail(f"no data rows in {path}")
    if any(None in row for row in rows):
        fail(f"row has extra columns in {path}")
    return rows


def positive_int(value: str, field: str, path: Path) -> int:
    try:
        parsed = int(value)
    except ValueError:
        fail(f"{field} is not an integer in {path}: {value}")
    if parsed < 1:
        fail(f"{field} must be positive in {path}: {value}")
    return parsed


def pair_key(row: dict[str, str], path: Path) -> tuple[str, str, int, str]:
    for field in MANIFEST_HEADER:
        value = row[field]
        if not value.strip():
            fail(f"blank {field} in {path}")
        if value != value.strip():
            fail(f"noncanonical whitespace in {field} in {path}: {value!r}")
    if row["split"] not in {"optimization", "validation"}:
        fail(f"invalid split in {path}: {row['split']}")
    return (row["split"], row["input_id"], positive_int(row["sample"], "sample", path), row["criterion"])


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
    parser.add_argument("--commit-manifest", action="store_true")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--experiment", type=int)
    args = parser.parse_args()

    manifest_rows = read_tsv(args.manifest, MANIFEST_HEADER)
    manifest_sha256 = sha256(args.manifest)
    manifest_keys = [pair_key(row, args.manifest) for row in manifest_rows]
    if len(set(manifest_keys)) != len(manifest_keys):
        fail("duplicate pair key in manifest")
    expected = set(manifest_keys)
    if args.commit_manifest:
        if args.ledger or args.experiment is not None:
            fail("--commit-manifest cannot be combined with --ledger or --experiment")
        create_manifest_commitment(args.manifest_commitment, manifest_sha256)
        print(json.dumps({
            "manifest_sha256": manifest_sha256,
            "rows": len(manifest_rows),
            "status": "COMMITTED",
        }, sort_keys=True))
        return
    if args.ledger is None or args.experiment is None:
        fail("validation requires --ledger and --experiment")
    if args.experiment < 1:
        fail("experiment must be a positive integer")
    check_manifest_commitment(args.manifest_commitment, manifest_sha256)

    by_experiment: dict[int, list[dict[str, str]]] = {}
    seen: set[tuple[int, str, str, int, str]] = set()
    for row in read_tsv(args.ledger, LEDGER_HEADER):
        experiment = positive_int(row["experiment"], "experiment", args.ledger)
        split, input_id, sample, criterion = pair_key(row, args.ledger)
        if row["verdict"] not in VERDICTS:
            fail(f"invalid verdict in {args.ledger}: {row['verdict']}")
        if not row["evidence"].strip():
            fail(f"blank evidence in {args.ledger}")
        key = (experiment, split, input_id, sample, criterion)
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

    selected = by_experiment[args.experiment]
    verdicts = Counter(row["verdict"] for row in selected)
    print(json.dumps({
        "experiment": args.experiment,
        "ledger_sha256": sha256(args.ledger),
        "manifest_sha256": manifest_sha256,
        "rows": len(selected),
        "status": "PASS",
        "validated_experiments": sorted(by_experiment),
        "verdicts": {verdict: verdicts[verdict] for verdict in sorted(VERDICTS)},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
