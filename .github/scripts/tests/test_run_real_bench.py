"""Exercise the real-bench aggregation without ever invoking the CLI."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "run_real_bench.py"
SPEC = importlib.util.spec_from_file_location("run_real_bench", SCRIPT)
BENCH = importlib.util.module_from_spec(SPEC)
sys.modules["run_real_bench"] = BENCH
SPEC.loader.exec_module(BENCH)


def completed(stdout: str = "", returncode: int = 0, stderr: str = "") -> mock.Mock:
    return mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)


PAYLOAD = json.dumps({
    "duration_ms": 12000, "num_turns": 9, "total_cost_usd": 0.42,
    "usage": {"input_tokens": 1000, "output_tokens": 300,
              "cache_read_input_tokens": 8000, "cache_creation_input_tokens": 500},
})


class SummarizeTests(unittest.TestCase):
    def test_median_is_taken_across_repeats(self) -> None:
        runs = [{"turns": 5, "wall_clock_s": 10.0}, {"turns": 9, "wall_clock_s": 30.0},
                {"turns": 7, "wall_clock_s": 20.0}]
        summary = BENCH.summarize(runs)
        self.assertEqual(summary["turns"], 7)
        self.assertEqual(summary["wall_clock_s"], 20.0)
        self.assertEqual((summary["attempted"], summary["succeeded"]), (3, 3))

    def test_partial_failure_is_counted_not_hidden(self) -> None:
        summary = BENCH.summarize([{"error": "boom"}, {"turns": 4}, {"turns": 6}])
        self.assertEqual(summary["turns"], 5)
        self.assertEqual((summary["attempted"], summary["succeeded"]), (3, 2))
        self.assertEqual(summary["first_failure"], "boom")

    def test_a_clean_sweep_records_no_failure(self) -> None:
        self.assertNotIn("first_failure", BENCH.summarize([{"turns": 4}]))

    def test_all_runs_failing_surfaces_the_error(self) -> None:
        summary = BENCH.summarize([{"error": "boom"}, {"error": "boom"}])
        self.assertEqual(summary["error"], "boom")
        self.assertEqual(summary["succeeded"], 0)
        self.assertNotIn("turns", summary)

    def test_missing_metric_is_omitted_rather_than_zeroed(self) -> None:
        self.assertNotIn("cost_usd", BENCH.summarize([{"turns": 3}]))


class SpreadTests(unittest.TestCase):
    def test_spread_records_the_observed_range(self) -> None:
        summary = BENCH.summarize([{"turns": 5}, {"turns": 9}, {"turns": 7}])
        self.assertEqual(summary["turns_spread"], [5, 9])

    def test_noise_floor_is_the_range_over_the_median(self) -> None:
        summary = BENCH.summarize([{"turns": 5}, {"turns": 9}, {"turns": 10}])
        # median 9, range 5, so the floor is 5/9 in percent
        self.assertAlmostEqual(BENCH.noise_floor(summary, "turns"), 500 / 9, places=4)

    def test_noise_floor_is_unknown_without_a_spread(self) -> None:
        self.assertIsNone(BENCH.noise_floor({"turns": 5}, "turns"))

    def test_noise_floor_is_unknown_without_a_median(self) -> None:
        self.assertIsNone(BENCH.noise_floor({"turns": 0, "turns_spread": [0, 0]}, "turns"))

    def test_a_delta_inside_the_spread_is_flagged_as_noise(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            BENCH.report({"small": {"attempted": 3, "succeeded": 3, "turns": 20,
                                    "turns_spread": [14, 26]}},
                         {"small": {"turns": 21}})
        self.assertIn("within noise", output.getvalue())

    def test_a_delta_beyond_the_spread_is_not_flagged(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            BENCH.report({"small": {"attempted": 3, "succeeded": 3, "turns": 10,
                                    "turns_spread": [10, 10]}},
                         {"small": {"turns": 20}})
        self.assertNotIn("within noise", output.getvalue())


class DeltaTests(unittest.TestCase):
    def test_delta_shows_absolute_and_relative_change(self) -> None:
        text = BENCH.format_delta("turns", {"turns": 5}, {"turns": 10})
        self.assertIn("-5", text)
        self.assertIn("-50%", text)

    def test_delta_is_blank_without_a_baseline(self) -> None:
        self.assertEqual(BENCH.format_delta("turns", {"turns": 5}, {}), "")

    def test_delta_is_blank_when_the_baseline_is_zero(self) -> None:
        self.assertEqual(BENCH.format_delta("turns", {"turns": 5}, {"turns": 0}), "")


class RunOnceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixture = Path(self.temp.name) / "small"
        self.fixture.mkdir()
        (self.fixture / "package.json").write_text("{}", encoding="utf-8")

    def run_once(self, *results: object) -> dict:
        with mock.patch.object(BENCH.subprocess, "run", side_effect=results):
            return BENCH.run_once("do the thing", self.fixture, None)

    def test_successful_run_is_parsed(self) -> None:
        result = self.run_once(completed(), completed(PAYLOAD))
        self.assertEqual(result["turns"], 9)
        self.assertEqual(result["cache_read"], 8000)
        self.assertEqual(result["cost_usd"], 0.42)
        self.assertIn("wall_clock_s", result)

    def test_nonzero_exit_is_reported_as_an_error(self) -> None:
        result = self.run_once(completed(), completed("", 1, "claude exploded"))
        self.assertIn("claude exploded", result["error"])

    def test_unparseable_output_is_reported_as_an_error(self) -> None:
        result = self.run_once(completed(), completed("not json"))
        self.assertIn("could not parse", result["error"])

    def test_timeout_is_reported_as_an_error(self) -> None:
        result = self.run_once(completed(), subprocess.TimeoutExpired("claude", 1))
        self.assertIn("timed out", result["error"])

    def test_payload_without_usage_still_returns(self) -> None:
        result = self.run_once(completed(), completed(json.dumps({"num_turns": 2})))
        self.assertEqual(result["turns"], 2)
        self.assertIsNone(result["input_tokens"])

    def test_hitting_the_turn_limit_counts_as_a_failure(self) -> None:
        # A truncated run still exits zero, so only the subtype gives it away.
        payload = json.dumps({"num_turns": 40, "subtype": "error_max_turns",
                              "usage": {"input_tokens": 10}})
        result = self.run_once(completed(), completed(payload))
        self.assertIn("error_max_turns", result["error"])
        self.assertEqual(result["turns"], 40)

    def test_an_error_flagged_payload_counts_as_a_failure(self) -> None:
        payload = json.dumps({"num_turns": 3, "is_error": True, "subtype": "success"})
        self.assertIn("error", self.run_once(completed(), completed(payload)))

    def test_a_success_subtype_is_recorded(self) -> None:
        payload = json.dumps({"num_turns": 3, "subtype": "success", "usage": {}})
        self.assertEqual(self.run_once(completed(), completed(payload))["outcome"],
                         "success")

    def test_the_fixture_is_copied_not_mutated(self) -> None:
        def capture(command, **kwargs):
            if command[0] == "git":
                return completed()
            Path(kwargs["cwd"], "scratch.txt").write_text("written", encoding="utf-8")
            return completed(PAYLOAD)

        with mock.patch.object(BENCH.subprocess, "run", side_effect=capture):
            BENCH.run_once("do the thing", self.fixture, None)
        self.assertFalse((self.fixture / "scratch.txt").exists())

    def capture_command(self, *args: object) -> list[str]:
        seen = []

        def capture(command, **kwargs):
            seen.append(command)
            return completed(PAYLOAD) if command[0] == "claude" else completed()

        with mock.patch.object(BENCH.subprocess, "run", side_effect=capture):
            BENCH.run_once("task", self.fixture, *args)
        return seen[-1]

    def test_model_override_is_passed_through(self) -> None:
        command = self.capture_command("claude-opus-4-8")
        self.assertIn("--model", command)
        self.assertIn("claude-opus-4-8", command)

    def test_each_plugin_directory_is_passed_through(self) -> None:
        command = self.capture_command(None, [Path("/tmp/clean-code"), Path("/tmp/devops")])
        self.assertEqual(command.count("--plugin-dir"), 2)
        self.assertIn("/tmp/devops", command)

    def test_no_plugin_directories_leaves_the_flag_off(self) -> None:
        self.assertNotIn("--plugin-dir", self.capture_command(None, []))


class LocalPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def add_plugin(self, name: str) -> None:
        manifest = self.root / name / ".claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}", encoding="utf-8")

    def test_plugins_are_discovered_from_their_manifests(self) -> None:
        self.add_plugin("clean-code")
        self.add_plugin("devops")
        self.assertEqual([path.name for path in BENCH.local_plugins(self.root)],
                         ["clean-code", "devops"])

    def test_a_tree_without_manifests_yields_nothing(self) -> None:
        self.assertEqual(BENCH.local_plugins(self.root), [])


class ReportTests(unittest.TestCase):
    def render(self, results: dict, baseline: dict | None = None) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            BENCH.report(results, baseline)
        return output.getvalue()

    def test_report_prints_metrics_and_deltas(self) -> None:
        text = self.render(
            {"small": {"attempted": 3, "succeeded": 3, "turns": 5, "wall_clock_s": 9.0}},
            {"small": {"turns": 10, "wall_clock_s": 18.0}})
        self.assertIn("3/3 runs succeeded", text)
        self.assertIn("-50%", text)

    def test_report_surfaces_a_fully_failed_scenario(self) -> None:
        text = self.render({"large": {"attempted": 3, "succeeded": 0,
                                      "error": "timed out"}})
        self.assertIn("ALL RUNS FAILED: timed out", text)

    def test_report_warns_loudly_on_a_partial_failure(self) -> None:
        text = self.render({"large": {"attempted": 3, "succeeded": 1, "turns": 7,
                                      "first_failure": "ended as error_max_turns"}})
        self.assertIn("1/3 runs succeeded", text)
        self.assertIn("WARNING", text)
        self.assertIn("error_max_turns", text)


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / ".github/benchmarks"
        (self.data / "scenarios").mkdir(parents=True)
        (self.data / "fixtures/small").mkdir(parents=True)
        (self.data / "scenarios/small.yaml").write_text(
            "task: Add a helper\nskills: [core-development]\ntriggers: []\n", encoding="utf-8")

    def main(self, argv: list[str], result: dict | None = None) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.object(BENCH.shutil, "which", return_value="/usr/bin/claude"), \
             mock.patch.object(BENCH, "run_once", return_value=result or {"turns": 4}), \
             redirect_stdout(output):
            code = BENCH.main(["--root", str(self.root), *argv])
        return code, output.getvalue()

    def test_missing_cli_exits(self) -> None:
        with mock.patch.object(BENCH.shutil, "which", return_value=None):
            with self.assertRaises(SystemExit):
                BENCH.main(["--root", str(self.root)])

    def test_run_reports_and_succeeds(self) -> None:
        code, text = self.main(["--repeat", "1"])
        self.assertEqual(code, 0, text)
        self.assertIn("small", text)

    def test_local_plugins_are_measured_by_default(self) -> None:
        manifest = self.root / "clean-code/.claude-plugin/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}", encoding="utf-8")
        code, text = self.main(["--repeat", "1"])
        self.assertEqual(code, 0, text)
        self.assertIn("measuring 1 local plugin", text)

    def test_installed_flag_skips_the_working_tree(self) -> None:
        code, text = self.main(["--repeat", "1", "--installed"])
        self.assertEqual(code, 0, text)
        self.assertIn("measuring the installed plugins", text)

    def test_only_filters_scenarios(self) -> None:
        code, text = self.main(["--repeat", "1", "--only", "absent"])
        self.assertEqual(code, 0, text)
        self.assertNotIn("running small", text)

    def test_scenario_without_a_fixture_is_an_error(self) -> None:
        (self.data / "fixtures/small").rmdir()
        code, text = self.main(["--repeat", "1"])
        self.assertEqual(code, 1)
        self.assertIn("fixtures/ directory", text)

    def test_results_are_written_and_can_be_compared(self) -> None:
        out = self.root / "after.json"
        before = self.root / "before.json"
        before.write_text(json.dumps({"small": {"runs": 1, "turns": 8}}), encoding="utf-8")
        code, text = self.main(
            ["--repeat", "1", "--out", str(out), "--compare", str(before)])
        self.assertEqual(code, 0, text)
        self.assertEqual(json.loads(out.read_text())["small"]["turns"], 4)
        self.assertIn("-50%", text)

    def test_no_scenarios_exits(self) -> None:
        (self.data / "scenarios/small.yaml").unlink()
        with mock.patch.object(BENCH.shutil, "which", return_value="/usr/bin/claude"), \
             redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                BENCH.main(["--root", str(self.root)])


if __name__ == "__main__":
    unittest.main()
