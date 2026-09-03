# GitHub Actions

A workflow runs with credentials against your repository, so treat it as production code, not a config afterthought. Grant the least it needs, pin what it depends on, and never let a secret reach a log. The rules below cover authoring CI/CD workflows.

## Workflow and job structure

- Give each workflow one clear trigger and purpose. Split unrelated pipelines into separate files.
- Scope triggers with path and branch filters so a workflow runs only when relevant files change.
- Use `needs:` to order jobs and pass outputs between them. Keep independent jobs parallel.
- Set `timeout-minutes` on every job. The default is six hours; a stuck job burns runner minutes silently.

```yaml
on:
  push:
    branches: [main]
    paths: ["src/**", "package.json"]
  pull_request:
    paths: ["src/**"]

jobs:
  test:
    timeout-minutes: 15
```

## Least-privilege permissions

- Set `permissions:` explicitly. The repository default can be write-all, and an unset block inherits it.
- Deny everything at the workflow level, then grant the minimum each job needs.
- `GITHUB_TOKEN` is scoped by this block. Give a read-only job `contents: read` and nothing more.

```yaml
permissions: {}

jobs:
  build:
    permissions:
      contents: read
  release:
    permissions:
      contents: write
```

## Pinning action versions

- Prefer a full commit SHA. Tags are mutable: a `@v4` tag can be moved to point at new code, including a compromised release.
- If you must use a tag, pin at least the major version and know the tradeoff.
- Apply the same rule to reusable workflows referenced from other repositories.
- Let Dependabot bump the pinned SHAs so pinning does not mean going stale.

```yaml
# mutable: the tag can be repointed
uses: actions/checkout@v4

# immutable: locked to exact code
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

## Caching dependencies

- Key the cache on a lockfile hash so it invalidates when dependencies change, and add `restore-keys` for partial hits.
- Prefer the caching built into setup actions (`actions/setup-node`, `setup-python`) over hand-rolled `actions/cache`.
- Never cache secrets or credentials. Any workflow in the repo can read the cache.

```yaml
- uses: actions/setup-node@<sha>
  with:
    node-version: "20"
    cache: "npm"
```

## Matrix builds

- Use a matrix to run the same job across versions or platforms without duplicating it.
- Set `fail-fast: false` when you want every combination reported instead of cancelling on the first failure.
- Cap `max-parallel` when the matrix hits a rate-limited external service.
- Use `include` to tune a single combination without repeating the whole matrix.

```yaml
strategy:
  fail-fast: false
  matrix:
    node: ["18", "20", "22"]
```

## Reusable workflows and composite actions

- Use a reusable workflow (`workflow_call`) to share a whole multi-job pipeline across repositories. Secrets pass explicitly through `secrets:`.
- Use a composite action to package a sequence of steps that run inside one job.
- Pin reusable workflows from external repos to a full SHA, same as any action.

| | Reusable workflow | Composite action |
|---|---|---|
| Reuse unit | multi-job pipeline | steps within a job |
| Best for | shared CI across repos | packaging setup steps |
| Secrets | explicit via `secrets:` | via the calling job |

## Secrets handling

- Never echo a secret or print it to a log. Even a masked value can leak through encoding or partial output.
- Store one value per secret. Packing JSON into a secret defeats masking, which only matches the exact string.
- Do not pass secrets to untrusted third-party actions through the environment.
- Mask any sensitive value you generate at runtime before using it.
- Keep production secrets in a GitHub Environment, not at repo level, so they are injected only after protection rules pass.

```yaml
- run: |
    TOKEN=$(generate-token)
    echo "::add-mask::$TOKEN"
```

## GITHUB_TOKEN and cloud auth

- Prefer `GITHUB_TOKEN` over a personal access token for in-repo operations, and scope it with `permissions:`.
- For cloud providers, use OIDC instead of long-lived keys stored as secrets. The token is scoped to one job and expires on its own.
- Lock the OIDC trust policy to a specific repository, branch, and environment.

```yaml
permissions:
  id-token: write
  contents: read

- uses: aws-actions/configure-aws-credentials@<sha>
  with:
    role-to-assume: arn:aws:iam::123456789:role/GitHubActionsRole
    aws-region: eu-west-1
```

## Concurrency

- Set `concurrency:` on PR workflows to cancel a superseded run when a new commit lands, so you do not pay for stale work.
- Do not cancel in-progress runs on `main` or release branches; let deploys finish.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

## Untrusted pull requests

- Never use `pull_request_target` to check out and run code from a fork PR. It runs with base-branch context and full secret access, so a malicious PR can exfiltrate every secret.
- Use `pull_request_target` only for operations that do not execute PR code, such as labelling or commenting. Keep untrusted build and test in a separate workflow.

## Do / Instead of

| Do | Instead of |
|---|---|
| `permissions: {}` then grant per job | inherit write-all defaults |
| Pin to a commit SHA | `@v4` floating tag |
| `timeout-minutes` on every job | default six-hour timeout |
| Cache key on lockfile hash | unkeyed or manual cache |
| OIDC for cloud auth | long-lived keys in secrets |
| `echo "::add-mask::$TOKEN"` | print a generated secret |
| Environment for prod secrets | repo-level production secrets |
| `cancel-in-progress` on PRs | let superseded runs finish |
| Path and branch filters | run on every push |
| Separate untrusted PR jobs | `pull_request_target` running fork code |
