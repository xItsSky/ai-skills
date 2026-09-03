# Challenge Checklist

The discovery is adversarial on purpose. A feature is not ready because it sounds reasonable; it is ready when it survives scrutiny. Find the small beast before it reaches production.

## How to run the conversation

- Ask two or three questions at a time, never a wall of them.
- Rephrase what you understood before going deeper, so the user can correct you early.
- When an answer is vague, propose a concrete interpretation and ask the user to confirm or reject it.
- Keep a running list of confirmed facts, open questions, and assumptions.
- Stop only when you can write solid acceptance criteria and list the business rules with confidence.

## What to probe

### Users and value

- Who uses this, in which roles? Who else is affected?
- What problem does it solve, and what happens if nothing is done?
- What is the observable outcome for the user?

### Functional behaviour

- The main flow, step by step.
- Every alternate flow and how the user reaches it.
- What the feature explicitly does not do.

### Business rules

- State each rule explicitly: limits, thresholds, eligibility, ordering, calculations, defaults.
- What is allowed, forbidden, or required, and for whom?
- What changes a rule: role, plan, state, time, locale?
- Enumerate them. This is the core of the epic.

### Data

- What entities and fields are involved? What is optional or required?
- Validation rules and formats.
- Lifecycle: created, updated, archived, deleted. Any migration or backfill?

### States and flows

- Happy path, empty state, loading state, partial data.
- Error handling: validation errors, failures, timeouts, retries.
- Permission and ownership: who can see or do what.
- Concurrency: two users acting at once, double submits.

### Edge cases and boundaries

- Zero, one, many, maximum. First use and repeat use.
- Boundary values on every limit and threshold.
- What happens when an upstream dependency is down.

### Non-functional

- Performance and scale expectations.
- Security and privacy: sensitive data, access control, audit trail.
- Accessibility and internationalisation.
- Observability: what to log, measure, or alert on.

### Dependencies and integrations

- Other epics, services, or teams this needs or blocks.
- External systems, APIs, webhooks, feature flags.

### Risks and unknowns

- What could make this much bigger than it looks.
- Assumptions that must be confirmed before build.

## Exit condition

You can write the epic's acceptance criteria and its business-rules section without guessing. Everything still open is captured as an explicit assumption or question, not silently assumed.
