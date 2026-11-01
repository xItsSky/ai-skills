"""Exercise the routing model against small, synthetic skill trees."""
from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "benchmark_skills.py"
SPEC = importlib.util.spec_from_file_location("benchmark_skills", SCRIPT)
BENCH = importlib.util.module_from_spec(SPEC)
# Register before exec: @dataclass resolves annotations through sys.modules.
sys.modules["benchmark_skills"] = BENCH
SPEC.loader.exec_module(BENCH)


class BenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        (self.data / "scenarios").mkdir(parents=True)
        self.write_skill("demo", "alpha", """
            ---
            name: alpha
            description: Demo skill
            ---
            # Alpha

            | When you are | Read |
            |---|---|
            | Writing code | `references/one.md` |
            | Using Postgres | `references/two.md` |

            Always consult `references/always.md` before finishing.
            """)
        self.write_reference("demo", "alpha", "one.md", "One. See `references/deep.md`.")
        self.write_reference("demo", "alpha", "two.md", "Two.")
        self.write_reference("demo", "alpha", "always.md", "Always.")
        self.write_reference("demo", "alpha", "deep.md", "Deep.")
        self.write_triggers({"writing code": ("writing_code", "task"),
                             "using postgres": ("postgres", "project")})
        self.write_budgets(files=99, tokens=99999, round_trips=99)
        self.write_scenario("basic", ["alpha"], ["writing_code"])

    # -- fixture helpers ------------------------------------------------------

    def write(self, relative: str, body: str) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
        return target

    def write_skill(self, plugin: str, skill: str, body: str) -> Path:
        return self.write(f"{plugin}/skills/{skill}/SKILL.md", body)

    def write_reference(self, plugin: str, skill: str, name: str, body: str) -> Path:
        return self.write(f"{plugin}/skills/{skill}/references/{name}", body)

    def write_triggers(self, mapping: dict[str, tuple[str, str]]) -> None:
        lines = [f'"{condition}":\n  key: {key}\n  scope: {scope}'
                 for condition, (key, scope) in mapping.items()]
        self.write("data/triggers.yaml", "\n".join(lines) + "\n")

    def write_budgets(self, **limits: int) -> None:
        body = "".join(
            f"{name}:\n  max: {{files: {limits['files']}, tokens: {limits['tokens']}, "
            f"round_trips: {limits['round_trips']}}}\n"
            for name in ("basic",))
        self.write("data/budgets.yaml", body)

    def write_scenario(self, name: str, skills: list[str], triggers: list[str]) -> None:
        body = ["skills:"] + [f"  - {s}" for s in skills]
        body += ["triggers:"] + [f"  - {t}" for t in triggers]
        self.write(f"data/scenarios/{name}.yaml", "\n".join(body) + "\n")

    def run_bench(self) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            code = BENCH.main(["--root", str(self.root), "--data", str(self.data)])
        return code, output.getvalue()

    def measure(self, scenario: str = "basic") -> "BENCH.Measurement":
        skills = BENCH.discover_skills(self.root)
        triggers = BENCH.read_yaml(self.data / "triggers.yaml")
        return BENCH.measure(BENCH.read_yaml(self.data / f"scenarios/{scenario}.yaml"),
                             scenario, skills, triggers, self.root)

    # -- parsing --------------------------------------------------------------

    def test_normalize_strips_backticks_and_case(self) -> None:
        self.assertEqual(BENCH.normalize("`@nestjs/core`   Thing"), "@nestjs/core thing")

    def test_parse_rows_ignores_separator_and_prose(self) -> None:
        rows = BENCH.parse_rows("| A | `references/x.md` |\n|---|---|\nprose only\n")
        self.assertEqual(rows, [("A", [("", "references/x.md")])])

    def test_parse_rows_skips_rows_without_references(self) -> None:
        self.assertEqual(BENCH.parse_rows("| Branch | Purpose |\n| main | prod |\n"), [])

    def test_routing_table_becomes_conditional_routes(self) -> None:
        skill = BENCH.discover_skills(self.root)["alpha"]
        self.assertEqual(sorted(skill.routes), ["using postgres", "writing code"])

    def test_prose_reference_without_a_route_is_unconditional(self) -> None:
        skill = BENCH.discover_skills(self.root)["alpha"]
        self.assertEqual([path.name for path in skill.unconditional], ["always.md"])

    def test_prose_reference_that_has_a_route_stays_conditional(self) -> None:
        self.write_skill("demo", "alpha", """
            ---
            name: alpha
            description: Demo skill
            ---
            | When you are | Read |
            |---|---|
            | Writing code | `references/one.md` |

            In a monorepo, also read `references/one.md`.
            """)
        self.assertEqual(BENCH.discover_skills(self.root)["alpha"].unconditional, [])

    # -- reference resolution -------------------------------------------------

    def test_prefixed_mention_resolves_across_skills(self) -> None:
        self.write_reference("demo", "beta", "shared.md", "Shared.")
        self.write_skill("demo", "beta", """
            ---
            name: beta
            description: Beta skill
            ---
            Read `beta/references/shared.md`.
            """)
        skill = BENCH.discover_skills(self.root)["beta"]
        self.assertEqual([path.name for path in skill.unconditional], ["shared.md"])

    def test_prefix_disambiguates_a_duplicated_basename(self) -> None:
        self.write_reference("demo", "alpha", "dup.md", "Alpha copy.")
        self.write_reference("other", "gamma", "dup.md", "Gamma copy.")
        self.write_skill("other", "gamma", """
            ---
            name: gamma
            description: Gamma skill
            ---
            Read `gamma/references/dup.md`.
            """)
        resolved = BENCH.resolve_reference(
            self.root / "demo/skills/alpha", ("gamma/", "references/dup.md"), self.root)
        self.assertEqual(resolved, self.root / "other/skills/gamma/references/dup.md")

    def test_ambiguous_mention_resolves_to_nothing(self) -> None:
        self.write_reference("demo", "alpha", "dup.md", "Alpha copy.")
        self.write_reference("other", "gamma", "dup.md", "Gamma copy.")
        self.write_skill("other", "gamma", "---\nname: gamma\ndescription: G\n---\n")
        resolved = BENCH.resolve_reference(
            self.root / "demo/skills/beta", ("", "references/dup.md"), self.root)
        self.assertIsNone(resolved)

    def test_missing_routed_reference_is_an_error(self) -> None:
        self.write_skill("demo", "alpha", """
            ---
            name: alpha
            description: Demo skill
            ---
            | When you are | Read |
            |---|---|
            | Writing code | `references/absent.md` |
            """)
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("points at a missing reference", output)

    # -- nesting --------------------------------------------------------------

    def test_nested_reference_is_reported_and_costs_a_round_trip(self) -> None:
        measurement = self.measure()
        self.assertEqual([path.name for path in measurement.nested], ["deep.md"])
        self.assertEqual(measurement.round_trips, 3)

    def test_nesting_disappears_once_the_target_is_loaded(self) -> None:
        self.write_reference("demo", "alpha", "one.md", "One, with no pointer.")
        self.assertEqual(self.measure().nested, [])

    def test_skill_tables_are_not_treated_as_nesting(self) -> None:
        # two.md is routed but inactive here; it must not surface as a nested hop.
        self.assertNotIn("two.md", [path.name for path in self.measure().nested])

    # -- scenario resolution --------------------------------------------------

    def test_inactive_trigger_keeps_its_reference_out(self) -> None:
        self.assertNotIn("two.md", [path.name for path in self.measure().files])

    def test_active_trigger_pulls_its_reference_in(self) -> None:
        self.write_scenario("basic", ["alpha"], ["writing_code", "postgres"])
        self.assertIn("two.md", [path.name for path in self.measure().files])

    def test_task_scope_trigger_needs_no_detection_pass(self) -> None:
        measurement = self.measure()
        self.assertFalse(measurement.needs_detection)
        self.assertEqual(measurement.round_trips, 3)

    def test_project_scope_trigger_forces_a_detection_pass(self) -> None:
        self.write_scenario("basic", ["alpha"], ["postgres"])
        self.assertTrue(self.measure().needs_detection)

    def test_unbatched_round_trips_track_the_file_count(self) -> None:
        measurement = self.measure()
        self.assertEqual(measurement.unbatched_round_trips,
                         1 + int(measurement.needs_detection) + measurement.file_count)

    def test_tokens_exclude_nested_files(self) -> None:
        measurement = self.measure()
        expected = sum(path.stat().st_size for path in measurement.files) // 4
        self.assertEqual(measurement.tokens, expected)

    # -- drift gates ----------------------------------------------------------

    def test_undeclared_routing_condition_fails(self) -> None:
        self.write_triggers({"writing code": ("writing_code", "task")})
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("missing from triggers.yaml", output)
        self.assertIn("using postgres", output)

    def test_trigger_for_no_routing_row_fails(self) -> None:
        self.write_triggers({"writing code": ("writing_code", "task"),
                             "using postgres": ("postgres", "project"),
                             "ghost condition": ("ghost", "task")})
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("conditions no skill uses", output)

    def test_unknown_trigger_in_a_scenario_fails(self) -> None:
        self.write_scenario("basic", ["alpha"], ["nonexistent"])
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("unknown trigger", output)

    def test_unknown_skill_in_a_scenario_fails(self) -> None:
        self.write_scenario("basic", ["ghost"], ["writing_code"])
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("unknown skill", output)

    def test_scenario_without_skills_fails(self) -> None:
        self.write("data/scenarios/basic.yaml", "triggers: []\n")
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("'skills' must be a nonempty list", output)

    def test_scenario_without_a_budget_fails(self) -> None:
        self.write_scenario("extra", ["alpha"], ["writing_code"])
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("no budget declared", output)

    # -- budgets --------------------------------------------------------------

    def test_passing_run_reports_every_scenario(self) -> None:
        code, output = self.run_bench()
        self.assertEqual(code, 0, output)
        self.assertIn("basic", output)
        self.assertIn("All scenarios within budget", output)

    def test_exceeding_the_file_ceiling_fails(self) -> None:
        self.write_budgets(files=1, tokens=99999, round_trips=99)
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("files 3 exceeds max 1", output)

    def test_exceeding_the_token_ceiling_fails(self) -> None:
        self.write_budgets(files=99, tokens=1, round_trips=99)
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("tokens", output)
        self.assertIn("exceeds max 1", output)

    def test_exceeding_the_round_trip_ceiling_fails(self) -> None:
        self.write_budgets(files=99, tokens=99999, round_trips=1)
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("round_trips 3 exceeds max 1", output)

    def test_non_integer_ceiling_fails(self) -> None:
        self.write("data/budgets.yaml",
                   "basic:\n  max: {files: many, tokens: 10, round_trips: 3}\n")
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("must be an integer", output)

    def test_crossing_the_compaction_budget_warns_without_failing(self) -> None:
        self.write_reference("demo", "alpha", "one.md",
                             "x" * (BENCH.COMPACTION_BUDGET_TOKENS * 4 + 10))
        code, output = self.run_bench()
        self.assertEqual(code, 0, output)
        self.assertIn("after compaction", output)

    # -- input handling -------------------------------------------------------

    def test_invalid_yaml_fails_cleanly(self) -> None:
        self.write("data/budgets.yaml", "basic: [unclosed\n")
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", output)

    def test_non_mapping_yaml_fails_cleanly(self) -> None:
        self.write("data/budgets.yaml", "- a list\n")
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("expected a YAML mapping", output)

    def test_missing_file_fails_cleanly(self) -> None:
        (self.data / "budgets.yaml").unlink()
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("cannot read file", output)

    def test_tree_without_skills_fails(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = BENCH.main(["--root", str(self.data), "--data", str(self.data)])
        self.assertEqual(code, 1)
        self.assertIn("no skills found", output.getvalue())

    def test_missing_scenario_directory_fails(self) -> None:
        for path in (self.data / "scenarios").iterdir():
            path.unlink()
        code, output = self.run_bench()
        self.assertEqual(code, 1)
        self.assertIn("no scenario files found", output)


class RepositoryTests(unittest.TestCase):
    """The real tables must stay parseable and inside their declared budgets."""

    def test_repository_is_within_budget(self) -> None:
        root = SCRIPT.parents[2]
        output = io.StringIO()
        with redirect_stdout(output):
            code = BENCH.main(["--root", str(root)])
        self.assertEqual(code, 0, output.getvalue())


if __name__ == "__main__":
    unittest.main()
