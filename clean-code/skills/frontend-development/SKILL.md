---
name: frontend-development
description: Use when writing, reviewing, or refactoring frontend or UI code (components, pages, templates, styling, client-side state, forms, or accessibility) in Angular, React, Next.js, Vue, or plain TypeScript/JavaScript. Also use for frontend testing and client-side performance work.
---

# Frontend Development

Load only the guidance that matches the project. Detect the framework first, read the one reference that fits, then pull in cross-cutting references as the task needs them. Do not read files for frameworks the project does not use.

## Step 1: Detect the framework

Before writing code, inspect the project:

1. Read `package.json` dependencies. Check `angular.json`, `next.config.*`, `vite.config.*`, or `.vue` files when present.
2. Match the strongest signal in the table. Read that one file.

| Signal in the project | Stack | Read |
|---|---|---|
| `@angular/core` | Angular | `references/angular.md` |
| `next` | Next.js | `references/nextjs.md` |
| `react` without `next` | React | `references/react.md` |
| `vue` | Vue | `references/vue.md` |
| TS/JS UI, no framework | Vanilla | core `references/typescript.md` (+ `javascript.md`) |

In a monorepo with several frontends, read the reference for each app whose files you actually touch, nothing more.

Then read the resolved framework version from the lockfile, not the caret range in `package.json`. Apply only the reference rules that match that version: a rule labelled for a newer version does not hold on an older project. For end-of-life status and upgrade proposals, see the `core-development` skill's `references/versioning-and-migration.md`.

## Step 2: Add cross-cutting references as the task requires

| When you are | Also read |
|---|---|
| Building or changing any UI | `references/accessibility.md` |
| Writing styles or a design system | `references/css-styling.md` |
| Writing or updating tests | `references/component-testing.md` + core `references/testing-philosophy.md` |
| Working on load time or runtime cost | `references/client-performance.md` |

## Step 3: Apply the shared baseline

For TypeScript rules, the testing contract, git workflow, and security, follow the `core-development` skill. Next.js Server Actions and Route Handlers are backend surface: for those, also read the `backend-development` skill (`api-design.md`, `auth-security.md`). In an NX monorepo (`nx.json` present), also read core `references/nx.md`. For layering and error-handling design, see core `references/architecture.md`.

## Non-negotiables

- Keep components small and single-purpose. Prefer composition over configuration flags.
- Compute derived values; store only what you cannot derive.
- Every UI change preserves keyboard access and semantics.
- Tests assert what the user observes, never internal calls.
- Before installing a dependency, vet it for known vulnerabilities. If any are found, report them and wait for approval. See core `references/security-baseline.md`.
- Detect the framework version and apply the rules that match it. Flag end-of-life versions and propose upgrades, but never change a version without approval.
