# Git and Gitflow

A branching model and commit discipline that keeps history readable and releases predictable. The rules assume the Gitflow model with Conventional Commits on top.

## Branches

Two branches live forever:

- `main` holds production. Every commit on it is a shipped release.
- `develop` is the integration branch. Finished work lands here first.

The rest are short-lived and deleted after merge:

- `feature/*` branches off `develop` and merges back into `develop`.
- `release/*` branches off `develop` to stabilize a version, then merges into both `main` and `develop`.
- `hotfix/*` branches off `main` to patch production, then merges into both `main` and `develop`.

Never commit directly to `main` or `develop`. Both change only through a reviewed merge.

## Branch naming

- `feat/<desc>` for a new capability.
- `fix/<desc>` for a bug fix.
- `chore/<desc>` for tooling, deps, and housekeeping.
- `docs/<desc>` for documentation-only work.
- `feat/#<issue>-<desc>` when the work ties to an issue; the issue number is mandatory there.

Keep the description short, lowercase, and hyphenated: `feat/#214-signup-rate-limit`.

## Commit messages

Follow Conventional Commits:

```
<type>(<scope>): <description>

[optional body: explain the why]

[optional footers]
```

- Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Scope names the affected area or project, and should match a real one.
- Description is imperative present tense, lowercase, no trailing period, under 72 characters. Write `add retry to fetch`, not `Added retry.`.
- Describe what changed, not how. The diff shows how.
- The body explains why the change was made and what it affects. Wrap it at a readable width.

## Breaking changes

- Mark a breaking change with `!` after the type or scope: `feat(api)!: drop legacy token endpoint`.
- Or add a footer: `BREAKING CHANGE: <description>`. Either form flags it for release tooling and reviewers.

## One concern per commit

- A commit does one thing. It should read as a single, revertible unit of intent.
- Do not mix a refactor with a feature, or a formatting sweep with a fix. Split them so review and `git revert` stay clean.

## Pull requests

- Follow the repository's PR template. Fill it in; do not delete sections.
- Link the related issue so the board and history stay connected.
- Keep the PR focused and small enough to review. A giant PR gets a shallow review.
- Do not merge your own PR without review. Review is the reviewer's responsibility, and the PR waits for it.

## Quick reference

| Branch | Off | Merges into | Purpose |
|---|---|---|---|
| `main` | n/a | n/a | Production releases |
| `develop` | n/a | n/a | Integration |
| `feature/*` | `develop` | `develop` | New work |
| `release/*` | `develop` | `main` + `develop` | Stabilize a version |
| `hotfix/*` | `main` | `main` + `develop` | Patch production |

| Commit type | Use for |
|---|---|
| `feat` | new user-facing capability |
| `fix` | bug fix |
| `docs` | documentation only |
| `refactor` | behavior-preserving change |
| `perf` | performance improvement |
| `test` | adding or fixing tests |
| `build` | build system or dependencies |
| `ci` | CI configuration |
| `chore` | housekeeping, no src/test change |
| `revert` | reverts a previous commit |
