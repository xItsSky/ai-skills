# Epic Specification

The epic is the complete picture of the feature, written for anyone to understand what is being built and why. It centres on business rules and outcomes. Keep implementation detail out; that is what the stories are for.

## Structure

```
Title

Context
  The problem, who is affected, and why it matters now.

Goal
  The outcome this delivers, in one or two sentences.

Functional description
  The feature in full: the flows, the behaviour, what the user can do.
  Written as prose a product owner would sign off.

Business rules
  Numbered and explicit. Each rule stands on its own.
  BR1: ...
  BR2: ...

Scope and non-goals
  In scope: ...
  Out of scope: ...

Acceptance criteria
  Outcome-focused, verifiable at the epic level.
  - [ ] ...

Dependencies and relations
  What this needs, blocks, or relates to.

Open questions and assumptions
  Anything not yet resolved, stated plainly.

Metadata
  Type: Epic
  Priority, area or labels, milestone or fix version.
  Mapped to the tracker in Step 8.
```

## Quality bar

- The business rules are exhaustive and numbered. A reader can tell exactly what is allowed, forbidden, and required.
- The acceptance criteria are verifiable and describe outcomes, not implementation.
- Non-goals are explicit, so scope creep has nowhere to hide.
- No technical design leaks in. If a decision is technical, it belongs in a story.
- Every open point is listed, not hidden.
