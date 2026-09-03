# Integration Testing

The backend mechanics of the contract in `testing-philosophy.md`. That file defines what a test must be worth and what counts as a real test. This one covers how to test a backend's wiring without faking the parts that carry the risk.

## Two layers, two jobs

- Unit tests cover business logic and decisions in isolation. Mock the boundaries (network, clock, other services) and exercise the branches, edges, and error paths.
- Integration tests cover the wiring: the request enters the controller, flows through the service, hits a real repository and a real database, and comes back out. Mocking that path proves the mocks agree with each other, not that the system works.

## Use a real database

- Run integration tests against a real instance of the database you ship, via Testcontainers or an equivalent ephemeral container. Not an in-memory substitute, not a mock repository.
- An in-memory stand-in has different SQL, different constraints, and different transaction semantics. Tests pass against it and the query fails in production.
- Spin the container up per suite, migrate the schema the same way production does, and let each test seed and clean its own data.

## Test the HTTP contract

- Drive the real HTTP layer (the framework's test client), not the controller method called as a plain function. Routing, serialization, validation, and middleware are part of what you're testing.
- Assert the status code and the response body shape, not just that a value came back.
- Confirm the error format matches the API contract (see `api-design.md`), including the problem+json shape and the fields clients depend on.

## Cover auth and validation

- Test the unauthenticated case returns `401` and the forbidden case returns `403`. These are the checks most likely to rot silently.
- Test object-level authorization: a valid user reaching another user's resource is denied.
- Test that invalid input is rejected at the boundary with `400` and a useful per-field error, and that unknown fields don't slip through.

## Keep them deterministic

- Control the clock. Inject a fixed time so anything date-dependent is reproducible.
- Seed known data at the start of each test and isolate state per test: wrap in a transaction and roll back, or truncate between tests. A test that depends on another test's leftovers is a flake waiting to happen.
- No real network, no random values, no reliance on wall-clock ordering.

## Prefer few high-value tests

- A handful of integration tests through the real stack catch more than a wall of mock-heavy tests that only confirm the mocks.
- If reaching the logic needs elaborate mock scaffolding, the seams are wrong. Fix the design, then test. (Restated in `testing-philosophy.md` as a red flag.)
- Don't re-test framework behavior. Test your routes, your rules, your queries.

## Quick reference

| Do | Instead of |
|---|---|
| Real DB via Testcontainers | In-memory DB or mock repository |
| Drive the HTTP layer end to end | Calling the controller method directly |
| Assert status + body shape | Asserting a single field came back |
| Test `401`, `403`, and object-level access | Only testing the happy path |
| Test `400` on invalid input | Trusting validation is wired |
| Inject a fixed clock | Depending on real time |
| Isolate state per test | Sharing data across tests |
| A few integration tests through the stack | Many brittle mocks-only tests |
