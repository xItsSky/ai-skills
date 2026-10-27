#!/usr/bin/env python3
"""Run each benchmark scenario through Claude Code and record what it really cost.

benchmark_skills.py models the routing on paper. This runs it: each scenario's
task is handed to `claude -p` inside a throwaway copy of its fixture project,
and the reported turns, tokens, and wall-clock come back as measurements.

Not a CI gate. Wall-clock swings with API load, and every run spends tokens.
Use it to calibrate the budgets in budgets.yaml and to compare two revisions of
the skills against each other.

    python .github/scripts/run_real_bench.py --out before.json
    git checkout some-optimization
    python .github/scripts/run_real_bench.py --out after.json --compare before.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import yaml

TURN_LIMIT = 40
TIMEOUT_SECONDS = 900


def load_scenarios(data: Path) -> list[tuple[str, dict]]:
    paths = sorted((data / "scenarios").glob("*.yaml"))
    if not paths:
        raise SystemExit(f"{data}/scenarios: no scenario files found")
    return [(path.stem, yaml.safe_load(path.read_text(encoding="utf-8"))) for path in paths]


def local_plugins(root: Path) -> list[Path]:
    """Plugin directories in this working tree, newest edits and all."""
    return sorted(path.parent.parent for path in root.glob("*/.claude-plugin/plugin.json"))


def run_once(task: str, fixture: Path, model: str | None,
             plugins: list[Path] | None = None) -> dict:
    """Run one task in a disposable copy of the fixture and parse the result."""
    with tempfile.TemporaryDirectory() as workspace:
        project = Path(workspace) / fixture.name
        shutil.copytree(fixture, project)
        subprocess.run(["git", "init", "--quiet"], cwd=project, check=True)
        command = ["claude", "-p", task, "--output-format", "json",
                   "--max-turns", str(TURN_LIMIT)]
        # Without this the run loads whatever version is installed in the plugin
        # cache, so a before/after comparison would measure the wrong tree.
        for plugin in plugins or []:
            command += ["--plugin-dir", str(plugin)]
        if model:
            command += ["--model", model]
        started = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=project, capture_output=True,
                                       text=True, timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            return {"error": f"timed out after {TIMEOUT_SECONDS}s"}
        elapsed = time.monotonic() - started
    if completed.returncode != 0:
        return {"error": (completed.stderr or completed.stdout).strip()[:400]}
    try:
        payload = json.loads(completed.stdout)
    except ValueError:
        return {"error": "could not parse --output-format json output"}
    usage = payload.get("usage") or {}
    return {
        "wall_clock_s": round(elapsed, 1),
        "reported_ms": payload.get("duration_ms"),
        "turns": payload.get("num_turns"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cache_read": usage.get("cache_read_input_tokens"),
        "cache_write": usage.get("cache_creation_input_tokens"),
        "cost_usd": payload.get("total_cost_usd"),
    }


def summarize(runs: list[dict]) -> dict:
    """Median across repeats, which is steadier than a mean on a noisy signal."""
    clean = [run for run in runs if "error" not in run]
    if not clean:
        return {"error": runs[0].get("error", "all runs failed"), "runs": len(runs)}
    summary = {"runs": len(clean)}
    for metric in ("wall_clock_s", "turns", "input_tokens", "output_tokens",
                   "cache_read", "cache_write", "cost_usd"):
        values = [run[metric] for run in clean if isinstance(run.get(metric), (int, float))]
        if values:
            summary[metric] = round(statistics.median(values), 2)
    return summary


def format_delta(name: str, now: dict, before: dict) -> str:
    was, is_now = before.get(name), now.get(name)
    if not isinstance(was, (int, float)) or not isinstance(is_now, (int, float)) or not was:
        return ""
    return f"  ({is_now - was:+.0f}, {(is_now - was) / was * 100:+.0f}%)"


def report(results: dict, baseline: dict | None) -> None:
    for scenario, summary in results.items():
        print(f"\n{scenario}")
        if "error" in summary:
            print(f"  failed: {summary['error']}")
            continue
        previous = (baseline or {}).get(scenario, {})
        for metric in ("wall_clock_s", "turns", "input_tokens", "output_tokens",
                       "cache_read", "cost_usd"):
            if metric in summary:
                print(f"  {metric:<14} {summary[metric]:>10}"
                      f"{format_delta(metric, summary, previous)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--repeat", type=int, default=3,
                        help="runs per scenario; the median is reported")
    parser.add_argument("--model", default=None, help="override the model under test")
    parser.add_argument("--only", action="append", help="limit to a scenario, repeatable")
    parser.add_argument("--out", type=Path, help="write results as JSON")
    parser.add_argument("--compare", type=Path, help="prior results to diff against")
    parser.add_argument("--installed", action="store_true",
                        help="measure the installed plugins instead of this tree")
    args = parser.parse_args(argv)

    if shutil.which("claude") is None:
        raise SystemExit("the `claude` CLI is not on PATH")
    data = (args.data or args.root / ".github/benchmarks").resolve()
    baseline = json.loads(args.compare.read_text()) if args.compare else None
    plugins = [] if args.installed else local_plugins(args.root.resolve())
    print(f"measuring {len(plugins)} local plugin(s)" if plugins
          else "measuring the installed plugins")

    results = {}
    for name, scenario in load_scenarios(data):
        if args.only and name not in args.only:
            continue
        task = scenario.get("task")
        fixture = data / "fixtures" / name
        if not task or not fixture.is_dir():
            results[name] = {"error": "scenario needs a 'task' and a fixtures/ directory"}
            continue
        print(f"running {name} x{args.repeat} ...", flush=True)
        results[name] = summarize(
            [run_once(task, fixture, args.model, plugins) for _ in range(args.repeat)])

    report(results, baseline)
    if args.out:
        args.out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0 if all("error" not in value for value in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
