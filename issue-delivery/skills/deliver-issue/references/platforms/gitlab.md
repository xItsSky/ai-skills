# GitLab

Adapter for delivering an issue on GitLab. Load this when the project tracker is GitLab. The skill fetches an issue, branches, implements, tests, and opens a merge request. This file provides the exact GitLab plumbing with `glab`, and a REST fallback via `glab api` where the CLI lacks a subcommand.

Golden rule: resolve every label, assignee, milestone, and iteration against GitLab's real options before you use it. List them first with `glab label list`. Never invent a value. Branch naming and commit messages are not decided here; the clean-code git-gitflow rule owns them.

Throughout, `<n>` is the issue number and `<base>` is the default branch. `:id` in an API path is the URL-encoded project path (for example `mygroup%2Fmyrepo`) or the numeric project ID. Substitute real values; placeholders in angle brackets are not literal.

## Detection and prerequisites

Confirm GitLab is the tracker before proceeding.

```bash
git remote get-url origin        # host must be gitlab.com or a self-managed GitLab
glab auth status                 # must report a logged-in, valid token
glab repo view -F json           # resolves the project path and default branch
```

Proceed only if:

- The `origin` host is `gitlab.com` or your self-managed GitLab instance. For self-managed, `glab` must be configured for that host (`glab auth status` lists it, or set `GITLAB_HOST`).
- `glab` is installed and `glab auth status` reports an authenticated account with `api` and `write_repository` scope.
- You can resolve the project path (`group/subgroup/repo`). Read it from `glab repo view -F json` or from the `origin` URL.

Resolve the default base branch once and reuse it:

```bash
BASE=$(glab api projects/:id --jq '.default_branch')   # e.g. main
```

## Fetch and eligibility

Read the issue in two forms: a human view and the full JSON for programmatic checks.

```bash
glab issue view <n>                          # human-readable summary
glab api projects/:id/issues/<n>             # full JSON: state, assignees, labels, milestone
```

Confirm every condition below before touching the code. If any fails, stop and report why.

- The issue is open: `.state == "opened"`.
- The issue is unassigned or assigned to the current user. Compare `.assignees[].username` against your username (`glab api user --jq '.username'`).
- The issue is in a ready state. GitLab boards are label-driven or iteration-driven, so "ready" is a scoped board label the project uses (for example `status::ready`) or the project's documented workflow. Check `.labels` for it.

Do not proceed on a closed issue, an issue assigned to someone else, or an issue that is not yet marked ready.

## Assign and status

Assign the issue to yourself:

```bash
glab issue update <n> --assignee @me
```

API fallback:

```bash
glab api --method PUT projects/:id/issues/<n> \
  --field assignee_ids=<your-user-id>
```

Move the board status by swapping the scoped label. GitLab boards are columns of scoped labels (`status::*`), so a card moves when its scoped label changes. Only one label of a given scope can be set at a time.

```bash
glab issue update <n> --label "status::doing" --unlabel "status::todo"
```

API fallback (use `add_labels` / `remove_labels` to avoid clobbering unrelated labels):

```bash
glab api --method PUT projects/:id/issues/<n> \
  --field add_labels="status::doing" \
  --field remove_labels="status::todo"
```

Resolve the real scope names first (see Rules). Do not assume `status::todo` or `status::doing` exist; the project may use `workflow::*`, `state::*`, or another scope.

## Branch

Create the branch off the default base branch. The branch name comes from the clean-code git-gitflow rule and is tied to the issue; do not choose it here.

```bash
git fetch origin
git switch -c <branch> origin/<base>
```

GitLab can also create a branch straight from an issue (the "Create merge request" / "Create branch" action, or the API below), which auto-links it. A plain local branch is fine for this workflow; the MR's closing pattern provides the link.

Optional server-side branch creation from the issue:

```bash
glab api --method POST projects/:id/repository/branches \
  --field branch=<branch> \
  --field ref=<base>
```

## Open the merge request

Open the MR from your branch into the base branch. Put `Closes #<n>` in the description so merging the MR closes the issue and links it automatically.

```bash
glab mr create \
  --source-branch <branch> \
  --target-branch <base> \
  --title "<mr title>" \
  --description "$(cat <<'EOF'
## Summary
<what this MR does and why>

## Changes
- <change 1>
- <change 2>

## Testing
<tests added or run>

Closes #<n>
EOF
)"
```

If the project ships an MR template under `.gitlab/merge_request_templates/`, follow it: fill its sections instead of the block above and keep the `Closes #<n>` line so the issue still closes on merge.

Push the branch first if the MR create step does not push for you:

```bash
git push -u origin <branch>
```

## Link and board

- The `Closes #<n>` line links the MR to the issue and closes the issue when the MR merges. No separate link step is needed.
- After the MR is open, move the board status to the review state by swapping the scoped label:

```bash
glab issue update <n> --label "status::review" --unlabel "status::doing"
```

- Set milestone or iteration only if the project uses them. Resolve the real values first, then apply:

```bash
# Milestone (by title)
glab issue update <n> --milestone "<milestone-title>"

# Iteration (no CLI flag; use the API with a resolved iteration id)
glab api --method PUT projects/:id/issues/<n> \
  --field iteration_id=<iteration-id>
```

List available iterations for the group to resolve the id:

```bash
glab api "groups/<group-id>/iterations?state=opened" \
  --jq '.[] | {id, title, start_date, due_date}'
```

Skip milestone and iteration entirely if the project does not use them.

## Rules

- Never run `glab mr merge`. Merging is the reviewer's call.
- Never approve the MR (`glab mr approve`). You are the author.
- Never invent labels. Resolve the real scoped labels the project uses before setting or unsetting any:

```bash
glab label list --per-page 200
```

- Use the exact label names from that list. If the expected `status::*` (or equivalent) scope is absent, stop and report it rather than creating one.
- Keep one label per scope. Swapping (add one, remove the other) is what moves a board card; setting a second label of the same scope is invalid.
