# NX Executors

An executor is a target's implementation. It takes typed options and a context, does the work, and reports success or failure so NX can cache the result and slot it into the graph. Write one when a raw script has outgrown what a `command` can express. The rules below assume NX 20.x and `@nx/devkit`.

## When to create one

- A build, deploy, lint, or test script that needs `--help`, NX Console integration, or caching.
- Wrapping a CLI so it exposes standard, typed options instead of a wall of flags.
- Composing several targets into one coordinated run.

## File structure

- Put each executor in `src/executors/<name>/` with four files: `executor.ts`, `executor.spec.ts`, `schema.json`, and `schema.d.ts`.
- Register it in `executors.json` with its implementation, schema, and a description.

```jsonc
{
  "executors": {
    "my-executor": {
      "implementation": "./src/executors/my-executor/executor",
      "schema": "./src/executors/my-executor/schema.json",
      "description": "Build the project with our conventions"
    }
  }
}
```

## schema.json

- Set `"cli": "nx"`.
- Give every option a `type` and a `description`.
- List the mandatory options under `required`.
- Provide sensible defaults so the common case needs no flags.

```jsonc
{
  "$schema": "https://json-schema.org/schema",
  "cli": "nx",
  "type": "object",
  "properties": {
    "outputPath": {
      "type": "string",
      "description": "Directory for build artifacts",
      "default": "dist"
    },
    "watch": {
      "type": "boolean",
      "description": "Rebuild on file changes",
      "default": false
    }
  },
  "required": ["outputPath"]
}
```

## Executor function

- Export a default `async function executor(options, context: ExecutorContext): Promise<{ success: boolean }>`.
- Read the current project from `context.projectsConfigurations.projects[context.projectName].root`.
- Always return `{ success }`. Return `{ success: false }` on error and never throw. NX reads the return value, not exceptions.
- Use `context.projectName`, `context.targetName`, and `context.configurationName` rather than re-deriving them.
- Log with `console.log` and `console.error`. Never call `process.exit()`; it kills the NX run.

```ts
import type { ExecutorContext } from "@nx/devkit";
import type { MyExecutorSchema } from "./schema";

export default async function executor(
  options: MyExecutorSchema,
  context: ExecutorContext,
): Promise<{ success: boolean }> {
  const projectName = context.projectName;
  if (!projectName) {
    console.error("No project in context");
    return { success: false };
  }

  const root = context.projectsConfigurations.projects[projectName].root;

  try {
    await build(root, options.outputPath);
    return { success: true };
  } catch (error) {
    console.error(`Build failed: ${(error as Error).message}`);
    return { success: false };
  }
}
```

## Composing executors

- Run another target with `runExecutor({ project, target }, {}, context)`. It returns an async iterable, so consume it with `for await`.
- Parse a target string with `parseTargetString(...)`.
- Read another target's options with `readTargetOptions(target, context)`.

```ts
import { parseTargetString, runExecutor } from "@nx/devkit";

const target = parseTargetString("my-app:build:production", context);

for await (const result of await runExecutor(target, {}, context)) {
  if (!result.success) {
    return { success: false };
  }
}
```

## Caching

- Set `"cache": true` on the target that uses the executor.
- Declare `inputs` and `outputs` so NX can hash and restore correctly.
- Write a custom `hasher.ts` only when the default file hashing is not enough. Scaffold it with `--includeHasher`.

## Testing

- Build an `ExecutorContext` object by hand for the test.
- Mock the external CLI and any filesystem side effects.
- Test both the success path and the `{ success: false }` path.
- Assert that outputs land at the declared path.

```ts
import type { ExecutorContext } from "@nx/devkit";
import executor from "./executor";

const context: ExecutorContext = {
  root: "/workspace",
  projectName: "my-app",
  targetName: "build",
  cwd: "/workspace",
  isVerbose: false,
  projectsConfigurations: {
    version: 2,
    projects: { "my-app": { root: "apps/my-app" } },
  },
} as ExecutorContext;

describe("my-executor", () => {
  it("returns success on a clean build", async () => {
    const result = await executor({ outputPath: "dist", watch: false }, context);
    expect(result.success).toBe(true);
  });

  it("returns success false when the build throws", async () => {
    const result = await executor({ outputPath: "", watch: false }, context);
    expect(result.success).toBe(false);
  });
});
```

## Invocation

```bash
nx run <project>:my-executor[:production]
```

## Quick reference

| Do | Instead of |
|---|---|
| return `{ success: false }` | `throw` on error |
| `console.log` / `console.error` | `process.exit()` |
| read project from `context` | re-derive paths by hand |
| `runExecutor` with `for await` | shell out to `nx run` |
| build an `ExecutorContext` in tests | run against a real workspace |
| custom `hasher.ts` only when needed | override hashing by default |
