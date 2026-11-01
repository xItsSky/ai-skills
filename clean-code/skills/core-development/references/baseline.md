# Engineering Baseline

The rules that apply to every change in every stack: types, tests, security, and
git. Read this once per task. Stack-specific guidance lives in the
`frontend-development` and `backend-development` skills; the deeper
cross-cutting files in this directory cover one topic each when a task needs
more than the contract below.

## Contents

- [Types](#types) — TypeScript 5.x under strictness
- [Tests](#tests) — what a test must be worth
- [Security](#security) — trust boundaries, secrets, dependencies
- [Git and commits](#git-and-commits) — branching and Conventional Commits

## Types

TypeScript 5.x with strictness opted in. Version-gated rules are labelled.

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

`noUncheckedIndexedAccess` makes indexing return `T | undefined`, which is the
truth. `exactOptionalPropertyTypes` keeps "present but `undefined`" distinct
from absent; enable it where the codebase can absorb it.

### Where to annotate

- Let inference handle locals. Annotating `const count = 0` as `number` is noise.
- Annotate public boundaries: exported signatures, public class members, module
  APIs. The annotation is the contract, and it stops an internal change from
  silently reshaping what callers depend on.
- Annotate a return type when the function is recursive, when inference would
  widen incorrectly, or to catch a drifting implementation.

### Make impossible states unrepresentable

```ts
type Request =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: User }
  | { status: "error"; error: Error };
```

One discriminant beats a bag of optional booleans: `data` exists only in the
branch that carries it, and the compiler forces every case to be handled.

### satisfies

Checks a literal against a type while keeping its narrow inferred type, which an
annotation would widen away (TS 4.9+).

```ts
const routes = { home: "/", users: "/users" } satisfies Record<string, string>;
// routes.home is "/", not string
```

### Unions over enums

Union literals erase at runtime and narrow cleanly. When you need a named
runtime object, a `const` object beats `enum`:

```ts
const Role = { Admin: "admin", Editor: "editor" } as const;
type Role = (typeof Role)[keyof typeof Role];
```

### Generics

- Add a type parameter only when it links two positions in a signature. A
  generic used once is a disguised `any`.
- Constrain with `extends` so the parameter carries meaning.
- A `const` type parameter (TS 5.0+) preserves the caller's literal without them
  writing `as const` at every call site:

```ts
function tuple<const T extends readonly unknown[]>(items: T): T {
  return items;
}
```

### Escape hatches

- `as` tells the compiler to stop checking. Fix the type that produced the wrong
  shape instead. A rare legitimate cast at a boundary deserves a comment saying
  why it is safe.
- `!` is the same bargain. If a value can be null, handle it; if it cannot, prove
  it to the compiler with a guard.

### Resource cleanup

`using` (TS 5.2+, needs a runtime with `Symbol.dispose`) disposes when the scope
exits, including on an early return or a throw. Prefer it to manual try/finally.

### Types: do / instead of

| Do | Instead of |
|---|---|
| `unknown`, then narrow with `typeof`/`instanceof`/`in`/a guard | `any` |
| `import type { X }` | `import { X }` for types |
| `readonly T[]`, `readonly` fields | `T[]` for data you only read |
| `satisfies Record<...>` | `: Record<...>` when you need the literal type |
| Discriminated union | parallel optional flags |
| `Omit<User, "id">`, `Parameters<typeof fn>` | hand-written duplicate type |
| Union literals, or a `const` object | `enum` in most cases |
| Fix the source type | `value as Target` |
| Guard clause | `value!` |

## Tests

Framework mechanics live in `component-testing.md` (frontend) and
`integration-testing.md` (backend). This is what a test must be worth.

### The contract

- Every feature and every fix ships with unit tests. No exceptions.
- Coverage floor is 80% per project. Below that, the work is not done.
- Coverage is a side effect of testing behavior, never the goal.
- Tests assert what the code does, not how it is wired.

### What earns its place

Test what can be wrong: business rules and decisions, branches, boundaries and
conditions, error paths, transformations and calculations, and the edge cases
(null, empty, zero, negative, unauthorized, missing data, concurrent access).

The check that settles it: gut the implementation. If the test still passes, it
was testing nothing.

### What does not count

These raise the number without protecting anything, and do not satisfy the
contract:

- Getters and setters with no logic, and pass-through methods that only forward.
- Asserting a mock was called instead of asserting a result.
- Restating the implementation line by line.
- Framework or library behavior you do not own.
- Snapshots standing in for real assertions.

Reaching 80% by testing accessors is a failure dressed as success. If the
meaningful logic is untested, the number is a lie.

### How to write them

- One behavior per test, named for the behavior: `returns 403 when the user
  lacks the role`.
- Arrange, act, assert, all three visible.
- Happy path plus at least one failure path for every public method.
- Mock at boundaries (network, clock, filesystem), never the unit under test.
- Deterministic only: no real time, no random, no live network. Inject the clock.
- A test that needs heavy mocking to reach the logic is a design smell. Fix the
  seams, then test.

### Before you commit

Run the suite; green, not skipped. Confirm coverage meets the floor and that the
covered lines are the ones carrying logic. New logic without a test that would
catch its regression is incomplete work.

### Red flags, stop

- "It's too simple to test." Simple code breaks; the test takes a minute.
- "I'll add tests after." Tests written to pass an existing implementation prove
  nothing about intent.
- "Coverage is at 80%, so we're fine." Check what is covered.
- "The mock verifies it works." A mock call is not a result. Assert the output
  or the state.

## Security

Defaults while writing, not a hardening phase for later.

### Trust boundaries

- Validate every input where it enters: request bodies, query params, headers,
  uploads, message payloads, env values.
- Validate against an allowlist of what is permitted, not a blocklist.
  Blocklists always miss a case.
- Validate before you sanitize. A well-formed value is easier to reason about.
- Anything running in a browser or on a device can be read, modified, and
  replayed. Client-side checks are not controls. Enforce authorization and
  validation on the server for every request, including ones a legitimate client
  would never send.

### Secrets

- No API keys, tokens, or passwords in source, in committed config, or in
  history. Load them from env vars or a secret manager, injected at deploy time.
- Rotate on a schedule, and immediately on a leak. Anything committed once is
  compromised forever, including after the commit is removed.
- Do not log secrets, tokens, or PII. Logs travel to places with weaker controls
  than your database. Redact before the log line, and be deliberate about what
  error detail reaches a client.

### Least privilege

Grant the minimum and scope it narrowly: database roles, API scopes, file
permissions, cloud IAM, service accounts. Separate credentials per environment.
A read path does not get write access.

### Injection and output encoding

- Pass data as data: parameterized queries or a query builder for every database
  call, and the same for shell commands, LDAP, and NoSQL filters.
- Where interpolation is unavoidable, use the platform's escaping API for that
  exact target.
- Encode output for the sink that consumes it, chosen at the point of output
  rather than at input: HTML-escape for markup, attribute-escape for attributes,
  JSON-encode for scripts, URL-encode for URLs.

### Fail closed

On error, ambiguity, or timeout, deny. A failed auth check rejects; it never
falls through to allowed. If you cannot confirm access, refuse it.

### Cryptography and transport

- Use vetted, maintained crypto libraries. Never invent a cipher, hash scheme,
  or token format. Let the library handle salts, IVs, and modes; misusing a
  primitive breaks it as surely as choosing a weak one.
- Hash passwords with an algorithm built to be slow: argon2, bcrypt, or scrypt.
  Never a plain SHA.
- Enforce HTTPS everywhere, redirect plaintext, enable HSTS. Use TLS for
  service-to-service traffic too, and verify certificates. Internal does not
  mean trusted.

### Before adding a dependency

Adding a package is a security decision, not a convenience. This applies in
every ecosystem (`npm install`, Yarn, pnpm, Maven, Gradle, `pip`, `go get`,
Cargo).

- Vet first, install second. Do not run the install command until the package
  has cleared this check.
- Audit the exact version you intend to add, and its transitive tree, against a
  known-vulnerability source: `npm audit` / `pnpm audit` / `yarn npm audit`,
  OWASP Dependency-Check for Maven or Gradle, `pip-audit`, `govulncheck`.
  Cross-check the advisory databases (GitHub Advisories, OSV, Snyk).
- Weigh supply-chain health too: maintained, widely used, no active advisories.
  An unmaintained or typosquatted package is a risk with no CVE attached.
- If the package or anything it pulls in has known vulnerabilities, stop. Do not
  install. Report the package, the affected version, the severity, and a link to
  the advisory, then wait for the user's explicit decision.
- Proceed only on a clean tree, or once the user has knowingly accepted the
  risk. Prefer a patched version or a safer alternative where one exists.

Keep the tree minimal and patched: every package is code you now trust and
attack surface you now own. Audit in CI, pin versions, and review what an
upgrade pulls in.

### Security: do / instead of

| Do | Instead of |
|---|---|
| Validate against an allowlist at the boundary | trust well-formatted input |
| Enforce authz on the server | rely on hidden UI or client checks |
| Load secrets from a secret manager | commit keys to the repo |
| Grant least privilege per role and environment | share one broad admin credential |
| Parameterized queries | string-concatenated SQL |
| Encode output for its sink | insert raw values into HTML/URLs |
| Vet and audit a dependency before installing | `npm install` first, check later |
| Surface vulnerabilities and wait for approval | add a flagged package silently |
| Deny on error (fail closed) | fall through to allowed |
| Redact secrets and PII from logs | log full request or user objects |
| Vetted crypto libraries, argon2/bcrypt/scrypt | hand-rolled encryption, plain SHA |
| HTTPS/TLS with cert verification | plaintext on "internal" networks |

## Git and commits

Gitflow branching with Conventional Commits on top.

| Branch | Off | Merges into | Purpose |
|---|---|---|---|
| `main` | n/a | n/a | production; every commit is a shipped release |
| `develop` | n/a | n/a | integration; finished work lands here first |
| `feature/*` | `develop` | `develop` | new work |
| `release/*` | `develop` | `main` + `develop` | stabilize a version |
| `hotfix/*` | `main` | `main` + `develop` | patch production |

Never commit directly to `main` or `develop`. Both change only through a
reviewed merge. Short-lived branches are deleted after merge.

Name them `feat/<desc>`, `fix/<desc>`, `chore/<desc>`, or `docs/<desc>`, with
the description short, lowercase, and hyphenated. When the work ties to an
issue, use `feat/#<issue>-<desc>`; the number is mandatory there:
`feat/#214-signup-rate-limit`.

### Commit messages

```
<type>(<scope>): <description>

[optional body: explain the why]

[optional footers]
```

- Description is imperative present tense, lowercase, no trailing period, under
  72 characters. Write `add retry to fetch`, not `Added retry.`.
- Describe what changed, not how. The diff shows how. The body explains why and
  what it affects.
- Scope names the affected area and should match a real one.

| Type | Use for |
|---|---|
| `feat` | new user-facing capability |
| `fix` | bug fix |
| `docs` | documentation only |
| `refactor` | behavior-preserving change |
| `perf` | performance improvement |
| `test` | adding or fixing tests |
| `build` | build system or dependencies |
| `ci` | CI configuration |
| `chore` | housekeeping, no src/test change |
| `revert` | reverts a previous commit |

Mark a breaking change with `!` after the type or scope
(`feat(api)!: drop legacy token endpoint`), or a `BREAKING CHANGE:` footer.
Either form flags it for release tooling and reviewers.

### One concern per commit

A commit does one thing and reads as a single revertible unit of intent. Do not
mix a refactor with a feature, or a formatting sweep with a fix: splitting them
keeps review and `git revert` clean.

### Pull requests

- Follow the repository's PR template. Fill it in; do not delete sections.
- Link the related issue so the board and history stay connected.
- Keep the PR small enough to review. A giant PR gets a shallow review.
- Do not merge your own PR without review. The PR waits for it.
