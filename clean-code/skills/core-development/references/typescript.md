# TypeScript

The type system is a tool for making wrong states impossible, not a formality to satisfy the compiler. Lean on it. The rules below assume TypeScript 5.x and a project that opts into strictness. Where a rule depends on a version, the version is called out.

## Compiler settings

- Turn on `strict`. It is the baseline, not an advanced mode.
- Enable `noUncheckedIndexedAccess`. Indexing into an array or record returns `T | undefined`, which is the truth.
- Enable `exactOptionalPropertyTypes` where the codebase can absorb it. An optional property that is present but `undefined` is a different thing from an absent one, and the flag keeps that honest.
- Keep `noImplicitAny` on. An implicit `any` is a hole in the type graph.

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

## No any

- `any` disables checking for everything it touches and everything downstream. Do not use it.
- When a value is genuinely open, type it `unknown` and narrow before use.
- Narrow with `typeof`, `instanceof`, `in`, discriminant checks, or a type guard predicate.

```ts
function parse(input: unknown): Config {
  if (typeof input !== "object" || input === null) {
    throw new TypeError("config must be an object");
  }
  // input is narrowed; validate its shape from here
}
```

## Inference and annotations

- Let inference do the work for locals and obvious expressions. Annotating `const count = 0` as `number` adds noise.
- Annotate public boundaries: exported function parameters and return types, public class members, module APIs. The annotation is the contract, and it stops an internal change from silently reshaping what callers depend on.
- Annotate a return type when the function is recursive, when inference would widen incorrectly, or when you want the compiler to catch a drifting implementation.

## Make impossible states unrepresentable

- Use discriminated unions to model states that cannot coexist. A single `status` field beats a bag of optional booleans.
- The compiler then forces every branch to be handled.

```ts
type Request =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: User }
  | { status: "error"; error: Error };

function render(req: Request) {
  switch (req.status) {
    case "success":
      return show(req.data); // data exists only here
    case "error":
      return fail(req.error);
    // ...
  }
}
```

## Utility types

- Derive types instead of restating them. `Pick`, `Omit`, `Partial`, `Required`, `Record`, `ReturnType`, and `Parameters` keep related types in sync.
- When a function's argument type should track another function, use `Parameters<typeof fn>` rather than copying the shape.

```ts
type UserId = User["id"];
type CreateUser = Omit<User, "id" | "createdAt">;
type UserIndex = Record<UserId, User>;
```

## Unions over enums

- Prefer union string literals to `enum` for most cases. They erase to nothing at runtime, work with plain string values, and narrow cleanly.
- Reach for `enum` only when you need a named runtime object with reverse mapping, and even then consider a `const` object with `as const`.

```ts
type Role = "admin" | "editor" | "viewer";

const Role = { Admin: "admin", Editor: "editor" } as const;
type Role = (typeof Role)[keyof typeof Role];
```

## Readonly and immutability

- Mark data that should not change as `readonly`, and use `readonly T[]` for arrays you only read.
- Freeze intent at the type level; it documents the contract and blocks accidental mutation.

## satisfies

- Use `satisfies` (TS 4.9+) to check a literal against a type while keeping its narrow inferred type. Annotation would widen it and lose information.

```ts
const routes = {
  home: "/",
  users: "/users",
} satisfies Record<string, string>;

// routes.home is "/" (literal), not string
```

## Avoid escape hatches

- Do not use the non-null assertion `!`. If a value can be null, handle it; if it cannot, prove that to the compiler with a guard.
- Do not paper over a mismatch with `as`. A cast tells the compiler to stop checking. Fix the type that produced the wrong shape instead.
- The rare legitimate cast (a well-tested `unknown` at a boundary) deserves a comment explaining why it is safe.

## Imports

- Use `import type` for type-only imports. It signals intent and lets the build strip the import entirely.

```ts
import type { User } from "./user";
```

## Keep generics honest

- Add a type parameter only when it links two positions in the signature. A generic used once is a disguised `any`.
- Constrain type parameters with `extends` so they carry meaning.
- Use a `const` type parameter (TS 5.0+) when you want the caller's literal preserved without them writing `as const` at every call site.

```ts
// good: return type follows the argument
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}

// const preserves the literal tuple instead of widening to string[]
function tuple<const T extends readonly unknown[]>(items: T): T {
  return items;
}
```

## Resource cleanup

- For a resource that must be released (file handle, lock, connection), prefer `using` (TS 5.2+, needs a runtime with `Symbol.dispose`) over a manual `try`/`finally`. The disposal runs when the scope exits, even on an early return or throw.

```ts
using file = openFile(path); // disposed at end of scope
```

## Quick reference

| Do | Instead of |
|---|---|
| `unknown` then narrow | `any` |
| `import type { X }` | `import { X }` for types |
| `readonly T[]` | `T[]` for read-only data |
| `satisfies Record<...>` | `: Record<...>` when you need the literal type |
| Discriminated union | parallel optional flags |
| `Omit<User, "id">` | hand-written duplicate type |
| Union literals | `enum` in most cases |
| Fix the source type | `value as Target` |
| Guard clause | `value!` |
