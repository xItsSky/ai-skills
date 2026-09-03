# Testing Philosophy

The contract for every feature and every bug fix, in any stack. Framework mechanics live in `component-testing.md` (frontend) and `integration-testing.md` (backend). This file defines what a test must be worth.

## The contract

- Every feature and every fix ships with unit tests. No exceptions.
- Coverage floor is 80% per project. Below that, the work is not done.
- A test earns its place by covering logic. Coverage is a side effect of testing behavior, never the goal itself.
- Tests assert what the code does, not how it is wired.

## What counts as a real test

Test the parts that can be wrong:

- Business rules and decisions.
- Branches, boundaries, and conditions.
- Error paths and failure handling.
- Edge cases: null, empty, zero, negative, unauthorized, missing data, concurrent access.
- Transformations and calculations.

A good test would fail if the behavior broke. If you can gut the implementation and the test still passes, it was testing nothing.

## What does not count

These raise the coverage number without protecting anything. They do not satisfy the contract:

- Getters and setters with no logic.
- Pass-through methods that only forward a call.
- Tests that assert a mock was called instead of asserting a result.
- Tests that restate the implementation line by line.
- Framework or library behavior you do not own.
- Snapshot tests used as a substitute for real assertions.

Reaching 80% by testing accessors is a failure dressed as success. If the meaningful logic is untested, the number is a lie.

## How to write them

- One behavior per test. The name states the behavior: `returns 403 when the user lacks the role`.
- Arrange, act, assert. Keep the three visible.
- Cover the happy path and at least one failure path for every public method.
- Mock at boundaries (network, clock, filesystem), not the unit under test.
- Deterministic only. No real time, no random, no live network. Inject the clock.
- A test that needs heavy mocking to reach the logic is a design smell. Fix the seams, then test.

## Before you commit

- Run the suite. Green, not skipped.
- Confirm coverage meets the floor and that the covered lines are the ones that carry logic.
- New logic without a test that would catch its regression is incomplete work.

## Red flags, stop

- "It's too simple to test." Simple code breaks; the test takes a minute.
- "I'll add tests after." Tests written to pass an existing implementation prove nothing about intent.
- "Coverage is at 80%, so we're fine." Check what is covered. Accessors padding the number do not count.
- "The mock verifies it works." A mock call is not a result. Assert the output or the state.
