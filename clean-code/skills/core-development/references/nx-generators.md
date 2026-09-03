# NX Generators

A generator turns a convention into code. It scaffolds files, wires up tags, and updates configuration the same way every time, so a new library looks like every other library without anyone remembering the checklist. The rules below assume NX 20.x and `@nx/devkit`.

## When to create one

- Any scaffolding you have done more than once. The second copy-paste is the signal.
- Enforcing conventions that are easy to forget: tags, project placement, test setup.
- Replacing a copy-paste ritual with a single command that cannot drift.

## File structure

- Put each generator in `src/generators/<name>/` with four files: `generator.ts`, `generator.spec.ts`, `schema.json`, and `schema.d.ts`.
- Register it in `generators.json` with its factory, schema, and a description.

```jsonc
{
  "generators": {
    "my-generator": {
      "factory": "./src/generators/my-generator/generator",
      "schema": "./src/generators/my-generator/schema.json",
      "description": "Generate a domain library with tags and tests"
    }
  }
}
```

## schema.json

- Set `"cli": "nx"`.
- Declare each option as a property with a `type` and a `description`.
- List the mandatory options under `required`.
- Give positional arguments a `$default` with `"$source": "argv"` so `nx g ... my-lib` fills them.
- Add `x-prompt` for options worth asking about interactively.
- Mark visibility with `x-priority: "important"` or `"internal"`, and offer a project picker with `x-dropdown: "projects"`.

```jsonc
{
  "$schema": "https://json-schema.org/schema",
  "cli": "nx",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Library name",
      "$default": { "$source": "argv", "index": 0 },
      "x-prompt": "What name do you want for the library?",
      "x-priority": "important"
    },
    "directory": {
      "type": "string",
      "description": "Target directory under libs/"
    }
  },
  "required": ["name"]
}
```

## Generator function

- Export a default `async function (tree: Tree, options)` built on `@nx/devkit`.
- Modify the virtual filesystem through `tree`: `read`, `write`, `exists`, `delete`. Never touch the real disk directly.
- Render templates with `generateFiles(tree, path, target, substitutions)`.
- Update JSON files with `updateJson(tree, path, updater)`.
- Always `await formatFiles(tree)` at the end.
- Return `() => installPackagesTask(tree)` only when you changed `package.json`. Otherwise return nothing.

```ts
import {
  Tree,
  formatFiles,
  generateFiles,
  installPackagesTask,
  updateJson,
} from "@nx/devkit";
import { join } from "node:path";
import type { MyGeneratorSchema } from "./schema";

export default async function (tree: Tree, options: MyGeneratorSchema) {
  const projectRoot = `libs/${options.directory ?? ""}/${options.name}`;

  generateFiles(tree, join(__dirname, "files"), projectRoot, {
    ...options,
    template: "",
  });

  updateJson(tree, `${projectRoot}/project.json`, (json) => {
    json.tags = [`scope:${options.name}`, "type:util"];
    return json;
  });

  await formatFiles(tree);
  return () => installPackagesTask(tree);
}
```

## Composing generators

- Call another generator by importing its default export and passing `tree` plus the options it expects.
- Never shell out to `nx generate` from inside a generator. That spawns a second process against the real filesystem and loses the shared `tree`.
- Prefer small, composable generators over one that does everything.

```ts
import libraryGenerator from "@nx/js/src/generators/library/library";

export default async function (tree: Tree, options: MyGeneratorSchema) {
  await libraryGenerator(tree, { name: options.name, directory: "libs" });
  // continue customizing the same tree
  await formatFiles(tree);
}
```

## Testing

- Build the workspace with `createTreeWithEmptyWorkspace()` from `@nx/devkit/testing`. Never test against the real filesystem.
- Assert that files exist and that their content is right.
- Assert the updates to `project.json` and `package.json`.
- Cover the edge cases: conflicting names, missing options, files that already exist.

```ts
import { Tree, readJson } from "@nx/devkit";
import { createTreeWithEmptyWorkspace } from "@nx/devkit/testing";
import generator from "./generator";

describe("my-generator", () => {
  let tree: Tree;

  beforeEach(() => {
    tree = createTreeWithEmptyWorkspace();
  });

  it("creates the library files", async () => {
    await generator(tree, { name: "my-lib" });
    expect(tree.exists("libs/my-lib/src/index.ts")).toBe(true);
  });

  it("tags the project by scope and type", async () => {
    await generator(tree, { name: "my-lib" });
    const project = readJson(tree, "libs/my-lib/project.json");
    expect(project.tags).toEqual(["scope:my-lib", "type:util"]);
  });
});
```

## Invocation

```bash
nx g @myorg/my-plugin:my-generator --name=my-lib
```

## Quick reference

| Do | Instead of |
|---|---|
| mutate through `tree` | write to the real filesystem |
| import and call a generator | shell out to `nx generate` |
| `await formatFiles(tree)` last | leave output unformatted |
| return `installPackagesTask` only if deps changed | return it unconditionally |
| `createTreeWithEmptyWorkspace()` in tests | a real workspace on disk |
| small composable generators | one generator that does everything |
