# NX

An NX workspace earns its keep through structure and caching. Get the boundaries and the target definitions right, and the tooling gives you fast builds, honest dependency graphs, and libraries that cannot import each other in ways they should not. The rules below assume NX 20.x and a monorepo with the project graph as the source of truth.

## Workspace structure

- Keep `apps/` and `libs/` separate. Apps wire things together; libs hold the code worth reusing. Never mix the two.
- Group libraries by domain scope: `libs/booking/`, `libs/shared/`. The folder tells you what the code is about before you open it.
- Do not nest projects more than two or three levels deep. Past that, the paths stop helping and start hiding.
- Move a project with `nx g move` and remove one with `nx g remove`. Both update references across the graph, which a manual `mv` will not.

## project.json

- Declare every task as a target with an explicit `executor` or `command`. An implicit task is one nobody can find later.
- Order dependencies with `dependsOn`. Use `["^build"]` to build a project's dependencies first, and `["build"]` to run this project's own build before the current target.
- Set `"cache": true` on any target whose output is a pure function of its inputs.
- Define `inputs` so the cache invalidates when a relevant file or env var changes, and `outputs` so NX knows what artifacts to restore.
- Point `outputs` at real artifact paths, for example `{workspaceRoot}/dist/libs/mylib`.
- Reuse `namedInputs` declared in `nx.json` instead of spelling out the same input set in every project.

```jsonc
{
  "name": "booking-data-access",
  "targets": {
    "build": {
      "executor": "@nx/js:tsc",
      "dependsOn": ["^build"],
      "cache": true,
      "inputs": ["production", "^production"],
      "outputs": ["{workspaceRoot}/dist/libs/booking/data-access"]
    }
  },
  "tags": ["scope:booking", "type:data-access"]
}
```

## Tags and module boundaries

- Tag every project with exactly two tags: a scope (`scope:booking`, `scope:shared`) and a type (`type:feature`, `type:ui`, `type:data-access`, `type:util`).
- Enforce the tags with the `@nx/enforce-module-boundaries` ESLint rule. Without enforcement, tags are just labels.
- Apply the type constraints so dependencies only flow downward:
  - `feature` may depend on `feature`, `ui`, `data-access`, `util`.
  - `ui` may depend on `ui`, `util`.
  - `data-access` may depend on `data-access`, `util`.
  - `util` may depend on `util` only.
- Cross a scope boundary only through `scope:shared`. One domain never reaches directly into another.

```jsonc
{
  "depConstraints": [
    { "sourceTag": "type:feature", "onlyDependOnLibsWithTags": ["type:feature", "type:ui", "type:data-access", "type:util"] },
    { "sourceTag": "type:ui", "onlyDependOnLibsWithTags": ["type:ui", "type:util"] },
    { "sourceTag": "type:data-access", "onlyDependOnLibsWithTags": ["type:data-access", "type:util"] },
    { "sourceTag": "type:util", "onlyDependOnLibsWithTags": ["type:util"] }
  ]
}
```

## Library types

- `feature`: containers, pages, and use cases. This is where the flow lives.
- `ui`: presentational components only. No business logic, no data fetching.
- `data-access`: API calls, state, and repositories.
- `util`: pure functions, helpers, and constants. Nothing stateful.

## Key commands

- `nx run <project>:<target>[:config]` runs one target, optionally with a configuration.
- `nx affected -t build [--base=main]` builds only the projects touched since the base.
- `nx run-many -t test --parallel=3` runs a target across projects with bounded concurrency.
- `nx graph` opens the project graph, and `nx affected:graph` shows just what changed.

## Caching and performance

- Make `inputs` cover every file and env var that affects the output. A missing input means a stale cache hit, which is worse than no cache.
- Exclude spec files from production build inputs with a negation: `!{projectRoot}/**/*.spec.ts`. Tests do not shape the build artifact.
- Use Nx Cloud for a distributed cache so the whole team and CI share results.
- Control concurrency with `--parallel`. More is not always faster once the machine is saturated.
- Mark long-running dev servers with `"continuous": true` so NX keeps them alive instead of waiting for them to exit.

## nx.json

- Put shared target config in `targetDefaults`: cache, inputs, outputs, and dependsOn. Set it once instead of repeating it in every project.
- Define reusable input sets as `namedInputs` and reference them by name from targets.

```jsonc
{
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "production": ["default", "!{projectRoot}/**/*.spec.ts"]
  },
  "targetDefaults": {
    "build": {
      "cache": true,
      "dependsOn": ["^build"],
      "inputs": ["production", "^production"],
      "outputs": ["{workspaceRoot}/dist/{projectRoot}"]
    }
  }
}
```

## Quick reference

| Do | Instead of |
|---|---|
| `apps/` and `libs/` separate | one folder for everything |
| `nx g move` / `nx g remove` | manual `mv` and delete |
| exactly two tags per project | untagged or over-tagged projects |
| `@nx/enforce-module-boundaries` on | tags with no enforcement |
| cross scopes via `scope:shared` | direct imports between domains |
| `targetDefaults` in nx.json | the same target config in every project |
| `namedInputs` referenced by name | inline input lists everywhere |
| `nx affected -t build` | rebuilding the whole workspace |
