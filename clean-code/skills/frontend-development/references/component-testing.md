# Component Testing

How to test UI components in any framework. The coverage contract and what counts as a real test live in `../../core-development/references/testing-philosophy.md`; this file is the frontend mechanics. The guiding idea is Testing Library's: a test should resemble how a user uses the component. The more it does, the more confidence it gives.

## Test behavior, not implementation

- Render the component, interact with it the way a user would, assert what the user can observe.
- Do not reach into internal state, private methods, or child component instances. Those are wiring, and the contract says test what the code does, not how it is wired.
- A good component test survives a refactor that keeps behavior identical. If renaming a state variable breaks your test, the test was measuring the wrong thing.

## Query priority

Query the way a user finds things. Fall down the list only when the one above genuinely does not apply.

1. By role, with the accessible name: `getByRole('button', { name: /save/i })`. This doubles as an accessibility check.
2. By label text for form fields: `getByLabelText('Email')`.
3. By visible text or placeholder for non-interactive content.
4. `getByTestId` as a last resort, when nothing user-facing identifies the element.

- Preferring role and label queries means the test fails when the component becomes inaccessible. That is a feature. If you cannot query by role, real users with assistive tech cannot find it either.

## Interactions

- Drive interactions through a user-event style API (`click`, `type`, `keyboard`, `tab`, `hover`), not by dispatching raw DOM events. It models real sequences: focus, keydown, input, keyup.
- Test keyboard operation, not only clicks: tab order, Enter and Space activation, Escape to dismiss.
- Assert the observable outcome of the interaction, not that a handler ran.

## Async UI

- Wait for elements that appear later with `findBy*` queries. Wait for a condition with `waitFor`. Wait for something to leave with `waitForElementToBeRemoved`.
- Never assert immediately after an async action and hope the update already landed. Never paper over it with a fixed `sleep`.
- Assert both states worth caring about: the loading state and the resolved state, and the error state when there is one.

## Accessibility inside tests

- Querying by role is the accessibility check built into the test. If `getByRole` cannot find your button, the markup has a real problem.
- Assert accessible names and states (`aria-expanded`, `aria-invalid`, `disabled`) where they carry meaning.

## Mock at boundaries

- Mock the network (request interception at the HTTP layer, e.g. MSW), the clock, and randomness. Leave the component and its real children in place.
- Prefer real child components over stubbing them out. Stubbing everything below the unit tests nothing but the render call.
- Do not mock the framework's own reactivity or lifecycle.

## What to reach for

- Prefer component and integration tests that mount real markup and exercise real interactions.
- Avoid shallow render that asserts a child was called with certain props. That tests the render tree's shape, not behavior, and it breaks on every refactor.
- An assertion that a mock was called is not a result. Assert the DOM the user sees or the state they can observe.

## Do / Instead of

| Do | Instead of |
|---|---|
| `getByRole('button', { name })` | `container.querySelector('.btn')` |
| `getByLabelText('Email')` | query by CSS class or DOM path |
| `getByTestId` as last resort | `getByTestId` as the default |
| `await user.click(...)` | `fireEvent`-only dispatch |
| `await findByText(...)` / `waitFor` | assert synchronously after async work |
| assert visible text / DOM state | assert internal state or props |
| assert a spy was called | mock a callback and assert output/DOM |
| real child components | shallow render with everything stubbed |
| mock network with request interception | mock the component's own methods |
