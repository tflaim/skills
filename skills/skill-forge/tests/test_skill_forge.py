from __future__ import annotations

import argparse
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skill_forge.py"
SPEC = importlib.util.spec_from_file_location("skill_forge", SCRIPT)
assert SPEC and SPEC.loader
forge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = forge
SPEC.loader.exec_module(forge)


class SkillForgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.stdout = sys.stdout
        sys.stdout = io.StringIO()

    def tearDown(self) -> None:
        sys.stdout = self.stdout
        self.temp.cleanup()

    def write_json(self, name: str, payload: object) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def make_run(self, mode: str = "quality", validation_tag: str = "routing") -> tuple[Path, Path, dict]:
        skill = self.root / "SKILL.md"
        skill.write_text("---\nname: sample\ndescription: sample skill\n---\n\nOld rule is deliberately long.\n", encoding="utf-8")
        rows = [
            {"id": "train-a", "prompt": "train a", "tags": ["routing"], "split": "train"},
            {"id": "train-b", "prompt": "train b", "tags": ["format"], "split": "train"},
            {"id": "validation-a", "prompt": "validation a", "tags": [validation_tag], "split": "validation"},
            {"id": "validation-b", "prompt": "validation b", "tags": ["format"], "split": "validation"},
        ]
        cases = self.root / f"cases-{mode}.jsonl"
        cases.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        commitments = self.root / f"test-commitments-{mode}.jsonl"
        commitment_rows = [
            {"id": "test-a", "commitment_sha256": "a" * 64},
            {"id": "test-b", "commitment_sha256": "b" * 64},
        ]
        commitments.write_text(
            "".join(json.dumps(row) + "\n" for row in commitment_rows),
            encoding="utf-8",
        )
        run = self.root / f"run-{mode}"
        args = argparse.Namespace(
            skill=str(skill),
            cases=str(cases),
            test_commitments=str(commitments),
            run_dir=str(run),
            mode=mode,
            run_id=f"{mode}-run",
            validation_pct=20,
            max_edits=4,
            max_edit_chars=2000,
            max_total_changed_chars=4000,
        )
        self.assertEqual(forge.command_init_run(args), 0)
        manifest = forge.load_json(run / "manifest.json")
        return skill, run, manifest

    def score(
        self,
        manifest: dict,
        split: str,
        values: list[float],
        maxima: list[float] | None = None,
        failures: list[int] | None = None,
        skill_sha256: str | None = None,
        evaluator_sha256: str = "c" * 64,
    ) -> dict:
        ids = manifest["split_case_ids"][split]
        maxima = maxima or [5.0] * len(ids)
        failures = failures or [0] * len(ids)
        cases = [
            {"id": case_id, "score": value, "max_score": maximum, "mandatory_failures": failure}
            for case_id, value, maximum, failure in zip(ids, values, maxima, failures)
        ]
        if split == "test":
            for case in cases:
                case["commitment_sha256"] = manifest["test_commitments"][case["id"]]
        return {
            "schema_version": forge.SCORE_SCHEMA,
            "run_id": manifest["run_id"],
            "manifest_sha256": manifest["manifest_sha256"],
            "skill_sha256": skill_sha256 or manifest["skill_sha256"],
            "evaluator_sha256": evaluator_sha256,
            "split": split,
            "score": sum(values),
            "max_score": sum(maxima),
            "mandatory_failures": sum(failures),
            "cases": cases,
        }

    def make_candidate(self, skill: Path, run: Path, replacement: str = "New rule.") -> tuple[Path, Path]:
        edits = self.write_json(
            f"{run.name}-edits.json",
            {
                "base_sha256": forge.file_hash(skill),
                "edits": [
                    {
                        "op": "replace",
                        "target": "Old rule is deliberately long.",
                        "replacement": replacement,
                    }
                ],
            },
        )
        candidate = run / "candidates" / "candidate.SKILL.md"
        args = argparse.Namespace(
            skill=str(skill),
            edits=str(edits),
            out=str(candidate),
            run_dir=str(run),
            allow_frontmatter_edits=False,
        )
        self.assertEqual(forge.command_apply_edits(args), 0)
        return candidate, Path(str(candidate) + ".receipt.json")

    def evidence(
        self,
        run: Path,
        manifest: dict,
        candidate: Path,
        candidate_values: list[float] | None = None,
        candidate_failures: list[int] | None = None,
    ) -> dict[str, Path]:
        train = self.write_json(f"{run.name}-train.json", self.score(manifest, "train", [3, 5]))
        candidate_train = self.write_json(
            f"{run.name}-candidate-train.json",
            self.score(
                manifest,
                "train",
                candidate_values or [5, 5],
                failures=candidate_failures,
                skill_sha256=forge.file_hash(candidate),
            ),
        )
        adequacy = run / "validation-adequacy.json"
        self.assertEqual(
            forge.command_check_validation(argparse.Namespace(run_dir=str(run), train_score=str(train), out=str(adequacy))),
            0,
        )
        return {"train": train, "candidate_train": candidate_train, "adequacy": adequacy}

    def decide(
        self,
        *,
        mode: str,
        current_values: list[float],
        candidate_values: list[float],
        test_values: tuple[list[float], list[float]] | None = None,
        candidate_failures: list[int] | None = None,
        candidate_train_values: list[float] | None = None,
        candidate_train_failures: list[int] | None = None,
        candidate_score_sha256: str | None = None,
        candidate_evaluator_sha256: str = "c" * 64,
    ) -> dict:
        skill, run, manifest = self.make_run(mode)
        candidate, receipt = self.make_candidate(skill, run, "Short." if mode == "compression" else "New rule.")
        candidate_sha256 = forge.file_hash(candidate)
        evidence = self.evidence(
            run,
            manifest,
            candidate,
            candidate_values=candidate_train_values,
            candidate_failures=candidate_train_failures,
        )
        current = self.write_json(f"{mode}-current.json", self.score(manifest, "validation", current_values))
        candidate_score = self.write_json(
            f"{mode}-candidate.json",
            self.score(
                manifest,
                "validation",
                candidate_values,
                failures=candidate_failures,
                skill_sha256=candidate_score_sha256 or candidate_sha256,
                evaluator_sha256=candidate_evaluator_sha256,
            ),
        )
        test_current = test_candidate = None
        if test_values:
            test_current = self.write_json(f"{mode}-test-current.json", self.score(manifest, "test", test_values[0]))
            test_candidate = self.write_json(
                f"{mode}-test-candidate.json",
                self.score(manifest, "test", test_values[1], skill_sha256=candidate_sha256),
            )
        common = dict(
            mode=mode, run_dir=str(run), current=str(current), candidate=str(candidate_score),
            current_skill=str(skill), candidate_skill=str(candidate), candidate_receipt=str(receipt),
            validation_adequacy=str(evidence["adequacy"]), train_score=str(evidence["train"]),
            candidate_train_score=str(evidence["candidate_train"]),
        )
        out = run / "decisions" / "forge.json"
        if test_values:
            accepted = run / "decisions" / "accepted.json"
            forge.command_decide(argparse.Namespace(
                **common, test_current=None, test_candidate=None, accepted_decision=None, out=str(accepted),
            ))
            forge.command_decide(argparse.Namespace(
                **common, test_current=str(test_current), test_candidate=str(test_candidate),
                accepted_decision=str(accepted), out=str(out),
            ))
        else:
            forge.command_decide(argparse.Namespace(
                **common, test_current=None, test_candidate=None, accepted_decision=None, out=str(out),
            ))
        return forge.load_json(out)

    def test_quality_validation_lift_is_accepted(self) -> None:
        self.assertEqual(self.decide(mode="quality", current_values=[4, 4], candidate_values=[5, 4])["status"], "Accepted")

    def test_candidate_train_regression_on_original_failure_is_rejected(self) -> None:
        with self.assertRaisesRegex(forge.SkillForgeError, "regressed on original train failures"):
            self.decide(
                mode="quality",
                current_values=[4, 4],
                candidate_values=[5, 4],
                candidate_train_values=[2, 5],
            )

    def test_candidate_train_mandatory_failure_is_rejected(self) -> None:
        with self.assertRaisesRegex(forge.SkillForgeError, "train evidence has mandatory failures"):
            self.decide(
                mode="quality",
                current_values=[4, 4],
                candidate_values=[5, 4],
                candidate_train_failures=[1, 0],
            )

    def test_stale_candidate_score_is_rejected(self) -> None:
        with self.assertRaisesRegex(forge.SkillForgeError, "expected skill"):
            self.decide(
                mode="quality",
                current_values=[4, 4],
                candidate_values=[5, 4],
                candidate_score_sha256="d" * 64,
            )

    def test_changed_candidate_evaluator_is_rejected(self) -> None:
        with self.assertRaisesRegex(forge.SkillForgeError, "evaluators do not match"):
            self.decide(
                mode="quality",
                current_values=[4, 4],
                candidate_values=[5, 4],
                candidate_evaluator_sha256="d" * 64,
            )

    def test_locked_test_bodies_are_not_written_to_run(self) -> None:
        _, run, _ = self.make_run()

        self.assertFalse((run / "cases" / "test.jsonl").exists())
        rows = list(forge.iter_jsonl(run / "cases" / "test-commitments.jsonl"))
        self.assertEqual([row["id"] for row in rows], ["test-a", "test-b"])
        self.assertTrue(all("prompt" not in row for row in rows))

    def test_locked_score_with_mismatched_commitment_is_rejected(self) -> None:
        _, _, manifest = self.make_run()
        payload = self.score(manifest, "test", [4, 4])
        payload["cases"][0]["commitment_sha256"] = "d" * 64

        with self.assertRaisesRegex(forge.SkillForgeError, "commitment does not match"):
            forge.parse_score(payload, manifest, "test", manifest["skill_sha256"])

    def test_quality_lift_and_locked_hold_is_promoted(self) -> None:
        decision = self.decide(
            mode="quality",
            current_values=[4, 4],
            candidate_values=[5, 4],
            test_values=([4, 4], [4, 4]),
        )
        self.assertEqual(decision["status"], "Promoted")
        self.assertIsNotNone(decision["current_train_sha256"])
        self.assertIsNotNone(decision["candidate_train_sha256"])
        self.assertIsNotNone(decision["current_test_sha256"])
        self.assertIsNotNone(decision["candidate_test_sha256"])
        self.assertIsNotNone(decision["accepted_decision_sha256"])

    def test_locked_stage_rejects_substituted_accepted_candidate(self) -> None:
        decision = self.decide(mode="quality", current_values=[4, 4], candidate_values=[5, 4])
        expected_fields = {
            field: decision[field]
            for field in (
                "current_skill_sha256", "candidate_skill_sha256",
                "current_validation_sha256", "candidate_validation_sha256",
                "current_train_sha256", "candidate_train_sha256",
                "validation_adequacy_sha256", "candidate_receipt_sha256",
            )
        }
        substituted = dict(decision)
        substituted["candidate_skill_sha256"] = "e" * 64
        substituted.pop("decision_sha256")
        substituted["decision_sha256"] = forge.payload_hash(substituted)

        with self.assertRaisesRegex(forge.SkillForgeError, "does not match candidate_skill_sha256"):
            forge.validate_accepted_decision(
                substituted,
                {"run_id": decision["run_id"], "manifest_sha256": decision["manifest_sha256"]},
                "quality",
                expected_fields,
            )

    def test_train_only_lift_is_found(self) -> None:
        self.assertEqual(self.decide(mode="quality", current_values=[4, 4], candidate_values=[4, 4])["status"], "Found")

    def test_validation_regression_is_rejected(self) -> None:
        self.assertEqual(self.decide(mode="quality", current_values=[5, 5], candidate_values=[4, 5])["status"], "Rejected")

    def test_compression_tie_and_shrink_is_compressed(self) -> None:
        self.assertEqual(self.decide(mode="compression", current_values=[4, 4], candidate_values=[4, 4])["status"], "Compressed")

    def test_exploratory_train_lift_is_found(self) -> None:
        self.assertEqual(self.decide(mode="exploratory", current_values=[4, 4], candidate_values=[4, 4])["status"], "Found")

    def test_locked_regression_remains_accepted_not_promoted(self) -> None:
        decision = self.decide(
            mode="quality",
            current_values=[4, 4],
            candidate_values=[5, 4],
            test_values=([5, 5], [4, 5]),
        )
        self.assertEqual(decision["status"], "Accepted")

    def test_locked_mandatory_failure_blocks_promotion(self) -> None:
        skill, run, manifest = self.make_run("quality")
        candidate, receipt = self.make_candidate(skill, run)
        candidate_sha256 = forge.file_hash(candidate)
        evidence = self.evidence(run, manifest, candidate)
        current = self.write_json("locked-failure-current.json", self.score(manifest, "validation", [4, 4]))
        candidate_score = self.write_json(
            "locked-failure-candidate.json",
            self.score(manifest, "validation", [5, 4], skill_sha256=candidate_sha256),
        )
        test_current = self.write_json("locked-failure-test-current.json", self.score(manifest, "test", [4, 4]))
        test_candidate = self.write_json(
            "locked-failure-test-candidate.json",
            self.score(
                manifest,
                "test",
                [5, 4],
                failures=[1, 0],
                skill_sha256=candidate_sha256,
            ),
        )
        common = dict(
            mode="quality", run_dir=str(run), current=str(current), candidate=str(candidate_score),
            current_skill=str(skill), candidate_skill=str(candidate), candidate_receipt=str(receipt),
            validation_adequacy=str(evidence["adequacy"]), train_score=str(evidence["train"]),
            candidate_train_score=str(evidence["candidate_train"]),
        )
        accepted = run / "decisions" / "accepted.json"
        forge.command_decide(argparse.Namespace(
            **common, test_current=None, test_candidate=None, accepted_decision=None, out=str(accepted),
        ))
        out = run / "decisions" / "forge.json"
        forge.command_decide(argparse.Namespace(
            **common, test_current=str(test_current), test_candidate=str(test_candidate),
            accepted_decision=str(accepted), out=str(out),
        ))
        decision = forge.load_json(out)
        self.assertEqual(decision["status"], "Accepted")
        self.assertIn("mandatory failures", decision["reason"])

    def test_infrastructure_failure_invalidates_comparison(self) -> None:
        _, _, manifest = self.make_run()
        current_payload = self.score(manifest, "validation", [4, 4])
        candidate_payload = self.score(manifest, "validation", [5, 4])
        candidate_payload["cases"][0]["infrastructure_failures"] = 1
        candidate_payload["infrastructure_failures"] = 1
        current = forge.parse_score(current_payload, manifest, "validation", manifest["skill_sha256"])
        candidate = forge.parse_score(candidate_payload, manifest, "validation", manifest["skill_sha256"])
        with self.assertRaisesRegex(forge.SkillForgeError, "infrastructure failures"):
            forge.validate_comparable(current, candidate)

    def test_candidate_mandatory_failure_is_rejected(self) -> None:
        decision = self.decide(
            mode="quality",
            current_values=[4, 4],
            candidate_values=[5, 4],
            candidate_failures=[1, 0],
        )
        self.assertEqual(decision["status"], "Rejected")

    def test_unequal_score_denominators_are_rejected(self) -> None:
        _, run, manifest = self.make_run()
        current = forge.parse_score(
            self.score(manifest, "validation", [4, 4]),
            manifest,
            "validation",
            manifest["skill_sha256"],
        )
        candidate = forge.parse_score(
            self.score(manifest, "validation", [4, 4], maxima=[6, 5]),
            manifest,
            "validation",
            manifest["skill_sha256"],
        )
        with self.assertRaisesRegex(forge.SkillForgeError, "maximums"):
            forge.validate_comparable(current, candidate)

    def test_duplicate_case_ids_are_rejected(self) -> None:
        rows = [
            {"id": "same", "prompt": "a", "split": "train"},
            {"id": "same", "prompt": "b", "split": "validation"},
        ]
        with self.assertRaisesRegex(forge.SkillForgeError, "duplicate case id"):
            forge.normalize_cases(rows, "run", 20)

    def test_validation_coverage_gap_is_reported(self) -> None:
        _, run, manifest = self.make_run(validation_tag="other")
        train = self.score(manifest, "train", [3, 5])
        result = forge.check_validation_adequacy(train, run, manifest)
        self.assertFalse(result["adequate"])
        self.assertEqual(result["missing_tags"], ["routing"])

    def test_failed_train_case_without_tags_is_rejected(self) -> None:
        _, run, manifest = self.make_run()
        train_path = run / "cases" / "train.jsonl"
        rows = list(forge.iter_jsonl(train_path))
        rows[0]["tags"] = []
        forge.write_jsonl(train_path, rows)
        manifest["split_sha256"]["train"] = forge.payload_hash(rows)
        bare = dict(manifest)
        bare.pop("manifest_sha256")
        manifest["manifest_sha256"] = forge.payload_hash(bare)
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(forge.SkillForgeError, "require tags"):
            forge.check_validation_adequacy(self.score(manifest, "train", [3, 5]), run, manifest)

    def test_duplicate_patch_targets_are_rejected(self) -> None:
        skill, run, _ = self.make_run()
        edits = self.write_json(
            "duplicate-edits.json",
            {
                "base_sha256": forge.file_hash(skill),
                "edits": [
                    {"op": "replace", "target": "Old rule is deliberately long.", "replacement": "One."},
                    {"op": "replace", "target": "Old rule is deliberately long.", "replacement": "Two."},
                ],
            },
        )
        with self.assertRaisesRegex(forge.SkillForgeError, "targets must be unique"):
            forge.command_apply_edits(
                argparse.Namespace(
                    skill=str(skill),
                    edits=str(edits),
                    out=str(run / "candidate.md"),
                    run_dir=str(run),
                    allow_frontmatter_edits=False,
                )
            )

    def test_nonunique_patch_target_is_rejected(self) -> None:
        skill, run, _ = self.make_run()
        text = skill.read_text(encoding="utf-8")
        skill.write_text(text + "Old rule is deliberately long.\n", encoding="utf-8")
        manifest = forge.load_json(run / "manifest.json")
        manifest["skill_sha256"] = forge.file_hash(skill)
        bare = dict(manifest)
        bare.pop("manifest_sha256")
        manifest["manifest_sha256"] = forge.payload_hash(bare)
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        edits = self.write_json(
            "nonunique-edits.json",
            {
                "base_sha256": forge.file_hash(skill),
                "edits": [{"op": "replace", "target": "Old rule is deliberately long.", "replacement": "One."}],
            },
        )
        with self.assertRaisesRegex(forge.SkillForgeError, "exactly once"):
            forge.command_apply_edits(
                argparse.Namespace(
                    skill=str(skill),
                    edits=str(edits),
                    out=str(run / "candidate.md"),
                    run_dir=str(run),
                    allow_frontmatter_edits=False,
                )
            )

    def test_exact_patch_preserves_trailing_newline(self) -> None:
        skill, run, _ = self.make_run()
        source = skill.read_text(encoding="utf-8")
        replacement = source.replace("Old rule is deliberately long.", "New rule.")
        edits = self.write_json(
            "whole-file-edits.json",
            {
                "base_sha256": forge.file_hash(skill),
                "edits": [{"op": "replace", "target": source, "replacement": replacement}],
            },
        )
        candidate = run / "whole-file-candidate.md"
        forge.command_apply_edits(
            argparse.Namespace(
                skill=str(skill),
                edits=str(edits),
                out=str(candidate),
                run_dir=str(run),
                allow_frontmatter_edits=True,
            )
        )
        self.assertEqual(candidate.read_text(encoding="utf-8"), replacement)
        self.assertTrue(candidate.read_text(encoding="utf-8").endswith("\n"))

    def test_malformed_json_is_rejected(self) -> None:
        path = self.root / "bad.json"
        path.write_text('{"a":', encoding="utf-8")
        with self.assertRaisesRegex(forge.SkillForgeError, "cannot read JSON"):
            forge.load_json(path)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        path = self.root / "duplicate.json"
        path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
        with self.assertRaisesRegex(forge.SkillForgeError, "duplicate JSON key"):
            forge.load_json(path)


if __name__ == "__main__":
    unittest.main()
