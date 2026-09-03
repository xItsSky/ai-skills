---
name: core-development
description: Use when writing or reviewing code in any stack. It captures the cross-cutting engineering baseline shared by frontend and backend work. Covers TypeScript and JavaScript conventions, the unit-testing contract, git and gitflow, clean-code principles, and a security baseline. Referenced by frontend-development and backend-development.
---

# Core Development

Standards that hold regardless of framework. The `frontend-development` and `backend-development` skills point here for anything that is not stack-specific. Read only the file that matches what you are doing.

## References

| When you are | Read |
|---|---|
| Writing typed code | `references/typescript.md` |
| Writing untyped JS | `references/javascript.md` |
| Writing or reviewing any unit test | `references/testing-philosophy.md` |
| Branching, committing, or opening a PR | `references/git-gitflow.md` |
| Structuring code or naming things | `references/clean-code.md` |
| Writing doc comments or documenting a public API | `references/code-documentation.md` |
| Checking a framework version, EOL status, or a migration | `references/versioning-and-migration.md` |
| Handling input, secrets, or trust boundaries | `references/security-baseline.md` |
| Adding or upgrading a dependency | `references/security-baseline.md` |

## The contract, in one line each

- Types are strict. `any` is a bug; reach for `unknown` when a type is genuinely open.
- Every feature and fix ships with meaningful unit tests. Coverage floor is 80%. See `testing-philosophy.md`.
- Work happens on a branch, never on `main` or `develop`. See `git-gitflow.md`.
- Untrusted input is validated before use. Secrets never reach the client or the repo.
- New dependencies are vetted before install. On known vulnerabilities, stop and get the user's approval. See `security-baseline.md`.
