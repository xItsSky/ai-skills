---
name: core-development
description: Use when writing or reviewing code in any stack. It captures the cross-cutting engineering baseline shared by frontend and backend work. Covers TypeScript and JavaScript conventions, the unit-testing contract, git and gitflow, clean-code principles, and a security baseline. Referenced by frontend-development and backend-development.
---

# Core Development

Standards that hold regardless of framework. `frontend-development` and
`backend-development` point here for anything not stack-specific.

Read every row that applies **in a single message**, not one per turn. Take only
what the task needs.

| When you are | Read |
|---|---|
| Changing code at all: types, tests, security, git | `references/baseline.md` |
| Writing untyped JS | `references/javascript.md` |
| Structuring code or naming things | `references/clean-code.md` |
| Designing layers, boundaries, DI, or error handling | `references/architecture.md` |
| Writing doc comments or documenting a public API | `references/code-documentation.md` |
| Checking a framework version, EOL status, or a migration | `references/versioning-and-migration.md` |
| Working in an NX monorepo (`nx.json` present) | `references/nx.md` |
| Authoring a custom NX generator or executor | `references/nx-generators.md`, `references/nx-executors.md` |
| Writing a Dockerfile or image (`Dockerfile` present) | `references/docker.md` |
| Writing GitHub Actions CI workflows (`.github/workflows` present) | `references/github-actions.md` |

`baseline.md` carries the four things every task needs, so it is one read
instead of four. The rest of this directory goes deeper on one topic each and
loads only when the row matches.

## The contract, in one line each

- Types are strict. `any` is a bug; reach for `unknown` when a type is genuinely open.
- Every feature and fix ships with meaningful unit tests. Coverage floor is 80%.
- Work happens on a branch, never on `main` or `develop`.
- Untrusted input is validated before use. Secrets never reach the client or the repo.
- New dependencies are vetted before install. On known vulnerabilities, stop and get the user's approval.
