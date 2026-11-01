---
name: frontend-development
description: Use when writing, reviewing, or refactoring frontend or UI code (components, pages, templates, styling, client-side state, forms, or accessibility) in Angular, React, Next.js, Vue, or plain TypeScript/JavaScript. Also use for frontend testing and client-side performance work.
---

# Frontend Development

Detect once, read once, then write. Reading references one at a time is the
slowest thing this skill can do: each extra turn costs more than the file.

## Step 1: Detect everything in one command

```bash
find . -maxdepth 3 -name package.json -not -path '*/node_modules/*' -print -exec \
  grep -oE '"(@angular/core|next|react|vue|svelte|typescript)": *"[^"]*"' {} \;
find . -maxdepth 2 \( -name angular.json -o -name 'next.config.*' -o -name 'vite.config.*' \
  -o -name nx.json -o -name Dockerfile \) -print
find . -maxdepth 3 -name '*.vue' -not -path '*/node_modules/*' -print -quit
```

Never open a lockfile whole; they run to megabytes. For a resolved version, grep
the one package: `grep -m1 -A2 '"node_modules/react"' package-lock.json`. A rule
labelled for a newer version does not hold on an older project; for end-of-life
status and upgrades see core `references/versioning-and-migration.md`.

## Step 2: Read every match in one batch

Read all applicable rows **in a single message**. A one-component change needs
the framework row alone; a cross-cutting feature needs all of them. In a
monorepo, take only the rows for apps whose files you touch.

| Signal | Stack | Read |
|---|---|---|
| `@angular/core` | Angular | `references/angular.md` |
| `next` | Next.js | `references/nextjs.md` |
| `react` without `next` | React | `references/react.md` |
| `vue` | Vue | `references/vue.md` |
| TS/JS UI, no framework | Vanilla | core `references/typescript.md` (+ `javascript.md`) |

| When you are | Also read |
|---|---|
| Building or changing any UI | `references/accessibility.md` |
| Writing styles or a design system | `references/css-styling.md` |
| Writing or updating tests | `references/component-testing.md` + core `references/testing-philosophy.md` |
| Working on load time or runtime cost | `references/client-performance.md` |

Fold the shared baseline into the same batch: `core-development` for TypeScript,
testing, git, and security; core `references/nx.md` when `nx.json` appeared;
core `references/docker.md` when a `Dockerfile` did; core
`references/architecture.md` for layering and error handling. Next.js Server
Actions and Route Handlers are backend surface: for those, add the
`backend-development` skill's `api-design.md` and `auth-security.md` to the
batch.

## Non-negotiables

- Keep components small and single-purpose. Prefer composition over configuration flags.
- Compute derived values; store only what you cannot derive.
- Every UI change preserves keyboard access and semantics.
- Tests assert what the user observes, never internal calls.
- Vet a dependency before installing it. On a known vulnerability, stop and get approval. See core `references/security-baseline.md`.
- Apply the rules matching the detected version. Flag end-of-life versions and propose upgrades, but never change a version without approval.
