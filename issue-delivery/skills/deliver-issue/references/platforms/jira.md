# Jira

Adapter for delivering a single issue when the tracker is Jira. Load this when the project tracker is Jira. Jira owns the issue lifecycle: fetch, eligibility, assignment, and status transitions. The code and the pull request do not live on Jira. They live on the git host linked to the repository (GitHub or GitLab). This file covers the Jira plumbing and tells you where to hand off to the git host adapter for the branch and PR.

Core rule: resolve every value against Jira's actual configuration before you use it. Read the issue's real status and its available transitions, and drive the workflow with transition ids. Never invent a status name or force a transition that the workflow does not offer. Statuses, transitions, and fields differ per project.

## Detection and prerequisites

Two systems are in play. Detect both.

Jira access path, in this order of preference:

- CLI: run `jira version`. If it succeeds, the ankitpokhrel/jira-cli is installed. Prefer it.
- MCP: check for a connected Atlassian MCP server exposing tools such as `atlassian_getJiraIssue`, `atlassian_transitionJiraIssue`, `atlassian_searchJiraIssuesUsingJql`. Prefer it when the CLI is absent.
- REST: fall back to Jira Cloud REST API v3 with an API token when neither the CLI nor MCP is present.

Find the Jira target from config or env:

- Base URL: `JIRA_BASE_URL`, `ATLASSIAN_URL`, or a `jira.baseUrl` / `site` key in project config (for example `https://your-org.atlassian.net`).
- Project key: `JIRA_PROJECT`, `JIRA_PROJECT_KEY`, or a `jira.project` config key (for example `PROJ`).

```bash
echo "${JIRA_BASE_URL:?set JIRA_BASE_URL}"
echo "${JIRA_PROJECT:?set JIRA_PROJECT}"
```

Auth for the chosen path:

```bash
# CLI (ankitpokhrel/jira-cli): one-time setup, then verify identity
jira init          # writes ~/.config/.jira/.config.yml
jira me            # prints your account, used later for assignment

# REST (Jira Cloud v3, Basic auth with email + API token)
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="xxxx"          # create at id.atlassian.com API tokens
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/myself" | jq '{accountId, emailAddress, displayName}'
```

MCP: the Atlassian MCP server resolves the cloud id and site. Call `atlassian_getAccessibleAtlassianResources` (or the server equivalent) once to confirm the connection.

Git host for the code and PR. Detect it from the git remote and hand off the branch and PR steps to that host's adapter:

```bash
git remote get-url origin
```

| Remote host | Delivery steps for branch and PR |
| --- | --- |
| `github.com` | Use `github.md` (`gh pr create`, `gh` auth, PR template). |
| `gitlab.com` or a GitLab host | Use `gitlab.md` (`glab mr create`, `glab` auth, MR template). |

Jira never hosts the code or the PR. It tracks the issue only. Throughout this file `<KEY-123>` is the target issue key. Substitute the real key; placeholders in angle brackets are not literal.

## Fetch and eligibility

Fetch the issue, including its status and the transitions the workflow currently allows.

```bash
# CLI
jira issue view <KEY-123>

# REST: issue plus the available transitions from its current status
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/KEY-123?fields=summary,status,assignee,issuetype" \
  | jq '{key, status: .fields.status.name, assignee: .fields.assignee.accountId}'

curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/KEY-123/transitions" \
  | jq '.transitions[] | {id, name, to: .to.name}'
```

Check every condition before touching the issue. Stop if any fails.

| Condition | Requirement |
| --- | --- |
| Open | The issue is not Done, Closed, or otherwise resolved. |
| Assignment | `assignee` is empty, or is the current user (`jira me` / `/myself` accountId). |
| Ready | The current status is the board's ready status (To Do, Backlog, Selected for Development, or the project's equivalent). |

Read the current status from the fetch. Do not assume the ready status is literally "To Do"; use whatever the board names as the pre-work column. Confirm a real transition exists from that status toward In Progress before continuing. If the issue is resolved, assigned to someone else, or not in a ready status, stop and report why. Do not proceed.

## Assign and transition to In Progress

Assign the issue to the current user.

```bash
# CLI
jira issue assign <KEY-123> $(jira me)

# REST: set assignee by accountId (resolve your own via /myself)
ME=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/myself" | jq -r .accountId)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X PUT "$JIRA_BASE_URL/rest/api/3/issue/KEY-123/assignee" \
  -d "$(jq -n --arg id "$ME" '{accountId: $id}')"
```

Move the issue to In Progress by applying a real transition. List the transitions, find the one whose `to` status is the workflow's In Progress equivalent, and apply it by id. Never post a status name that is not in the list.

```bash
# CLI: interactive picker shows only valid transitions
jira issue move <KEY-123>
# Or non-interactive, naming a transition the list actually offers:
jira issue move <KEY-123> "In Progress"

# REST: read the transition id, then post it
TID=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/KEY-123/transitions" \
  | jq -r '.transitions[] | select(.to.name == "In Progress") | .id')
test -n "$TID" || { echo "no In Progress transition available; stop"; exit 1; }
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issue/KEY-123/transitions" \
  -d "$(jq -n --arg id "$TID" '{transition: {id: $id}}')"
```

If no transition reaches an In Progress status, stop. Do not create or rename a status.

## Branch

The branch lives on the git host, off the base branch. Create it there, not on Jira. Naming is owned by the clean-code git-gitflow rule; do not define it here. The name must include the Jira key so smart commits and the Jira git integration link the branch, commits, and PR back to the issue.

Resolve the base branch on the host, then branch:

```bash
git fetch origin <base>
git switch -c <branch> origin/<base>
```

The `<branch>` name comes from the clean-code git-gitflow rule and carries `<KEY-123>`. Follow that host's adapter (`github.md` or `gitlab.md`) for resolving `<base>` and pushing.

## Implement and test

Implement the change on `<branch>`. Commit through the clean-code rule; put the Jira key in every commit message (for example `KEY-123`) so the Jira development panel and smart commits pick it up. Run the project's test and build tasks and keep them green before opening the PR. Push the branch to the git host per that host's adapter.

## Open the PR or MR

The pull request lives on the git host. Jira does not host it. Open it with the host's flow and put the Jira key where the Jira git integration reads it: the branch name, the PR or MR title, and the commits. That is what wires the PR into the Jira development panel.

```bash
# GitHub (see github.md for template handling and base resolution)
gh pr create --base <base> --head <branch> \
  --title "KEY-123: <what changes>" \
  --body "<summary, testing, and any context>"

# GitLab (see gitlab.md for template handling and base resolution)
glab mr create --source-branch <branch> --target-branch <base> \
  --title "KEY-123: <what changes>" \
  --description "<summary, testing, and any context>"
```

There is no closing keyword for Jira. The link is made by the key appearing in the branch, title, and commits, plus the Jira git integration on the host. Capture the PR or MR URL from the command output; it appears in the Jira development panel once the integration syncs.

## Update Jira

After the PR or MR is open, move the issue to the review status. Resolve the transition by id exactly as in the In Progress step. The review status name varies (In Review, Code Review, To Be Reviewed, Review); read it from the transitions list, do not guess.

```bash
# REST: find and apply the transition into the review status
TID=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/KEY-123/transitions" \
  | jq -r '.transitions[] | select(.to.name | test("Review"; "i")) | .id' | head -n1)
test -n "$TID" || { echo "no review transition available; stop"; exit 1; }
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issue/KEY-123/transitions" \
  -d "$(jq -n --arg id "$TID" '{transition: {id: $id}}')"

# CLI equivalent (name a transition the list offers)
jira issue move <KEY-123> "In Review"
```

Sprint: set it only if the project uses sprints. Add the issue to the active sprint via the Agile API; skip this on a Kanban board with no sprints.

```bash
# Board id for the project
BOARD=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/agile/1.0/board?projectKeyOrId=$JIRA_PROJECT" \
  | jq -r '.values[] | select(.type=="scrum") | .id' | head -n1)
# Active sprint id
SPRINT=$(curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/agile/1.0/board/$BOARD/sprint?state=active" \
  | jq -r '.values[0].id')
# Add the issue
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/agile/1.0/sprint/$SPRINT/issue" \
  -d '{"issues": ["KEY-123"]}'
```

Story points and other fields, if the project uses them, go in the custom fields resolved the same way as in the epic-planning Jira adapter (`epic-planning/.../references/platforms/jira.md`, Metadata resolution): find the field id via `/rest/api/3/field`, then PUT it. Do not set a field the project does not have.

## Rules

- Never merge on the git host. Merging is the reviewer's call.
- Never force a transition that the workflow does not offer. List transitions, apply one by id, and stop if the target status is not reachable.
- Never invent a status, transition, or field. Resolve every one against the live Jira configuration first.
- Jira tracks the issue only. The branch, commits, and PR live on the git host resolved from the remote; drive them through `github.md` or `gitlab.md`.
- Put the Jira key in the branch, PR title, and commits so the development panel links them. Do not rely on a closing keyword; Jira has none.
- Stop and report if any eligibility condition fails rather than forcing the issue through.
```
