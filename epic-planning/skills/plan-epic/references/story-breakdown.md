# Story Breakdown

Decompose the epic into work items that are each independently deliverable. This is where technical detail lives.

## Work item types

| Type | Use for |
|---|---|
| Epic | The feature as a whole. One per run. |
| Story | A vertical slice of user-facing value. |
| Task | Technical work with no direct user value on its own. |
| Sub-task | A piece of a story, when splitting the work helps. |
| Bug | A defect to fix. |
| Spike | Time-boxed research to remove an unknown before estimating. |

Not every tracker has every type. The platform adapter maps these to what exists.

## Decomposition rules

- Prefer vertical slices that deliver value end to end over horizontal layers.
- Each item is completable in about one to two days. Split anything larger.
- Separate genuinely distinct concerns into their own items.
- Turn edge cases, error states, and empty states into stories or explicit acceptance criteria, not afterthoughts.
- Do not create work already tracked elsewhere. Check first.

## Story format

```
As a <role>, I want <capability>, so that <value>.

Description
  What this delivers and how it behaves.

Business rules
  The rules from the epic that this story enforces (BR1, BR3...).

Acceptance criteria
  - [ ] Given <context>, when <action>, then <result>.

Technical notes
  Approach, constraints, references. Use the clean-code stack references when available.

Estimate
  Optional. Fibonacci points or t-shirt size, per the tracker's field.

Definition of done
  Tests, docs, review, whatever the project requires.
```

## Estimation

Offer it, do not force it. Use Fibonacci (1, 2, 3, 5, 8, 13) or t-shirt sizes (S, M, L, XL), matching the tracker's field. A 13 or an XL is almost always two smaller items; prefer splitting.

## Grooming

After the first draft, offer to groom, the user's choice of mode:

- With the user: walk each story together, sharpen acceptance criteria, split what is too big, add stories for missing edge cases, and estimate.
- On your own: groom to a consistent bar, then present the result for review.

Grooming checklist:

- Every story has clear, testable acceptance criteria.
- No story is oversized or vague.
- Edge cases and error paths are covered somewhere.
- Estimates are consistent with each other.
- No duplication or overlap between stories.

## Sprints

Only if the tracker has sprints or iterations. Offer to place stories into the current, next, or a named sprint. Never assume one, and never place the epic in a sprint.
