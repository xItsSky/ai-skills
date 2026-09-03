# Clean Code

Language-agnostic principles for code that the next person can read, change, and trust. The next person is usually you, six months out. Apply these everywhere; they cost little and compound.

## Names

- Names reveal intent. A reader should understand what a thing is without chasing its definition.
- Name for the concept, not the type or the loop. `elapsedMs` beats `x`; `activeUsers` beats `list2`.
- A function name is a verb phrase that says what it does. If you need "and" in it, the function does too much.
- Avoid abbreviations that only you expand, and avoid encoding types into names.

## Functions

- One function, one job. If you can describe it accurately with an "and", split it.
- Keep functions short enough to hold in your head. Length is a symptom; the real target is a single responsibility.
- Keep one level of abstraction per function. Do not mix high-level orchestration with byte-level fiddling in the same body.
- Few parameters. When the list grows, pass a single well-named object or split the function.

## Control flow

- Use guard clauses. Handle invalid input, empty cases, and early exits at the top, then run the main path flat.
- Deep nesting hides the happy path. Flatten it.

```
// Instead of nesting the whole body inside a valid check:
function charge(order) {
  if (!order) return;
  if (!order.paid) return;
  applyCharge(order);
}
```

## Composition over inheritance

- Prefer composing small pieces to deep inheritance trees. Inheritance couples subclasses to a base you cannot change freely.
- Prefer composition over a pile of configuration flags. A function whose behavior forks on three booleans is really several functions wearing one signature. Split them.

## Modules and boundaries

- A module should have one reason to change and a clear public surface. Hide the rest.
- Depend on interfaces, not concretions, at the seams that cross a boundary or a layer.
- Keep related code together and unrelated code apart. Cohesion inside, low coupling across.

## DRY, but not premature

- Remove real duplication of knowledge: one rule, one place.
- Do not abstract on the first repeat. Two similar blocks are often a coincidence, not a shared concept. Wait for the third occurrence (the rule of three) before extracting.
- A wrong abstraction costs more than duplication. When an abstraction starts sprouting flags and special cases, inline it and start over.

## Comments

- Comments explain why, not what. The code says what it does; the comment says why it had to.
- A comment that restates the code is noise that rots. Delete it and let the name carry the meaning.
- Document the non-obvious: a workaround, a business constraint, a subtle ordering, a link to the ticket that explains it.

## Dead code

- Delete unused code, commented-out blocks, and unreachable branches. Version control remembers; the file should not.
- Dead code misleads readers into thinking it matters and drags along in every search.

## Errors

- Handle errors explicitly. Do not swallow an exception into an empty catch.
- Fail where you can act, with enough context to diagnose. Do not return a null that a caller will forget to check.
- Distinguish expected outcomes (a lookup miss) from exceptional ones (a broken connection) and model them differently.

## Purity and side effects

- Keep functions pure where you can. Pure functions are trivial to test and safe to move.
- Isolate side effects (I/O, mutation, time, randomness) at the edges. Push them out of the logic they surround so the core stays deterministic.

## Quick reference

| Do | Instead of |
|---|---|
| `elapsedMs`, `activeUsers` | `x`, `data`, `list2` |
| One job per function | a function that does "X and Y" |
| Guard clause, then flat body | deeply nested `if` blocks |
| Compose small units | deep inheritance chains |
| Split on behavior | boolean flag parameters |
| Extract on the third repeat | abstracting the first duplicate |
| Comment the *why* | comment restating the code |
| Delete dead code | commented-out blocks kept "just in case" |
| Explicit error handling | empty `catch` / ignored return |
| Pure core, effects at edges | I/O tangled through the logic |
