# Trello

Realise the generic epic/story model on Trello. Trello has cards, lists, checklists, and labels only. It has no issue types and no native issue links, so map honestly and state each convention as you apply it.

Golden rule: resolve every value (label, list, member) against the board's real options. List them first. Never invent a label or a list.

## Detection

Trello has no git remote signal. Treat it as the tracker when one of these is present:

- A board id or board URL in project config or passed as a parameter.
- A Trello API key and token in config or env.

Board id sources:

- URL form `https://trello.com/b/<shortId>/<slug>` gives the short id in `<shortId>`.
- Resolve the short id to the full id with `GET /boards/<shortId>`.

```bash
# Extract the short id from a board URL and resolve the full board id.
BOARD_URL="https://trello.com/b/AbCdEfGh/my-board"
SHORT_ID=$(printf '%s' "$BOARD_URL" | sed -E 's#.*/b/([^/]+).*#\1#')
curl -s "https://api.trello.com/1/boards/${SHORT_ID}?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.id'
```

If no board is configured, ask the user for the board id or URL. This tracker is usually named by the user or passed as a parameter.

## Prerequisites

- Base URL: `https://api.trello.com/1`.
- Trello API key: get it from `https://trello.com/app-key`.
- Trello token: generate it from the same page (authorize the key), scoped to read and write.
- Pass both on every call as query params `key` and `token`.

```bash
export TRELLO_KEY="<your-key>"
export TRELLO_TOKEN="<your-token>"
export TRELLO_BOARD="<full-board-id>"

# Sanity check: the token must resolve to a member.
curl -s "https://api.trello.com/1/members/me?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.username'
```

Optional: a `trello` CLI (for example `trello-cli`) can wrap these calls. It still needs the same key and token. Examples below use `curl` so they are runnable without extra tooling.

## Item type mapping

Trello has no work item types. Adopt these conventions and keep them consistent:

| Generic type | Trello realisation |
|---|---|
| Epic | A dedicated card that gathers the feature, holding a checklist of Story links. |
| Story | A card. |
| Task | A card, or a checklist item on the Story card for small tasks. |
| Sub-task | A checklist item on its Story card. |
| Bug | A card tagged with a `Bug` label. |
| Spike | A card tagged with a `Spike` label. |

Conventions adopted here:

- Epic is a card, not a list. This keeps epics addressable by URL so Story cards can attach them.
- Type is carried by a label (`Bug`, `Spike`, `Story`, and so on) because Trello has no type field.
- A Task is a card when it needs its own assignee, due date, or labels; otherwise it is a checklist item.

## Metadata resolution

List the board's real options before setting anything. Match requested values to these by name. If a value has no match, stop and ask; do not create labels or lists silently.

```bash
# Labels: id, name, and colour.
curl -s "https://api.trello.com/1/boards/${TRELLO_BOARD}/labels?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.[] | "\(.id)\t\(.color)\t\(.name)"'

# Lists (columns): id and name.
curl -s "https://api.trello.com/1/boards/${TRELLO_BOARD}/lists?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.[] | "\(.id)\t\(.name)"'

# Members: id, username, full name.
curl -s "https://api.trello.com/1/boards/${TRELLO_BOARD}/members?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.[] | "\(.id)\t\(.username)\t\(.fullName)"'
```

Mapping rules:

- Priority maps to a label (for example `Priority: High`). Use the real label whose name matches; do not invent one.
- Type maps to a label (`Bug`, `Spike`, `Story`).
- Assignee maps to board members (`idMembers`), resolved by username to member id.
- Due date maps to the card `due` field (ISO 8601, for example `2026-09-30T17:00:00.000Z`).
- Labels map to board labels by name.

## Create

Create the Epic card, a Story card, and a Sub-task as a checklist item. Put Context, Business rules, and Acceptance criteria in the card `desc`. Acceptance criteria can also be a checklist for tracking.

```bash
# 1. Create the Epic card on the target list.
EPIC_ID=$(curl -s -X POST "https://api.trello.com/1/cards?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "idList=${LIST_ID}" \
  --data-urlencode "name=[Epic] Checkout revamp" \
  --data-urlencode "desc=## Context
Rework the checkout flow.

## Business rules
- Guest checkout stays available.

## Acceptance criteria
- [ ] Payment succeeds end to end." \
  | jq -r '.id')

# 2. Create a Story card.
STORY_ID=$(curl -s -X POST "https://api.trello.com/1/cards?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "idList=${LIST_ID}" \
  --data-urlencode "name=Add express checkout button" \
  --data-urlencode "desc=## Context
One-click express checkout.

## Acceptance criteria
- [ ] Button shows on the cart page." \
  | jq -r '.id')

# 3. Set labels (type, priority) on the Story card. Repeat per label id.
curl -s -X POST "https://api.trello.com/1/cards/${STORY_ID}/idLabels?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "value=${STORY_LABEL_ID}"
curl -s -X POST "https://api.trello.com/1/cards/${STORY_ID}/idLabels?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "value=${PRIORITY_HIGH_LABEL_ID}"

# 4. Assign a member.
curl -s -X POST "https://api.trello.com/1/cards/${STORY_ID}/idMembers?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "value=${MEMBER_ID}"

# 5. Set a due date.
curl -s -X PUT "https://api.trello.com/1/cards/${STORY_ID}?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "due=2026-09-30T17:00:00.000Z"

# 6. Add a Sub-task as a checklist item on the Story card.
CHECKLIST_ID=$(curl -s -X POST "https://api.trello.com/1/checklists?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "idCard=${STORY_ID}" \
  --data-urlencode "name=Sub-tasks" \
  | jq -r '.id')

curl -s -X POST "https://api.trello.com/1/checklists/${CHECKLIST_ID}/checkItems?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "name=Wire the button to the payment API"
```

Acceptance criteria as a checklist (optional, in addition to the description):

```bash
AC_ID=$(curl -s -X POST "https://api.trello.com/1/checklists?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "idCard=${STORY_ID}" \
  --data-urlencode "name=Acceptance criteria" \
  | jq -r '.id')
curl -s -X POST "https://api.trello.com/1/checklists/${AC_ID}/checkItems?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "name=Button shows on the cart page"
```

## Relations

Trello has no native issue links. These are conventions, not native links. State each one in the card description so it survives outside the API.

Map parent/child two ways, use both:

- The Epic card holds a checklist whose items are Story card links (see Linking stories to the epic).
- Attach the related card URL with `POST /cards/{id}/attachments`.

```bash
# Attach a related card by URL (works for parent/child and cross-card relations).
curl -s -X POST "https://api.trello.com/1/cards/${STORY_ID}/attachments?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "url=https://trello.com/c/${OTHER_CARD_SHORT_ID}"
```

Map `needs`, `depends-on`, `blocks`, `blocked-by`, `relates-to`, and `duplicates` as:

1. A card attachment pointing at the related card URL (as above).
2. A stated line in the description naming the relation and the target.

```
## Relations
- depends-on: https://trello.com/c/aB12cd3E Payment gateway integration
- blocks: https://trello.com/c/Zy98wx7V Refund flow
- relates-to: https://trello.com/c/Qw34er5T Cart persistence
```

Say plainly in output: Trello does not enforce these relations. They are text and attachments only.

## Sprints

Trello has no native sprints. Detect the board's convention and map to it:

- If the board uses a list per sprint (a column such as `Sprint 24`), place Story cards there.
- If the board uses a sprint label, apply that label instead.

```bash
# Move a Story card into a sprint list.
curl -s -X PUT "https://api.trello.com/1/cards/${STORY_ID}?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "idList=${SPRINT_LIST_ID}"
```

Rules:

- Only Story cards go in a sprint. Epics never go in a sprint list.
- Resolve the sprint list or label against the real board options first.
- If the board has no sprint concept, skip this step.

## Linking stories to the epic

Keep the link bidirectional:

- The Epic card holds a checklist of Story links.
- Each Story card attaches the Epic card URL.

```bash
# 1. Epic keeps a checklist of Story links.
EPIC_STORIES_ID=$(curl -s -X POST "https://api.trello.com/1/checklists?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "idCard=${EPIC_ID}" \
  --data-urlencode "name=Stories" \
  | jq -r '.id')

# Read the Story short link, then add it as a checklist item.
STORY_URL=$(curl -s "https://api.trello.com/1/cards/${STORY_ID}?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.shortUrl')
curl -s -X POST "https://api.trello.com/1/checklists/${EPIC_STORIES_ID}/checkItems?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "name=Add express checkout button ${STORY_URL}"

# 2. Each Story attaches the Epic card URL.
EPIC_URL=$(curl -s "https://api.trello.com/1/cards/${EPIC_ID}?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  | jq -r '.shortUrl')
curl -s -X POST "https://api.trello.com/1/cards/${STORY_ID}/attachments?key=${TRELLO_KEY}&token=${TRELLO_TOKEN}" \
  --data-urlencode "url=${EPIC_URL}"
```
