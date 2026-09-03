# GitHub

Adapter for realising the generic epic model on GitHub. Load this when the project tracker is GitHub. The skill has already drafted the epic and its stories against the generic model. This file maps that model to real GitHub constructs using `gh`.

Golden rule: resolve every label, milestone, assignee, and Project field value against GitHub's real options before you use it. List them first. Never invent a value. When a relation has no native GitHub equivalent, record it in the item body and state that you did so.

## Detection

Confirm GitHub is the tracker before proceeding.

```bash
git remote get-url origin              # host must be github.com
gh auth status                         # must report a logged-in, valid token
gh repo view --json nameWithOwner -q .nameWithOwner   # resolves {owner}/{repo}
```

Proceed only if the remote is on `github.com`, `gh` is installed, and `gh auth status` reports an authenticated account with repo scope.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`).
- Repo write access for creating issues, labels, and milestones.
- For iterations and custom fields: access to a GitHub Projects v2 board and its project number.
- GitHub has no native "Epic" or "Story" issue type. Express work item types with labels, and optionally mirror them in a Project single-select field (for example `Type`). Parent/child uses native sub-issues.

Throughout, `{owner}` and `{repo}` are the values from detection. Substitute real numbers and IDs; the placeholders in angle brackets are not literal.

## Item type mapping

Map each generic type to a `type:*` label. Create the labels once if they do not already exist (see Metadata resolution before creating anything).

| Generic type | GitHub label | Structure |
| --- | --- | --- |
| Epic | `type:epic` | Parent issue; owns stories via sub-issues |
| Story | `type:story` | Sub-issue of the epic |
| Task | `type:task` | Standalone or sub-issue of a story |
| Sub-task | `type:subtask` | Native sub-issue, or a task list checkbox on its parent |
| Bug | `type:bug` | Issue with `type:bug` |
| Spike | `type:spike` | Issue with `type:spike` |

Rules:
- Parent/child (Epic to Story, Story to Sub-task) uses the native sub-issues API.
- Sub-tasks may instead be task list checkboxes in the parent body when they are too small to warrant their own issue. Pick one approach per parent and stay consistent.
- If the board carries a `Type` single-select field, set it to match the label after adding the item to the project.

## Metadata resolution

List the real options before assigning any value. Do not assign a value that is absent from these outputs; create the label or milestone first, or pick an existing option.

Labels (type, priority, area/domain):

```bash
gh label list --limit 200 --json name,color,description
```

Milestones:

```bash
gh api /repos/{owner}/{repo}/milestones --jq '.[] | {number, title, state}'
```

Assignees (valid users for this repo):

```bash
gh api /repos/{owner}/{repo}/assignees --jq '.[].login'
```

Project custom fields (Priority, Status, Iteration, Type) and their option IDs:

```bash
gh project field-list <project-number> --owner {owner} --format json
```

Create a missing label instead of inventing one inline:

```bash
gh label create "type:epic" --color 5319E7 --description "Epic work item"
gh label create "prio:p1"   --color D93F0B --description "Priority P1"
gh label create "area:api"  --color 0E8A16 --description "Area: API"
```

Create a missing milestone when the target does not exist:

```bash
gh api --method POST /repos/{owner}/{repo}/milestones -f title="<milestone-title>"
```

Metadata to resolve per item: type (label), priority (label such as `prio:p1` and/or a Project `Priority` field), labels (area/domain such as `area:api`), assignee (from the assignees list), milestone (from the milestones list), area/domain (label).

## Create

### Epic

Body template sections: Context, Business rules, Acceptance criteria, Technical notes. The epic never receives an iteration.

```bash
gh issue create \
  --title "Epic: <epic title>" \
  --label "type:epic,area:<x>,prio:<p1>" \
  --milestone "<milestone-title>" \
  --body "$(cat <<'EOF'
## Context
<why this epic exists, scope, out of scope>

## Business rules
<rules and constraints that govern the work>

## Acceptance criteria
- [ ] <epic-level outcome 1>
- [ ] <epic-level outcome 2>

## Technical notes
<architecture, dependencies, risks>

## Stories
<!-- filled in the Linking section as sub-issues are created -->
EOF
)"
```

Capture the epic number from the created issue URL for the relations step.

### Story

Create each story as its own issue, then attach it to the epic as a sub-issue (see Relations).

```bash
gh issue create \
  --title "<story title>" \
  --label "type:story,area:<x>,prio:<p2>" \
  --assignee "<login>" \
  --milestone "<milestone-title>" \
  --body "$(cat <<'EOF'
## Context
<user-facing goal and where it sits in the epic>

## Business rules
<rules specific to this story>

## Acceptance criteria
- [ ] <testable criterion 1>
- [ ] <testable criterion 2>

## Technical notes
<implementation pointers, affected modules>

## Relations
<!-- non-native relations recorded here, see Relations -->
EOF
)"
```

Sub-tasks that warrant their own issue follow the same pattern with `type:subtask`, attached to their story.

## Relations

### Parent/child (native)

Use the sub-issues API. `sub_issue_id` is the numeric issue number of the child.

```bash
gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/issues/<parent-number>/sub_issues \
  -f sub_issue_id=<child-issue-number>
```

Fallback when sub-issues are unavailable or the child is a lightweight checkbox: add a task list to the parent body.

```markdown
## Sub-tasks
- [ ] #<child-number> <short label>
```

### Non-native relations

GitHub has no first-class type for needs, depends-on, blocks / blocked-by, relates-to, or duplicates. Record each one in the item body under a `Relations` heading using a stated convention, and note in your summary that these are body conventions, not enforced links.

Convention:

| Generic relation | Body line |
| --- | --- |
| depends-on / needs | `Depends on #<n>` |
| blocks | `Blocks #<n>` |
| blocked-by | `Blocked by #<n>` |
| relates-to | `Relates to #<n>` |
| duplicates | `Duplicates #<n>` |

Example body block:

```markdown
## Relations
Blocked by #12
Depends on #9
Relates to #14
```

State explicitly wherever you apply these that GitHub does not enforce them and they exist only as references in the body.

## Sprints/iterations

Iterations live on a GitHub Projects v2 board as an Iteration field. Only stories (and their sub-tasks) may be placed in an iteration. The epic never gets one.

List iterations and field IDs:

```bash
gh project field-list <project-number> --owner {owner} --format json
```

Read the Iteration field's `id` and, from its configuration, the target iteration's `id`.

Add the story to the project, then set its iteration:

```bash
# Add the item, capture its item id from the output
gh project item-add <project-number> --owner {owner} --url <story-issue-url>

# Set the iteration
gh project item-edit \
  --project-id <project-id> \
  --id <item-id> \
  --field-id <iteration-field-id> \
  --iteration-id <iteration-id>
```

Set a single-select field (Priority, Status, Type) on the same item:

```bash
gh project item-edit \
  --project-id <project-id> \
  --id <item-id> \
  --field-id <field-id> \
  --single-select-option-id <option-id>
```

Do not run any of the above against the epic item's iteration field.

## Linking stories to the epic

Link each story to the epic in two ways so the relationship is both structural and visible.

1. Attach the story as a native sub-issue of the epic:

```bash
gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/issues/<epic-number>/sub_issues \
  -f sub_issue_id=<story-number>
```

2. Add the story to the epic body's `## Stories` checklist so progress is readable at a glance:

```markdown
## Stories
- [ ] #<story-1> <short label>
- [ ] #<story-2> <short label>
```

Edit the epic body to append each story as it is created:

```bash
gh issue edit <epic-number> --body-file <updated-body-file>
```
