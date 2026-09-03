# Jira

This adapter tells the skill how to realise a drafted epic and its stories on Jira. The skill drafts using a generic model (Epic, Story, Task, Sub-task, Bug, Spike plus relations, metadata, and sprints). Map that model onto Jira's real configuration.

Core rule: resolve every value against Jira's actual options before you use it. List issue types, fields, priorities, components, versions, link types, and sprints first. Never invent an issue type, field id, link type, or value. When a generic relation has no native Jira equivalent, record it in the item body and state that you did so.

## Detection

Decide which access path is available, in this order of preference.

- CLI: run `jira version`. If it succeeds, the ankitpokhrel/jira-cli is installed. Prefer it.
- MCP: check for a connected Atlassian MCP server exposing tools such as `atlassian_createJiraIssue`, `atlassian_searchJiraIssuesUsingJql`, `atlassian_getJiraIssue`. Prefer it when the CLI is absent.
- REST: fall back to Jira Cloud REST API v3 with an API token when neither the CLI nor MCP is present.

Find the Jira target from config or env:

- Base URL: `JIRA_BASE_URL`, `ATLASSIAN_URL`, or a `jira.baseUrl` / `site` key in project config (for example `https://your-org.atlassian.net`).
- Project key: `JIRA_PROJECT`, `JIRA_PROJECT_KEY`, or a `jira.project` config key (for example `PROJ`).

```bash
echo "${JIRA_BASE_URL:?set JIRA_BASE_URL}"
echo "${JIRA_PROJECT:?set JIRA_PROJECT}"
```

## Prerequisites

Set up auth for the chosen path.

CLI (ankitpokhrel/jira-cli):

```bash
# One-time interactive setup writes ~/.config/.jira/.config.yml
jira init
# Verify auth and identity
jira me
```

REST (Jira Cloud v3, Basic auth with email + API token):

```bash
export JIRA_BASE_URL="https://your-org.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="xxxx"          # create at id.atlassian.com API tokens
export JIRA_PROJECT="PROJ"

# Verify auth
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/myself" | jq '{accountId, emailAddress, displayName}'
```

MCP: use the Atlassian MCP tools directly. The cloud id and site are resolved by the server; call `atlassian_getAccessibleAtlassianResources` (or the server equivalent) once to confirm the connection, then pass `projectKey`/`cloudId` to the create and search tools.

Give both a CLI example and a REST fallback for every operation below.

## Item type mapping

Available issue types are per project. List them (see next section) before mapping. Typical mapping:

| Generic type | Jira issue type |
|---|---|
| Epic | Epic |
| Story | Story |
| Task | Task |
| Sub-task | Sub-task (subtask; requires a parent) |
| Bug | Bug |
| Spike | Story or Task with a `spike` label, unless the project defines a Spike issue type |

Rules:

- If the project defines a native `Spike` type, use it. Otherwise create the Spike as a Story (or Task) and add the `spike` label.
- Sub-task always needs a parent issue; it cannot exist standalone.
- If a mapped type is missing from the project's create metadata, do not invent it. Pick the closest available type and note the substitution in the item body.

## Metadata resolution

List the real options first, then resolve each drafted value against them. Do not use any value that is not in these lists.

Issue types for the project:

```bash
# CLI
jira issuetype list --project "$JIRA_PROJECT"

# REST (createmeta scoped to the project)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/createmeta?projectKeys=$JIRA_PROJECT&expand=projects.issuetypes.fields" \
  | jq '.projects[].issuetypes[] | {id, name, subtask}'
```

Fields, including the Story Points custom field id:

```bash
# REST: find the custom field id for Story Points / Story point estimate
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/field" \
  | jq '.[] | select(.name | test("Story [Pp]oint")) | {id, name}'
# Typical results: "Story Points" -> customfield_10016, "Story point estimate" -> customfield_10016 (varies per site)
```

Record the resolved id, for example `export JIRA_STORY_POINTS_FIELD=customfield_10016`.

Priorities:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/priority" | jq '.[] | {id, name}'
```

Components:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/project/$JIRA_PROJECT/components" | jq '.[] | {id, name}'
```

Versions (for fix version):

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/project/$JIRA_PROJECT/versions" | jq '.[] | {id, name, released}'
```

Boards and sprints (Agile API, see Sprints section for full commands):

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/agile/1.0/board?projectKeyOrId=$JIRA_PROJECT" | jq '.values[] | {id, name, type}'
```

Metadata mapping:

| Generic metadata | Jira target |
|---|---|
| type | issue type name (resolved above) |
| priority | `priority` field (resolved name/id) |
| labels | `labels` (free text array, no spaces per label) |
| components | `components` (resolved ids) |
| assignee | `assignee.accountId` (look up via `/rest/api/3/user/search`) |
| fix version | `fixVersions` (resolved ids) |
| story points | resolved Story Points custom field |

Assignee lookup:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/user/search?query=jane@example.com" | jq '.[] | {accountId, displayName}'
```

## Create

Create the Epic, a Story under the Epic, and a Sub-task under the Story. The body carries Context, Business rules, Acceptance criteria, and Technical notes.

CLI:

```bash
# Epic
jira issue create \
  --project "$JIRA_PROJECT" \
  --type Epic \
  --summary "Checkout revamp" \
  --priority High \
  --label checkout --label q3 \
  --component "Payments" \
  --body "$(cat <<'EOF'
h2. Context
Why this epic exists.

h2. Business rules
- Rule one.

h2. Acceptance criteria
- Criterion one.

h2. Technical notes
- Note one.
EOF
)"
# Note the returned key, for example PROJ-100

# Story under the Epic (jira-cli uses --parent for the Epic Link on Story types)
jira issue create \
  --project "$JIRA_PROJECT" \
  --type Story \
  --parent PROJ-100 \
  --summary "Add express checkout button" \
  --priority Medium \
  --label checkout \
  --body "h2. Context
...
h2. Acceptance criteria
- ..."
# Returns PROJ-101

# Sub-task under the Story (--parent is the Story key)
jira issue create \
  --project "$JIRA_PROJECT" \
  --type Sub-task \
  --parent PROJ-101 \
  --summary "Wire up analytics event" \
  --body "h2. Technical notes
- ..."
```

REST (`POST /rest/api/3/issue`, body in Atlassian Document Format):

```bash
# Reusable ADF body builder: pass plain text sections, get an ADF doc.
adf () { jq -Rn --arg t "$1" '{type:"doc",version:1,content:[{type:"paragraph",content:[{type:"text",text:$t}]}]}'; }

# Epic
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issue" -d "$(jq -n \
    --arg project "$JIRA_PROJECT" \
    --argjson desc "$(adf 'Context: ...\nBusiness rules: ...\nAcceptance criteria: ...\nTechnical notes: ...')" '
    {fields:{
      project:{key:$project},
      issuetype:{name:"Epic"},
      summary:"Checkout revamp",
      priority:{name:"High"},
      labels:["checkout","q3"],
      description:$desc
    }}')" | jq '{key}'
# Returns PROJ-100

# Story under the Epic. On team-managed and current company-managed projects the
# Epic Link is the standard parent field. On older company-managed projects it is
# the Epic Link custom field (for example customfield_10014) discovered in step 4.
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issue" -d "$(jq -n \
    --arg project "$JIRA_PROJECT" \
    --argjson desc "$(adf 'Context: ...')" \
    --arg spf "$JIRA_STORY_POINTS_FIELD" '
    {fields:{
      project:{key:$project},
      issuetype:{name:"Story"},
      summary:"Add express checkout button",
      priority:{name:"Medium"},
      labels:["checkout"],
      parent:{key:"PROJ-100"},
      description:$desc
    } | .[$spf]=5 }')" | jq '{key}'
# Returns PROJ-101
# Fallback for legacy Epic Link field instead of parent:
#   "customfield_10014":"PROJ-100"

# Sub-task under the Story (parent is mandatory)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issue" -d "$(jq -n \
    --arg project "$JIRA_PROJECT" \
    --argjson desc "$(adf 'Technical notes: ...')" '
    {fields:{
      project:{key:$project},
      issuetype:{name:"Sub-task"},
      summary:"Wire up analytics event",
      parent:{key:"PROJ-101"},
      description:$desc
    }}')" | jq '{key}'
```

MCP: call the create-issue tool with `projectKey`, `issueTypeName`, `summary`, `description`, and a `parent` (or Epic Link field) for children.

## Relations

Two mechanisms: the parent field for parent/child, and native issue links for everything else.

Parent/child:

- Story under Epic: set the parent (Epic Link) field, at create time or by update. See Linking stories to the epic.
- Sub-task under Story: set `parent` at create time (required).

List available link types first:

```bash
# CLI
jira issuelinktype list   # if unavailable, use REST below

# REST
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issueLinkType" | jq '.issueLinkTypes[] | {name, inward, outward}'
```

Map the generic relations to native link types. Only use type names returned above.

| Generic relation | Jira link type | Direction |
|---|---|---|
| blocks | Blocks | outward "blocks" |
| blocked-by | Blocks | inward "is blocked by" |
| depends-on | Blocks | this issue "is blocked by" the dependency |
| needs | Blocks | this issue "is blocked by" what it needs |
| relates-to | Relates | "relates to" |
| duplicates | Duplicate | outward "duplicates" |

Convention: Jira has no native `needs`/`depends-on` type, so both map to `Blocks`. The item that needs or depends on another is the `is blocked by` (inward) side. State this convention in the body of the dependent item. If the site defines a `Dependency` link type, prefer it and note the choice.

Create a link:

```bash
# CLI: PROJ-101 is blocked by PROJ-105 (depends-on / needs)
jira issue link PROJ-101 PROJ-105 Blocks   # links inward/outward per the type

# REST: explicit direction. inwardIssue "is blocked by" outwardIssue.
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issueLink" -d '{
    "type": {"name": "Blocks"},
    "inwardIssue": {"key": "PROJ-101"},
    "outwardIssue": {"key": "PROJ-105"}
  }'

# relates-to
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issueLink" -d '{
    "type": {"name": "Relates"},
    "inwardIssue": {"key": "PROJ-101"},
    "outwardIssue": {"key": "PROJ-102"}
  }'

# duplicates
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/api/3/issueLink" -d '{
    "type": {"name": "Duplicate"},
    "inwardIssue": {"key": "PROJ-101"},
    "outwardIssue": {"key": "PROJ-099"}
  }'
```

No native equivalent: if a relation cannot be expressed with any available link type, record it in the item body (for example a line `Depends on: PROJ-105 (recorded in body; no native link type)`) and state explicitly that it was written to the body rather than linked.

## Sprints

Use the Agile API. Epics never go in a sprint; only stories (and their sub-tasks, implicitly) do. Story Points go in the custom field resolved in Metadata resolution.

```bash
# List boards for the project
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/agile/1.0/board?projectKeyOrId=$JIRA_PROJECT" \
  | jq '.values[] | {id, name, type}'
# Note the scrum board id, for example 42

# List active and future sprints on the board
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/agile/1.0/board/42/sprint?state=active,future" \
  | jq '.values[] | {id, name, state}'
# Note the target sprint id, for example 7

# Move stories into the sprint (max 50 issues per call)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X POST "$JIRA_BASE_URL/rest/agile/1.0/sprint/7/issue" \
  -d '{"issues": ["PROJ-101", "PROJ-102"]}'

# Set story points (resolved field)
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X PUT "$JIRA_BASE_URL/rest/api/3/issue/PROJ-101" -d "$(jq -n \
    --arg spf "$JIRA_STORY_POINTS_FIELD" '{fields: ({} | .[$spf]=5)}')"
```

CLI equivalents:

```bash
jira sprint list --board 42 --state active,future
jira sprint add 7 PROJ-101 PROJ-102        # add issues to a sprint
```

Do not add the Epic to any sprint. If the skill drafted a sprint for the epic, drop it and note the omission.

## Linking stories to the epic

Set the parent (Epic Link) at create time (shown in Create) or update it afterwards.

```bash
# CLI: attach an existing Story to an Epic
jira epic add PROJ-100 PROJ-101 PROJ-102

# REST: set the parent field on the Story
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X PUT "$JIRA_BASE_URL/rest/api/3/issue/PROJ-101" \
  -d '{"fields": {"parent": {"key": "PROJ-100"}}}'

# REST fallback for legacy company-managed Epic Link custom field
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Content-Type: application/json" \
  -X PUT "$JIRA_BASE_URL/rest/api/3/issue/PROJ-101" \
  -d '{"fields": {"customfield_10014": "PROJ-100"}}'
```

Verify the link:

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROJ-101?fields=parent,summary" | jq '.fields.parent'
```
