from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_pair_ledger.py"
MANIFEST_HEADER = "split\tinput_id\tsample\tcriterion\n"
LEDGER_HEADER = "experiment\tsplit\tinput_id\tsample\tcriterion\tverdict\tevidence\n"


class PairLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = self.root / "pair-manifest.tsv"
        self.commitment = self.root / "pair-manifest.sha256"
        self.ledger = self.root / "pair-ledger.tsv"

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
        ]
        if commit:
            command.append("--commit-manifest")
        else:
            command.extend(["--ledger", str(self.ledger), "--experiment", str(experiment)])
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_single_pair(self, input_id: str = "case-1", experiment: int = 1) -> None:
        self.manifest.write_text(
            MANIFEST_HEADER + f"optimization\t{input_id}\t1\tquality\n",
            encoding="utf-8",
        )
        rows = [
            f"{number}\toptimization\t{input_id}\t1\tquality\tSAME\tmatched\n"
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
        self.assertIn("differs from frozen commitment", result.stderr)

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


if __name__ == "__main__":
    unittest.main()
