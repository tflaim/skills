from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_pair_ledger.py"
MANIFEST_HEADER = "split\tinput_id\tinput_sha256\tsample\tcriterion\tcriterion_sha256\n"
LEDGER_HEADER = "experiment\tsplit\tinput_id\tinput_sha256\tsample\tcriterion\tcriterion_sha256\tverdict\tevidence\n"
RESAMPLE_HEADER = "experiment\tresample_batch\tsplit\tinput_id\tinput_sha256\tsample\tcriterion\tcriterion_sha256\tverdict\tevidence\n"


def payload_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PairLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = self.root / "pair-manifest.tsv"
        self.commitment = self.root / "pair-manifest.sha256"
        self.contract = self.root / "decision-contract.json"
        self.contract_commitment = self.root / "decision-contract.sha256"
        self.ledger = self.root / "pair-ledger.tsv"
        self.resample_ledger = self.root / "resample-ledger.tsv"
        self.resample_ledger.write_text(RESAMPLE_HEADER, encoding="utf-8")
        self.input_bodies = {
            "case-1": {"split": "optimization", "prompt": "case prompt"},
            "case-2": {"split": "optimization", "prompt": "other prompt"},
        }
        self.criterion_body = {
            "question": "Did it work?", "pass": "yes", "fail": "no",
            "applicability": "all cases", "verification": "inspect output",
            "applicable_inputs": ["case-1"],
        }
        self.write_contract()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_validator(self, experiment: int | None = None, *, commit: bool = False) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(self.manifest),
            "--manifest-commitment",
            str(self.commitment),
            "--decision-contract",
            str(self.contract),
            "--decision-contract-commitment",
            str(self.contract_commitment),
        ]
        if commit:
            command.append("--commit-manifest")
        else:
            command.extend([
                "--ledger",
                str(self.ledger),
                "--resample-ledger",
                str(self.resample_ledger),
                "--experiment",
                str(experiment),
            ])
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_contract(self, *, resample_cap: int = 1, input_ids: tuple[str, ...] = ("case-1",)) -> None:
        self.criterion_body["applicable_inputs"] = list(input_ids)
        self.contract.write_text(json.dumps({
            "allowed_resample_count": resample_cap,
            "samples_per_input": 1,
            "inputs": {input_id: self.input_bodies[input_id] for input_id in input_ids},
            "criteria": {"quality": self.criterion_body},
        }), encoding="utf-8")

    def pair_fields(self, input_id: str = "case-1") -> str:
        input_body = self.input_bodies[input_id.strip()]
        return (
            f"{input_body['split']}\t{input_id}\t{payload_sha256(input_body)}\t1\tquality\t"
            f"{payload_sha256(self.criterion_body)}"
        )

    def write_single_pair(self, input_id: str = "case-1", experiment: int = 1) -> None:
        self.manifest.write_text(
            MANIFEST_HEADER + self.pair_fields(input_id) + "\n",
            encoding="utf-8",
        )
        rows = [
            f"{number}\t{self.pair_fields(input_id)}\tSAME\tmatched\n"
            for number in range(1, experiment + 1)
        ]
        self.ledger.write_text(LEDGER_HEADER + "".join(rows), encoding="utf-8")

    def test_rejects_manifest_change_after_first_experiment(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.assertEqual(self.run_validator(1).returncode, 0)

        self.write_single_pair(input_id="case-2", experiment=2)
        result = self.run_validator(2)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest input is absent from decision contract", result.stderr)

    def test_rejects_manifest_omitting_declared_input(self) -> None:
        self.write_contract(input_ids=("case-1", "case-2"))
        self.write_single_pair()

        result = self.run_validator(commit=True)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest_contract_missing", result.stderr)

    def test_accepts_same_manifest_for_cumulative_experiment(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.assertEqual(self.run_validator(1).returncode, 0)

        self.write_single_pair(experiment=2)
        result = self.run_validator(2)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_missing_commitment(self) -> None:
        self.write_single_pair()

        result = self.run_validator(1)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing manifest commitment", result.stderr)

    def test_rejects_whitespace_variant_key(self) -> None:
        self.write_single_pair(input_id=" case-1 ")

        result = self.run_validator(commit=True)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("noncanonical whitespace", result.stderr)
        self.assertFalse(self.commitment.exists())

    def test_accepts_declared_resample_batch(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.resample_ledger.write_text(
            RESAMPLE_HEADER + f"1\t1\t{self.pair_fields()}\tBETTER\trepeated evidence\n",
            encoding="utf-8",
        )

        result = self.run_validator(1)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"resample_batches": ["1:1"]', result.stdout)
        self.assertIn('"status": "EVIDENCE_VALID"', result.stdout)

    def test_rejects_resample_batch_over_contract_cap(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.resample_ledger.write_text(
            RESAMPLE_HEADER + f"1\t1\t{self.pair_fields()}\tSAME\tfirst\n"
            + f"1\t2\t{self.pair_fields()}\tBETTER\tsecond\n",
            encoding="utf-8",
        )

        result = self.run_validator(1)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exceed decision-contract cap", result.stderr)

    def test_rejects_noncontiguous_resample_batches(self) -> None:
        self.write_contract(resample_cap=2)
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.resample_ledger.write_text(
            RESAMPLE_HEADER + f"1\t2\t{self.pair_fields()}\tBETTER\tskipped batch\n",
            encoding="utf-8",
        )

        result = self.run_validator(1)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be contiguous from 1", result.stderr)

    def test_rejects_changed_rubric_content(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.criterion_body["pass"] = "changed after baseline"
        self.write_contract()

        result = self.run_validator(1)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("criterion commitment differs", result.stderr)

    def test_rejects_changed_nonrubric_contract_term(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.write_contract(resample_cap=99)

        result = self.run_validator(1)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("decision-contract.sha256", result.stderr)
        self.assertIn("differs from frozen commitment", result.stderr)

    def test_rejects_missing_trailing_column_without_traceback(self) -> None:
        self.write_single_pair()
        self.assertEqual(self.run_validator(commit=True).returncode, 0)
        self.ledger.write_text(
            LEDGER_HEADER + f"1\t{self.pair_fields()}\tSAME\n",
            encoding="utf-8",
        )

        result = self.run_validator(1)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wrong number of columns", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
