# JavaScript

For projects without TypeScript. The language gives you enough rope to write unreadable, fragile code; these rules keep you on the safe side of a modern ES baseline (ES2020 and up). Where a feature needs a newer runtime, that is called out. Where types matter at a boundary, document them with JSDoc.

## Declarations

- Use `const` by default. Use `let` only when you reassign. Never use `var`; its function scope and hoisting cause bugs that block scoping removes.
- Declare variables close to first use, not at the top of the function.

## Equality and comparison

- Use `===` and `!==`. The loose operators coerce in ways that surprise even experienced developers.
- The one deliberate exception: `x == null` to test for `null` or `undefined` together. Comment it if it is not obvious.

## Immutability and pure functions

- Do not mutate function arguments or shared state. Return new values.
- Prefer pure functions: same input, same output, no side effects. They are easy to test and reason about.
- Copy before changing with spread or the immutable array methods (`toSorted`, `toSpliced`, `with`, ES2023, so a recent runtime) instead of the mutating ones. On an older target, spread then sort the copy.

```js
const next = { ...state, active: true };
const sorted = items.toSorted((a, b) => a.rank - b.rank);
```

## Async

- Use `async`/`await`. It reads top to bottom and keeps error handling in one place.
- Do not chain `.then()` where `await` would be clearer, and never mix the two styles in one flow.
- Always handle rejection. Wrap awaits in `try`/`catch`, or attach a `.catch()`. An unhandled rejection is a crash waiting to happen.
- Run independent async work concurrently with `Promise.all`; do not `await` in a loop when the iterations are independent.

```js
const [user, orders] = await Promise.all([fetchUser(id), fetchOrders(id)]);
```

## Modules

- Use ES modules. Import what you need; export a clear surface.
- Do not attach to globals or `window` to share state. A global is an untracked dependency for every file.

## Optional chaining and nullish coalescing

- Reach into possibly-absent structures with `?.`.
- Default with `??`, not `||`, when `0`, `""`, or `false` are valid values. `||` swallows them.

```js
const port = config.server?.port ?? 3000;
```

## Control flow

- Return early. Handle the invalid and edge cases first, then let the main path run unindented.
- Deep nesting is a readability tax. Flatten it with guard clauses.

```js
function totalFor(order) {
  if (!order) return 0;
  if (order.items.length === 0) return 0;
  return order.items.reduce((sum, i) => sum + i.price, 0);
}
```

## Avoid clever coercion

- No `+str`, `!!x` sprinkled around, or `~indexOf`. Write `Number(str)`, `Boolean(x)`, `arr.includes(x)`. The intent should be readable, not decoded.

## Array methods with judgment

- Prefer `map`, `filter`, `find`, `some`, `every`, and `reduce` over manual loops when they read clearly.
- Do not force a `reduce` when a plain `for...of` is more legible. Readability wins over cleverness.
- Chaining is fine until it hides what is happening; break long chains into named steps.

## JSDoc at boundaries

- Document exported functions with JSDoc: parameter types, return type, and thrown errors. The editor uses it for completion and the reader uses it for contracts.

```js
/**
 * @param {string} id
 * @returns {Promise<User>}
 * @throws {NotFoundError} when no user matches
 */
export async function getUser(id) { /* ... */ }
```

## Quick reference

| Do | Instead of |
|---|---|
| `const` / `let` | `var` |
| `===` / `!==` | `==` / `!=` |
| `value ?? fallback` | `value \|\| fallback` for `0`/`""`/`false` |
| `obj?.a?.b` | manual `obj && obj.a && obj.a.b` |
| `async`/`await` with `try`/`catch` | unbounded `.then()` chains |
| `Promise.all([...])` | `await` in a loop for independent work |
| `Number(x)` / `Boolean(x)` | `+x` / `!!x` |
| `arr.includes(x)` | `~arr.indexOf(x)` |
| early return | deep `if` nesting |
| `toSorted` / `with` | mutating `sort` / index assignment |
