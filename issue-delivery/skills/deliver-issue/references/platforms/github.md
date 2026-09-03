# GitHub

Adapter for delivering a single issue on GitHub. Load this when the project tracker is GitHub. The skill fetches the issue, branches, implements, tests, and opens a PR. This file provides the exact GitHub plumbing for each step of that lifecycle.

Golden rule: resolve every label, assignee, and Project field value against GitHub's real options before you use it. List them first. Never invent a value. Branch names and commit messages are owned by the clean-code git-gitflow rule; do not define naming here.

## Detection

Confirm GitHub is the tracker before proceeding.

```bash
git remote get-url origin              # host must be github.com
gh auth status                         # must report a logged-in, valid token
gh repo view --json nameWithOwner -q .nameWithOwner   # resolves {owner}/{repo}
```

Proceed only if the remote is on `github.com`, `gh` is installed, and `gh auth status` reports an authenticated account with repo write access.

Throughout, `{owner}` and `{repo}` are the values from detection, and `<n>` is the target issue number. Substitute real numbers and IDs; placeholders in angle brackets are not literal.

## Fetch and eligibility

Fetch the issue with the fields needed to judge eligibility.

```bash
gh issue view <n> --json number,title,body,state,assignees,labels,milestone,projectItems
```

Check every condition before touching the issue. Stop if any fails.

| Condition | Requirement |
| --- | --- |
| State | `state` is `OPEN`. |
| Assignment | `assignees` is empty, or contains the current user. |
| Ready | The Project board item sits in a To Do status, or the issue carries a ready label. |

Resolve the current user for the assignment check:

```bash
gh api user --jq .login
```

Resolve "ready" against real values, never a guessed one. Read the board status from `projectItems` in the fetch output, and confirm the ready label exists before relying on it:

```bash
gh label list --limit 200 --json name,description
```

If the issue is closed, assigned to someone else, or not in a ready state, stop and report why. Do not proceed.

## Assign and move to In Progress

Assign the issue to the current user:

```bash
gh issue edit <n> --add-assignee @me
```

Move the Project board item to In Progress. Resolve the Status field id and its option ids first; do not hardcode them.

```bash
gh project field-list <project-number> --owner {owner} --format json
```

Read the `Status` field's `id` and the `id` of its `In Progress` option from that output. Then edit the item. The `<item-id>` is the Project item id for this issue, available from the `projectItems` field of the fetch or from `gh project item-list`.

```bash
gh project item-edit \
  --project-id <project-id> \
  --id <item-id> \
  --field-id <status-field-id> \
  --single-select-option-id <in-progress-option-id>
```

## Branch

Create the working branch off the default base branch. Resolve the base branch; do not assume `main`.

```bash
gh repo view --json defaultBranchRef -q .defaultBranchRef.name   # resolves <base>
git fetch origin <base>
git switch -c <branch> origin/<base>
```

The `<branch>` name comes from the clean-code git-gitflow rule and is tied to the issue number `<n>`. Do not name it here.

## Implement and test

Implement the change on `<branch>`. Commit through the clean-code rule (naming and message format live there). Run the project's test and build tasks and keep them green before opening the PR. Push the branch:

```bash
git push -u origin <branch>
```

## Open the PR

Use the repository PR template if one exists. Check for it before writing a body:

```bash
ls .github/PULL_REQUEST_TEMPLATE.md .github/pull_request_template.md 2>/dev/null
```

Open the PR against the resolved base. The body must link the issue with a closing keyword (`Closes #<n>`) so merge auto-closes it. If a template exists, fill it and append the closing keyword.

```bash
gh pr create \
  --base <base> \
  --head <branch> \
  --title "<pr title>" \
  --body "$(cat <<'EOF'
## Summary
<what this PR changes and why>

## Testing
<commands run and their result>

Closes #<n>
EOF
)"
```

With a template present instead:

```bash
gh pr create --base <base> --head <branch> --title "<pr title>" \
  --body-file <filled-template-file>
```

Capture the PR URL from the command output for the board step.

## Link and move to review

The `Closes #<n>` keyword links the PR to the issue and closes it on merge; no separate link step is needed.

Move the Project item to the review status now that the PR is open. Resolve the option id first, as in the In Progress step, then edit the same item:

```bash
gh project item-edit \
  --project-id <project-id> \
  --id <item-id> \
  --field-id <status-field-id> \
  --single-select-option-id <review-option-id>
```

## Rules

- Never run `gh pr merge`. Merging is the reviewer's call.
- Never approve or request changes on the PR.
- Never invent a label, status, or field value. Resolve it against the live options first, and stop if the value does not exist.
- Never move an item to a Project status without resolving the field id and option id from `gh project field-list`.
- Stop and report if any eligibility condition fails rather than forcing the issue through.
