# Skill cost benchmarks

These benchmarks measure what invoking a skill costs before it writes a single
line of code, and fail the build when that cost grows.

There are two harnesses. One models the routing on paper and runs on every pull
request; the other runs the scenarios for real and is driven by hand.

## The static gate

`benchmark_skills.py` reads the routing tables out of every `SKILL.md` and works
out which reference files a given scenario pulls in. It runs on every pull
request, needs no API key, and finishes in well under a second.

```
python .github/scripts/benchmark_skills.py
```

It reports four numbers per scenario:

| Metric | Meaning |
|---|---|
| `files` | reference files the routing selects |
| `tokens` | their combined size, at four characters per token |
| `trips` | the design floor: load the skill, detect the stack, read one batch |
| `unbatched` | what reading one file per turn costs, which is the shape of today's instructions |
| `nested` | references pointed at from inside another reference |

Most of the available speedup sits in the gap between `trips` and `unbatched`. A
skill whose instructions let the model fetch everything in one batch pays the
floor. One that walks the model through a file at a time pays the larger number,
and pays it in seconds of wall-clock.

`nested` counts hops that break Anthropic's one-level-deep rule for references.
Each one risks a partial read and a recovery turn, so each one adds a round trip.

### Budgets

`budgets.yaml` carries two sets of numbers per scenario. `max` is a ratchet: it
starts at the measured baseline and only ever goes down, so no change can quietly
make every task slower. `target` is where the scenario should land once the
optimization work is finished; it is reported but never enforced.

Lowering a `max` is the normal way to bank a win. Raising one needs a reason in
the pull request.

### Why a change can fail the gate

Beyond a blown budget, two kinds of drift fail the run:

- A routing row whose condition is not declared in `triggers.yaml`. Adding a
  route means saying which scenarios pay for it.
- An entry in `triggers.yaml` that no routing row uses any more.

Both exist so the model in this directory cannot silently fall out of step with
the skills it claims to measure.

## The real run

`run_real_bench.py` hands each scenario's task to `claude -p` inside a throwaway
copy of its fixture project and records the turns, tokens, and wall-clock that
come back.

```
python .github/scripts/run_real_bench.py --out before.json
git checkout some-optimization
python .github/scripts/run_real_bench.py --out after.json --compare before.json
```

By default it loads the plugins straight from the working tree with
`--plugin-dir`, not from whatever version sits in the plugin cache. Without
that, every run would measure the last published release and a before/after
comparison would be meaningless. Pass `--installed` when you want to measure the
released version on purpose.

This one is deliberately not in CI. Wall-clock moves with API load and every run
spends tokens, so a gate built on it would fail at random and get ignored within
a week. Run it by hand to calibrate the budgets and to compare two revisions
against each other.

The `num_turns` it reports is the measured counterpart to `unbatched`. The static
gate can only model what the instructions permit; this shows what the model
actually did.

### Why the scenario prompts forbid running anything

Each task ends with an instruction not to install dependencies or run a build,
lint, or test command. The fixtures declare a test runner but ship no
`node_modules`, so without that line the model tries to install one, fails, and
retries. One early run burned 41 turns and 685 seconds on exactly that before
hitting the turn limit, which swamped the signal the benchmark exists to
measure.

So these numbers cover skill loading plus code generation, with toolchain
friction held out. That is the surface the skills control, and the right one for
an A/B. It is not the cost of a full task in a working repository, where
installing and running tests is part of the job.

A run that trips `--max-turns` still exits zero; only the `subtype` field in the
output gives it away. The harness checks that field, so a truncated run counts
as a failure instead of quietly becoming a data point. Partial failures are
reported as `N/M runs succeeded` with a warning, never averaged away in silence.

## Scenarios

Three sizes, each with a fixture project under `fixtures/` that carries just
enough signal for stack detection to fire.

| Scenario | Shape | Fixture |
|---|---|---|
| `small` | a pure utility function and its unit test | React + TypeScript |
| `medium` | a validated endpoint with persistence and tests | NestJS + PostgreSQL |
| `large` | an authenticated feature across API and frontend, with Docker and CI | NestJS + Next.js monorepo |

A scenario declares the skills it invokes and the triggers it activates. The
trigger keys come from `triggers.yaml`, which maps every routing condition in the
repository to a key and a scope. `task` scope means the condition is knowable
from the request alone; `project` scope means the repository has to be inspected
first, which forces a detection pass.

## Adding a scenario

1. Write `scenarios/<name>.yaml` with a `task`, the `skills` it invokes, and its
   `triggers`.
2. Build `fixtures/<name>/` with the manifest files the detection step reads.
3. Add a `<name>` block to `budgets.yaml`. Run the gate once to get the numbers,
   then set `max` to what you measured.

## What these numbers do not tell you

The token figure is an estimate at four characters per token, not a real
tokenizer count. That keeps the gate dependency-free, and for catching
regressions a consistent estimate is enough. When you need the true number,
the real run reports it, and the budgets can be recalibrated against it.

The fixtures are also minimal by design. They carry enough for the routing to
resolve, which is what these benchmarks measure. They are not a judgement of the
code the skills produce.
