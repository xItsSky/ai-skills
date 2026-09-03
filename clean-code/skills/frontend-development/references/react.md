# React

Modern React (v19+): function components, hooks, and the React Compiler. The patterns below assume that baseline. Where a rule depends on a version or on the compiler, it is called out. On React 18 and earlier there is no compiler, so the manual memoization notes below apply in full.

## Mental model

- UI is a function of its inputs: `UI = f(props, state, context)`. Given the same inputs, a component renders the same output.
- Render is pure. No side effects, no mutation, no fetching, no subscriptions during render. Side effects belong in event handlers or effects.
- State is immutable. Never mutate an object or array in place; produce a new value and set it. Mutation skips the render the UI depends on.
- Keep state close to where it is used. Lift it only when two components genuinely need to share it.

## Components

- One responsibility per component. If a component both fetches and renders and formats, split it.
- Compose small components instead of building one large component driven by flags. A pile of booleans (`admin`, `editable`, `compact`, `showDetails`) mixes unrelated concepts into a single body.
- Separate the UI from the business logic. The component renders; a hook or service decides.

```tsx
// Instead of a configurable monolith
<UserCard admin editable compact showDetails />

// Compose
<Card>
  <UserHeader user={user} />
  <UserDetails user={user} />
</Card>
```

## State

Store the minimum. Anything you can compute from existing state or props is not state.

```tsx
// Don't store what you can derive
const fullName = `${firstName} ${lastName}`;
```

Pick the smallest tool that fits:

| Need | Use |
|---|---|
| Local, simple | `useState` |
| Local, complex transitions | `useReducer` |
| Shared between parent and children | Lift to the closest common parent |
| Global and stable (theme, auth, locale) | Context |
| Large, frequently changing global | External store (Zustand, Redux) |
| Server data | Query/cache layer (TanStack Query), not global state |

- Server data is not application state. Cache it, revalidate it, and let the query layer own loading and error status.

## Hooks

### useState

- Use the functional form when the next state depends on the previous one: `setCount(c => c + 1)`. The direct form reads a stale value inside closures and batches.

### useEffect

An effect synchronizes React with an external system. That is its only job.

- Use it for subscriptions, timers, DOM APIs, WebSockets, and non-React libraries.
- Do not use it to compute a value from props or state. Derive that value during render.
- Do not use it to orchestrate internal data flow between components. Pass props or lift state.
- Always clean up. Return the unsubscribe or teardown so re-runs and unmounts do not leak.

```tsx
useEffect(() => {
  const socket = connect(roomId);
  socket.subscribe(onMessage);
  return () => socket.close();
}, [roomId]);
```

Common failures: missing dependencies, stale closures, infinite loops from unstable deps, forgotten cleanup, and reaching for an effect when a plain computation would do.

### useRef

- Holds a value that survives renders without triggering one: a DOM node, a timeout id, a previous value, an external instance.
- Mutating `.current` does not re-render. If the UI must react to the change, it is state, not a ref.

### useMemo and useCallback

- `useMemo` caches a computed value. `useCallback` caches a function reference.
- Reach for them only when there is a reason: a genuinely expensive calculation, a referential identity that a memoized child or an effect dependency relies on.
- The React Compiler (React 19+) memoizes automatically. With it enabled, manual memoization is the exception, applied where profiling shows it pays off rather than by reflex. On React 18 or with the compiler off, keep the manual `useMemo` / `useCallback` where identity or an expensive calculation genuinely needs it.

### memo

- `React.memo` skips a re-render when props are shallowly equal. It is an optimization, not an architecture.
- Do not use it to paper over a component that should have been split. Fix the boundary first.

## Context

- Good for values that are global and change rarely: theme, authenticated user, locale, config, injected dependencies.
- A context change re-renders every consumer. Keep frequently changing values out of context, or split them off.
- Prefer several focused contexts over one context holding everything. A single mega-context re-renders unrelated consumers on every change.

## Custom hooks

- Extract a hook to reuse logic or to give a behavior a name, not merely to shorten a file.
- A custom hook can call other hooks. That is how you compose behavior.

Rules of hooks, without exception:

- Call hooks only at the top level. Never inside conditions, loops, or nested callbacks.
- Call hooks only from a React component or another custom hook.

## Lists and keys

- A key is a stable logical identity, usually `item.id`. React uses it to match elements across renders.
- `key={index}` is acceptable only for a list that never reorders, filters, or inserts. Anywhere else it corrupts state and DOM identity.

## Architecture

Organize by feature, not by technical layer. A folder of 300 files split across `components/`, `services/`, `models/`, and `hooks/` tells you nothing about what the app does.

```
src/
├── features/
│   └── <feature>/
│       ├── components/
│       ├── hooks/
│       ├── services/
│       ├── types/
│       └── utils/
├── shared/          Reusable across features
└── infrastructure/  Framework, clients, config
```

## Separation of concerns

Keep a clear chain: Component → Hook / use-case → Service / Repository → API.

- The component does not know HTTP details, endpoints, or headers.
- Call `userService.getUsers()` or a dedicated query hook. Do not scatter `fetch()` through the UI.

```tsx
// In the component
const { data: users } = useUsers();

// In the hook
function useUsers() {
  return useQuery({ queryKey: ['users'], queryFn: userService.getUsers });
}
```

## Performance

Measure first, optimize second. Work through this order before touching memoization:

1. Avoid unnecessary work: don't render, compute, or fetch what nothing needs.
2. Get the architecture right: correct state placement and component boundaries.
3. Ship less JavaScript.
4. Split code and lazy-load routes and heavy components.
5. Virtualize long lists.
6. Memoize, once the profiler shows where it helps.

Manual memoization added on a guess usually costs more than it saves.

## TypeScript with React

- Type props precisely. Use union literals (`'sm' | 'md' | 'lg'`) instead of a bare `string`.
- Model state with discriminated unions so impossible states cannot be represented:

```tsx
type State =
  | { status: 'loading' }
  | { status: 'success'; data: User[] }
  | { status: 'error'; error: Error };
```

A flag bag (`isLoading`, `isError`, `data`, `error`) allows contradictory combinations the union forbids.

- Lean on utility types: `Pick`, `Omit`, `Partial`, `Record`, `ReturnType`, `Parameters`.

## Testing

Test behavior, not implementation. Use React Testing Library and interact as the user would: query by role and text, fire events, assert on what renders. Favor component and integration tests, back them with targeted unit tests, and reserve end-to-end tests for critical flows. See `core-development/references/testing-philosophy.md` for the coverage contract.

## Quick reference

| Do | Instead of |
|---|---|
| `setCount(c => c + 1)` | `setCount(count + 1)` when it depends on previous |
| Derive during render | Compute in `useEffect` and store in state |
| `useEffect` to sync with external systems | `useEffect` to orchestrate internal data flow |
| Compose small components | One component with many boolean flags |
| Store the minimum, derive the rest | Store `fullName` alongside `firstName` + `lastName` |
| `key={item.id}` | `key={index}` on a dynamic list |
| Discriminated union | Flag bag that allows impossible states |
| Let the React Compiler memoize | `useMemo` / `useCallback` everywhere by reflex |
| Query layer for server data | Server data in global state |
| `userService.getUsers()` | `fetch()` scattered through components |
