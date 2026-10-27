#!/usr/bin/env python3
"""Measure what a skill invocation costs before it writes a line of code.

Static model of the routing tables in every SKILL.md. For a scenario it resolves
which reference files load, then reports file count, token estimate, and the
floor on sequential round-trips. Budgets gate the result so a routing change
cannot quietly make every task slower.

This measures the *design*. What the model actually does at runtime is measured
by run_real_bench.py.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

import yaml

# Markdown English prose runs close to four characters per token. The absolute
# value matters less than its stability: budgets are calibrated against it, and
# run_real_bench.py reports the true ratio so they can be re-tuned.
CHARS_PER_TOKEN = 4

# Claude Code keeps at most this many tokens of skill content after compaction,
# shared across every skill in the session. Past it, older skills are dropped
# outright, so a scenario above the line is one that silently loses guidance.
# https://code.claude.com/docs/en/skills
COMPACTION_BUDGET_TOKENS = 25_000

REFERENCE = re.compile(r"`(?P<prefix>[^`]*?)(?P<tail>references/[A-Za-z0-9._/-]+\.md)`")
TABLE_ROW = re.compile(r"^\|(?P<cells>.+)\|\s*$")
SEPARATOR = re.compile(r"^\|[\s:|-]+\|\s*$")


class BenchmarkError(ValueError):
    """A scenario, budget, or routing table cannot be resolved."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkError(message)


def read_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BenchmarkError(f"{path}: cannot read file: {exc}") from exc
    except yaml.YAMLError as exc:
        raise BenchmarkError(f"{path}: invalid YAML: {exc}") from exc
    require(isinstance(data, dict), f"{path}: expected a YAML mapping")
    return data


def normalize(condition: str) -> str:
    """Collapse a routing-table cell to a stable key for the trigger map."""
    return " ".join(condition.replace("`", "").split()).lower()


@dataclass
class Skill:
    """One SKILL.md and the reference files its routing table can reach."""

    name: str
    path: Path
    routes: dict[str, list[Path]] = field(default_factory=dict)
    unconditional: list[Path] = field(default_factory=list)


def find_references(text: str) -> list[tuple[str, str]]:
    """Every backticked reference mention, as (prefix, 'references/...md')."""
    return [(match["prefix"], match["tail"]) for match in REFERENCE.finditer(text)]


def resolve_reference(skill_dir: Path, mention: tuple[str, str], root: Path) -> Path | None:
    """Resolve a reference mention to a file, honouring any plugin/skill prefix.

    Mentions appear as `references/x.md`, `core-development/references/x.md`, or
    `../../core-development/references/x.md`. The prefix disambiguates basenames
    that exist in more than one plugin, so it is used before any wildcard search.
    """
    prefix, tail = mention
    # An explicit prefix is a deliberate choice of owner, so it outranks a
    # same-named file sitting next to the mention.
    for segment in reversed([part for part in prefix.split("/") if part not in ("", ".", "..")]):
        for pattern in (f"*/skills/{segment}/{tail}", f"{segment}/skills/*/{tail}"):
            scoped = sorted(root.glob(pattern))
            if len(scoped) == 1:
                return scoped[0]
    local = skill_dir / tail
    if local.is_file():
        return local
    matches = sorted(root.glob(f"*/skills/*/{tail}"))
    return matches[0] if len(matches) == 1 else None


def parse_rows(text: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Extract (condition, reference mentions) from every markdown table row."""
    rows = []
    for line in text.splitlines():
        match = TABLE_ROW.match(line.strip())
        if not match or SEPARATOR.match(line.strip()):
            continue
        cells = [cell.strip() for cell in match["cells"].split("|")]
        mentions = find_references(line)
        if cells and mentions:
            rows.append((cells[0], mentions))
    return rows


def parse_skill(path: Path, root: Path) -> Skill:
    """Build the routing model for one SKILL.md."""
    text = path.read_text(encoding="utf-8")
    skill = Skill(name=path.parent.name, path=path)
    for condition, mentions in parse_rows(text):
        resolved = [resolve_reference(path.parent, mention, root) for mention in mentions]
        found = [item for item in resolved if item is not None]
        require(len(found) == len(resolved),
                f"{path}: routing row '{condition}' points at a missing reference")
        skill.routes.setdefault(normalize(condition), []).extend(found)
    return skill


def attach_prose(skill: Skill, routed: set[Path], root: Path) -> None:
    """Record prose-mentioned references that no routing row governs.

    Prose mostly restates a condition the tables already carry ("in an NX
    monorepo, also read nx.md"). Those stay conditional. A file reachable only
    through prose has no gate at all, so it loads whenever the skill does.
    """
    body = "\n".join(line for line in skill.path.read_text(encoding="utf-8").splitlines()
                     if not TABLE_ROW.match(line.strip()))
    for mention in sorted(set(find_references(body))):
        resolved = resolve_reference(skill.path.parent, mention, root)
        require(resolved is not None,
                f"{skill.path}: prose points at a missing {mention[0]}{mention[1]}")
        if resolved not in routed and resolved not in skill.unconditional:
            skill.unconditional.append(resolved)


def discover_skills(root: Path) -> dict[str, Skill]:
    skills = {}
    for path in sorted(root.glob("*/skills/*/SKILL.md")):
        skill = parse_skill(path, root)
        require(skill.name not in skills, f"{skill.name}: duplicate skill name")
        skills[skill.name] = skill
    require(bool(skills), f"{root}: no skills found")
    routed = {target for skill in skills.values()
              for targets in skill.routes.values() for target in targets}
    for skill in skills.values():
        attach_prose(skill, routed, root)
    return skills


def nested_references(files: list[Path], root: Path) -> list[Path]:
    """References pointed at from inside another reference, not already loaded.

    Anthropic caps references at one level deep from SKILL.md: a deeper hop
    risks a partial read and a recovery round-trip. These are not counted as
    loaded tokens, because following the pointer is a judgement call, but each
    one is a latency risk worth reporting.
    """
    sources = [path for path in files if path.name != "SKILL.md"]
    reached = []
    for source in sources:
        for mention in find_references(source.read_text(encoding="utf-8")):
            resolved = resolve_reference(source.parent.parent, mention, root)
            if resolved is not None and resolved not in files:
                reached.append(resolved)
    return sorted(set(reached))


def check_triggers(skills: dict[str, Skill], triggers: dict) -> None:
    """Fail when a routing row has no declared trigger.

    This is the anti-drift gate: a new routing row cannot ship until someone
    states which scenarios pay for it.
    """
    declared = set(triggers)
    routed = {condition for skill in skills.values() for condition in skill.routes}
    missing = sorted(routed - declared)
    require(not missing,
            "routing conditions missing from triggers.yaml: " + ", ".join(missing))
    stale = sorted(declared - routed)
    require(not stale, "triggers.yaml declares conditions no skill uses: " + ", ".join(stale))


@dataclass
class Measurement:
    """What one scenario costs before the first productive edit."""

    scenario: str
    files: list[Path]
    nested: list[Path]
    needs_detection: bool

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def tokens(self) -> int:
        chars = sum(path.stat().st_size for path in self.files)
        return chars // CHARS_PER_TOKEN

    @property
    def round_trips(self) -> int:
        """Floor on sequential turns: load, detect, batch, then any deeper hop."""
        return 1 + int(self.needs_detection) + 1 + int(bool(self.nested))

    @property
    def unbatched_round_trips(self) -> int:
        """What reading one file per turn costs, which is today's behaviour."""
        return 1 + int(self.needs_detection) + self.file_count


def measure(scenario: dict, name: str, skills: dict[str, Skill],
            triggers: dict, root: Path) -> Measurement:
    entries = scenario.get("skills")
    require(isinstance(entries, list) and bool(entries),
            f"{name}: 'skills' must be a nonempty list")
    active = scenario.get("triggers") or []
    require(isinstance(active, list), f"{name}: 'triggers' must be a list")
    unknown = sorted(set(active) - {trigger["key"] for trigger in triggers.values()})
    require(not unknown, f"{name}: unknown trigger(s): " + ", ".join(unknown))

    files, needs_detection = [], False
    for entry in entries:
        require(entry in skills, f"{name}: unknown skill '{entry}'")
        skill = skills[entry]
        files.append(skill.path)
        files.extend(skill.unconditional)
        for condition, targets in skill.routes.items():
            trigger = triggers[condition]
            if trigger["key"] in active:
                files.extend(targets)
                needs_detection |= trigger.get("scope") == "project"
    files = sorted(set(files))
    return Measurement(name, files, nested_references(files, root), needs_detection)


def evaluate(measurement: Measurement, budget: dict) -> list[str]:
    """Compare a measurement against its ceiling. Returns breach descriptions."""
    limits = {"files": measurement.file_count, "tokens": measurement.tokens,
              "round_trips": measurement.round_trips}
    breaches = []
    for metric, actual in limits.items():
        ceiling = budget.get("max", {}).get(metric)
        require(isinstance(ceiling, int),
                f"{measurement.scenario}: budget 'max.{metric}' must be an integer")
        if actual > ceiling:
            breaches.append(f"{metric} {actual} exceeds max {ceiling}")
    return breaches


def format_row(measurement: Measurement, budget: dict) -> str:
    target = budget.get("target", {})
    return (f"  {measurement.scenario:<7}"
            f"files {measurement.file_count:>3}/{budget['max']['files']:<3}"
            f"(target {str(target.get('files', '-')):>3})   "
            f"tokens {measurement.tokens:>6}/{budget['max']['tokens']:<6}"
            f"(target {str(target.get('tokens', '-')):>6})   "
            f"trips {measurement.round_trips:>2}/{budget['max']['round_trips']:<2}"
            f"(unbatched {measurement.unbatched_round_trips:>3})   "
            f"nested {len(measurement.nested):>2}")


def run(root: Path, data: Path) -> int:
    skills = discover_skills(root)
    triggers = read_yaml(data / "triggers.yaml")
    budgets = read_yaml(data / "budgets.yaml")
    check_triggers(skills, triggers)

    scenarios = sorted((data / "scenarios").glob("*.yaml"))
    require(bool(scenarios), f"{data}/scenarios: no scenario files found")

    failures, crowded = [], []
    print("Skill invocation cost (static routing model):")
    for path in scenarios:
        name = path.stem
        require(name in budgets, f"{name}: no budget declared in budgets.yaml")
        measurement = measure(read_yaml(path), name, skills, triggers, root)
        print(format_row(measurement, budgets[name]))
        failures.extend(f"{name}: {breach}"
                        for breach in evaluate(measurement, budgets[name]))
        if measurement.tokens > COMPACTION_BUDGET_TOKENS:
            crowded.append(f"{name}: {measurement.tokens} tokens")
    if crowded:
        print(f"\nWarning: over the {COMPACTION_BUDGET_TOKENS}-token skills budget "
              "Claude Code keeps after compaction. Older skills get dropped.")
        for scenario in crowded:
            print(f"  {scenario}")
    if failures:
        print("\nBudget exceeded:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("\nAll scenarios within budget.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="repository root holding the skill plugins")
    parser.add_argument("--data", type=Path, default=None,
                        help="directory holding budgets, triggers, and scenarios")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    data = (args.data or root / ".github/benchmarks").resolve()
    try:
        return run(root, data)
    except (BenchmarkError, OSError) as exc:
        print(f"Benchmark failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
