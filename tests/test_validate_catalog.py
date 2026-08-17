from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_catalog import (
    ValidationError,
    parse_frontmatter,
    parse_openai_implicit_invocation,
    validate_openai_invocation,
)


class OpenAIInvocationPolicyTests(unittest.TestCase):
    def parse(self, policy: str) -> bool | None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "openai.yaml"
            path.write_text(
                'interface:\n  display_name: "Example"\n' + policy,
                encoding="utf-8",
            )
            return parse_openai_implicit_invocation(path)

    def test_accepts_explicit_false(self) -> None:
        self.assertFalse(self.parse("policy:\n  allow_implicit_invocation: false\n"))

    def test_accepts_absent_policy(self) -> None:
        self.assertIsNone(self.parse(""))

    def test_rejects_contradictory_duplicate_values(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "policy:\n"
                "  allow_implicit_invocation: false\n"
                "  allow_implicit_invocation: true\n"
            )

    def test_rejects_spaced_duplicate_value(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "policy:\n"
                "  allow_implicit_invocation: false\n"
                "  allow_implicit_invocation : true\n"
            )

    def test_rejects_duplicate_policy_blocks(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "policy:\n"
                "  allow_implicit_invocation: false\n"
                "policy:\n"
                "  allow_implicit_invocation: true\n"
            )

    def test_rejects_policy_without_invocation_value(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse("policy:\n  future_setting: true\n")

    def test_rejects_comment_on_policy_key(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "policy: # documented policy\n"
                "  allow_implicit_invocation: false\n"
            )

    def test_rejects_commented_duplicate_policy_key(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "policy:\n"
                "  allow_implicit_invocation: false\n"
                "policy: # override\n"
                "  allow_implicit_invocation: true\n"
            )

    def test_rejects_false_for_model_invoked_skill(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "openai.yaml"
            path.write_text(
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                validate_openai_invocation("pr-preflight", path)

    def test_rejects_true_for_user_invoked_skill(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "openai.yaml"
            path.write_text(
                "policy:\n  allow_implicit_invocation: true\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError):
                validate_openai_invocation("baton", path)


class FrontmatterTests(unittest.TestCase):
    def parse(self, metadata: str) -> dict[str, str]:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "SKILL.md"
            path.write_text(f"---\n{metadata}---\n# Skill\n", encoding="utf-8")
            return parse_frontmatter(path)

    def test_accepts_canonical_disable_model_invocation(self) -> None:
        fields = self.parse(
            "name: example\n"
            "description: Example skill\n"
            "disable-model-invocation: true\n"
        )
        self.assertEqual(fields["disable-model-invocation"], "true")

    def test_rejects_spaced_disable_model_invocation_key(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "name: example\n"
                "description: Example skill\n"
                "disable-model-invocation : true\n"
            )

    def test_rejects_duplicate_disable_model_invocation_key(self) -> None:
        with self.assertRaises(ValidationError):
            self.parse(
                "name: example\n"
                "description: Example skill\n"
                "disable-model-invocation: false\n"
                "disable-model-invocation: true\n"
            )


if __name__ == "__main__":
    unittest.main()
