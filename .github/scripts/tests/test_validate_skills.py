"""Exercise catalog validation against small, real plugin trees."""
from contextlib import chdir, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "validate_skills.py"
REPO = SCRIPT.parents[2]
SPEC = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.claude = {"name": "sample", "plugins": [
            {"name": "example", "source": "./example", "version": "1.0.0"}]}
        self.codex = {"name": "sample", "plugins": [{
            "name": "example", "source": {"source": "local", "path": "./example"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity"}]}
        self.manifest = {"name": "example", "version": "1.0.0", "description": "Example skill"}
        self.write_json(".claude-plugin/marketplace.json", self.claude)
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.write_json("example/.claude-plugin/plugin.json", self.manifest)
        self.write_json("example/.codex-plugin/plugin.json", {
            **self.manifest, "skills": "./skills/", "interface": {"displayName": "Example"}})
        self.skill = self.root / "example/skills/example/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: example\ndescription: An example skill\n---\nDo the task.\n")

    def write_json(self, path: str, data: object) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data))

    def run_validator(self) -> SimpleNamespace:
        output = io.StringIO()
        with chdir(self.root), redirect_stdout(output):
            code = VALIDATOR.main()
        return SimpleNamespace(returncode=code, stdout=output.getvalue(), stderr="")

    def assert_invalid(self, message: str) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_accepts_matching_catalogs(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 skill(s)", result.stdout)

    def test_requires_codex_catalog(self) -> None:
        (self.root / ".agents/plugins/marketplace.json").unlink()
        self.assert_invalid("marketplace.json")

    def test_rejects_malformed_codex_json(self) -> None:
        (self.root / ".agents/plugins/marketplace.json").write_text("{")
        self.assert_invalid("invalid JSON")

    def test_rejects_non_object_catalog(self) -> None:
        self.write_json(".agents/plugins/marketplace.json", [])
        self.assert_invalid("object")

    def test_rejects_mismatched_catalog_names(self) -> None:
        self.codex["name"] = "different"
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.assert_invalid("marketplace names")

    def test_rejects_missing_catalog_entry(self) -> None:
        self.codex["plugins"] = []
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.assert_invalid("plugin sets")

    def test_rejects_duplicate_plugin(self) -> None:
        self.codex["plugins"] *= 2
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.assert_invalid("duplicate")

    def test_rejects_invalid_policy(self) -> None:
        self.codex["plugins"][0]["policy"]["installation"] = "sometimes"
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.assert_invalid("installation")

    def test_rejects_missing_source_directory(self) -> None:
        self.codex["plugins"][0]["source"]["path"] = "./missing"
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.assert_invalid("directory")

    def test_rejects_source_outside_repository(self) -> None:
        self.codex["plugins"][0]["source"]["path"] = "../outside"
        self.write_json(".agents/plugins/marketplace.json", self.codex)
        self.assert_invalid("inside")

    def test_requires_both_plugin_manifests(self) -> None:
        (self.root / "example/.codex-plugin/plugin.json").unlink()
        self.assert_invalid("plugin.json")

    def test_rejects_manifest_name_mismatch(self) -> None:
        self.manifest["name"] = "wrong"
        self.write_json("example/.claude-plugin/plugin.json", self.manifest)
        self.assert_invalid("name")

    def test_rejects_version_drift(self) -> None:
        self.manifest["version"] = "2.0.0"
        self.write_json("example/.claude-plugin/plugin.json", self.manifest)
        self.assert_invalid("version")

    def test_rejects_missing_skills(self) -> None:
        self.skill.unlink()
        self.assert_invalid("no skills")

    def test_rejects_skill_name_mismatch(self) -> None:
        self.skill.write_text("---\nname: wrong\ndescription: Example\n---\nBody\n")
        self.assert_invalid("directory name")

    def test_rejects_non_string_description(self) -> None:
        self.skill.write_text("---\nname: example\ndescription: 42\n---\nBody\n")
        self.assert_invalid("description")

    def test_rejects_silently_truncated_description(self) -> None:
        self.skill.write_text('---\nname: example\ndescription: Use for "issue #42"\n---\nBody\n')
        self.assert_invalid("quote")

    def test_accepts_hash_in_folded_description(self) -> None:
        self.skill.write_text('---\nname: example\ndescription: >-\n  Use for "issue #42"\n---\nBody\n')
        self.assertEqual(self.run_validator().returncode, 0)

    def test_rejects_missing_skill_in_directory(self) -> None:
        (self.root / "example/skills/unfinished").mkdir()
        self.assert_invalid("missing SKILL.md")

    def test_rejects_unlisted_plugin(self) -> None:
        self.write_json("extra/.claude-plugin/plugin.json", self.manifest)
        self.assert_invalid("missing or found outside")

    def test_rejects_skill_outside_registered_plugins(self) -> None:
        orphan = self.root / "forgotten/skills/orphan/SKILL.md"
        orphan.parent.mkdir(parents=True)
        orphan.write_text("---\nname: orphan\ndescription: Forgotten skill\n---\nBody\n")
        self.assert_invalid("unlisted skills")

    def test_accepts_description_at_frontmatter_end(self) -> None:
        self.skill.write_text("---\nname: example\ndescription: Example\n---")
        self.assertEqual(self.run_validator().returncode, 0)

    def test_rejects_invalid_frontmatter(self) -> None:
        self.skill.write_text("---\nname: [\n---\nBody\n")
        self.assert_invalid("invalid YAML")

    def test_rejects_unterminated_frontmatter(self) -> None:
        self.skill.write_text("---\nname: example\ndescription: Example\n")
        self.assert_invalid("unterminated")

    def test_rejects_non_mapping_frontmatter(self) -> None:
        self.skill.write_text("---\n- name\n- description\n---\nBody\n")
        self.assert_invalid("mapping")

    def test_rejects_malformed_entries(self) -> None:
        for value in (None, "example", [42]):
            with self.subTest(value=value):
                self.codex["plugins"] = value
                self.write_json(".agents/plugins/marketplace.json", self.codex)
                self.assert_invalid("must be")

    def test_rejects_source_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            (self.root / "escape").symlink_to(outside, target_is_directory=True)
            self.codex["plugins"][0]["source"]["path"] = "./escape"
            self.write_json(".agents/plugins/marketplace.json", self.codex)
            self.assert_invalid("inside")

    def test_existing_trigger_descriptions_are_complete(self) -> None:
        import yaml
        for plugin, skill, ending in [
            ("code-review", "review-changes", "Never approves, merges, or formally requests changes."),
            ("issue-delivery", "deliver-issue", "Never merges."),
        ]:
            with self.subTest(skill=skill):
                text = (REPO / plugin / "skills" / skill / "SKILL.md").read_text()
                metadata = yaml.safe_load(text.split("---", 2)[1])
                self.assertTrue(metadata["description"].endswith(ending), metadata["description"])


if __name__ == "__main__":
    unittest.main()
