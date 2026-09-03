# Review Dimensions

Each dimension is one parallel review pass. Give each subagent the diff, the change intent, the loaded conventions, and the brief below. Use the noted decoration on findings so the consolidation step can group them.

## Convention baseline

Review against the project's actual standard, in this order: the `clean-code` plugin's stack references when installed, then the project's own conventions (CONTRIBUTING, CLAUDE.md or AGENTS.md, lint and format configs), then general best practice. Do not invent rules the project does not hold.

## Scaling

Match the passes to the change. A small single-file fix needs Correctness, Tests, and maybe Security. A large feature warrants the full set. Do not spawn a Performance or Runtime pass for a change that cannot affect them.

## Dependency audit (feeds Security)

Before the Security pass, audit new or changed dependencies and pass the results in.

```bash
npm audit --json 2>/dev/null          # npm, pnpm, yarn
pip-audit 2>/dev/null                  # Python
govulncheck ./... 2>/dev/null          # Go
```

For the JVM, run the OWASP Dependency-Check task (`mvn dependency-check:check` or `gradle dependencyCheckAnalyze`). For each finding note the advisory ID, severity, affected package and version, and the risk. Default threshold: High and Critical are blocking, the rest non-blocking. Honour a user-specified threshold when given.

## Dimensions

### Correctness and logic

Does the code do what the change claims?

- Logic errors, off-by-one, wrong conditions
- Unhandled null, undefined, or empty cases
- Swallowed errors or wrong error handling
- Race conditions and async ordering
- Incorrect data transformations or wrong status codes

### Security: decoration `(security)`

Could this introduce a vulnerability?

- Exposed secrets, tokens, or credentials
- Missing input validation or sanitisation at the boundary
- Injection vectors: SQL, NoSQL, shell, template
- Broken access control: missing authn or authz, wrong roles, object-level gaps (IDOR)
- Sensitive data logged or returned in a response
- Mass assignment through an unfiltered input object
- Known advisories in dependencies, from the audit above

### Architecture and design

Does it fit the existing design?

- Business logic leaking into controllers, handlers, or UI
- Persistence models exposed instead of DTOs or contracts
- Single-responsibility violations and unclear abstractions
- Unnecessary coupling, or divergence from established patterns

### Tests: decoration `(test)`

Is the change adequately tested? Apply the project's testing standard.

- Missing tests for new logic
- Happy path only, with untested error and edge cases
- Over-broad mocks that assert nothing real
- Tests that restate the implementation or duplicate coverage without value

When available, use the clean-code `testing-philosophy.md` for what counts as a real test.

### Performance: decoration `(performance)`

Could this hurt at scale? Only when the change can affect it.

- N+1 queries, or missing indexes inferred from access patterns
- Blocking work that should be async
- Over-fetching, or unbounded payloads without pagination
- Repeated expensive work that could be cached or hoisted

### Readability and maintainability

Is it clean and idiomatic for the language?

- Weak or misleading names
- Functions doing too much, or deep nesting
- Duplication that should be extracted
- Dead code and needless complexity
- Loose typing where a precise type exists, or unsafe casts

### Documentation and conventions

Documented and consistent with the project?

- Missing doc comments on public methods (JSDoc, Javadoc, and the like)
- Missing or stale API docs where the project uses them (OpenAPI, Swagger)
- Commit and branch naming against the project's convention
- Docs not updated for a changed endpoint, config, or behaviour

### Runtime and behavioral (optional): decoration `(runtime)`

Does it actually work when run? Only when a local run is feasible.

- Run the app or the affected path and confirm the feature behaves end to end
- Watch for runtime errors, warnings, and unexpected logs
- Exercise real edge cases, not only the unit tests
- Confirm migrations, setup, or env changes apply cleanly, and look for regressions in related flows
