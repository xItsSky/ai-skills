# Vue

Modern Vue (3.4+): `<script setup>`, Composition API, and Pinia. The patterns below assume that baseline, and version-specific macros are tagged inline. Options API still works, but new code uses `<script setup>` unless a specific constraint forces otherwise. On Vue 2, none of the `<script setup>` macros exist; use the Options API and the Vue 2 reactivity rules instead.

## Components

- Write components with `<script setup>`. It is the least verbose form and gives the best type inference. Reach for Options API only when a legacy codebase already leans on it.
- One responsibility per component. When a template grows past what you can hold in your head, split it.
- Prefer composition and slots over configuration flags. A component with a dozen boolean props to toggle sections wants to be several components with a slot.
- Name multi-word components (`UserCard`, not `Card`) so they never collide with current or future HTML elements.
- Keep the `<template>` declarative. Push branching and formatting into a `computed` or a method, not into the markup.

```vue
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ items: Item[] }>()
const total = computed(() => props.items.reduce((sum, i) => sum + i.price, 0))
</script>

<template>
  <p>Total: {{ total }}</p>
</template>
```

## Reactivity: ref vs reactive

- Default to `ref` for everything: primitives, objects, arrays. One mental model, one access pattern (`.value` in script, unwrapped in template).
- Use `reactive` only for an object you never reassign as a whole. Reassigning a `reactive` binding breaks the link to the original proxy.
- Never destructure a `reactive` object or `props`. Destructuring copies the current value and drops reactivity.
- When you need to pull fields out of a reactive source, wrap with `toRefs` (whole object) or `toRef` (single field) so each extracted binding stays live.

```ts
// Loses reactivity: count is a plain number now
const { count } = reactive({ count: 0 })

// Stays reactive
const state = reactive({ count: 0 })
const { count } = toRefs(state)
```

- Props are reactive but read-only. To derive from a prop, use `computed`; to keep a live reference for a composable, use `toRef(props, 'id')`. Reactive-props destructure (`const { id } = defineProps(...)`, stable from Vue 3.5) keeps destructured props reactive; before 3.5, destructuring props drops reactivity, so read them through `props.x` or `toRefs`.

## Derived state with computed

- Never store what you can derive. If a value is a pure function of other reactive state, it is a `computed`, not a `ref` you keep in sync by hand.
- `computed` is cached and only re-evaluates when a dependency changes. Keep the getter pure: no side effects, no async.
- A `ref` that a `watch` keeps updating from other refs is almost always a `computed` in disguise. Rewrite it.

```ts
// Instead of a ref kept in sync by a watcher
const fullName = computed(() => `${first.value} ${last.value}`)
```

## watch vs watchEffect

Watchers react to change. They do not compute values; that is what `computed` is for. Use them to run side effects.

- `watch` when you react to a specific source and need the old and new value, or want lazy evaluation (it does not run until the source changes).
- `watchEffect` when you sync with an external system and the dependency set is obvious from the body. It runs once immediately and re-runs when any tracked dependency changes.
- Reach for a watcher to talk to something outside Vue: fetch on route change, write to `localStorage`, drive an imperative canvas or map API.
- If you catch yourself assigning to a `ref` inside a watcher because "this value depends on that value", stop. That is derived state; use `computed`.

```ts
// React to a specific source, need the previous id
watch(() => props.userId, (id, prevId) => {
  if (id !== prevId) fetchUser(id)
})

// Sync with an external system, deps are implicit
watchEffect(() => {
  localStorage.setItem('theme', theme.value)
})
```

- Set `{ immediate: true }` on `watch` when the effect must also run on mount.
- Cancel stale async work when the source changes again: use the `onCleanup` callback passed to the watcher, or the standalone `onWatcherCleanup` (Vue 3.5+).

## Props

- Declare props with the type-only `defineProps<T>()` form. It gives full type checking with no runtime overhead.
- Set defaults with `withDefaults`, or use reactive-props destructure defaults (`const { size = 'md' } = defineProps(...)`, Vue 3.5+).
- Keep props read-only. Never mutate a prop; emit an event or expose a writable `computed` via `v-model`.

```ts
const props = withDefaults(
  defineProps<{ size?: 'sm' | 'md' | 'lg'; disabled?: boolean }>(),
  { size: 'md', disabled: false },
)
```

## Emits

- Declare events with the typed `defineEmits<T>()` form. It documents the payload and type-checks every `emit` call.
- Name events in the DOM-friendly form the parent binds to: `update:modelValue`, `submit`, `close`.

```ts
const emit = defineEmits<{
  submit: [payload: FormData]
  'update:modelValue': [value: string]
}>()
```

## v-model

- Use the `defineModel()` macro (stable from 3.4). It replaces the `modelValue` prop plus `update:modelValue` emit boilerplate with a single writable ref.
- Name multiple models for multi-field bindings: `defineModel('firstName')`, `defineModel('lastName')`.
- Reach for a model when a child needs two-way binding on a value the parent owns. For anything read-only, a prop plus an event is clearer.

```ts
const model = defineModel<string>()
// <input v-model="model" /> in the template
```

## Composables

- Extract reusable stateful logic into a composable when two components need it, or when a component's setup grows unwieldy. Composables are to Composition API what mixins tried and failed to be, without the naming collisions.
- Name them `useX`: `useMouse`, `usePagination`, `useFetch`.
- Return refs (or a reactive object), not raw values. Callers need the reactivity.
- Register lifecycle hooks and watchers inside the composable; Vue ties them to the calling component automatically.
- Keep them focused. A composable that does fetching, formatting, and routing is three composables.

```ts
export function useMouse() {
  const x = ref(0)
  const y = ref(0)
  const update = (e: MouseEvent) => { x.value = e.pageX; y.value = e.pageY }
  onMounted(() => window.addEventListener('mousemove', update))
  onUnmounted(() => window.removeEventListener('mousemove', update))
  return { x, y }
}
```

## State management with Pinia

- Use Pinia for state shared across unrelated components. Local component state stays in the component.
- Prefer setup stores. They read like a composable and give the same flexibility with `ref`, `computed`, and functions.
- Keep the global store for genuine client state: auth session, UI preferences, cross-page selections.
- Do not park server data in the global store. Server data is a cache with its own concerns: staleness, refetch, invalidation. Put it in a query layer (TanStack Query, or a `useFetch`-style composable) and let that own the cache. The Pinia store holds identity and intent, not a mirror of the database.

```ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => user.value !== null)
  function login(u: User) { user.value = u }
  return { user, isLoggedIn, login }
})
```

## Templates

- Give `v-for` a `:key` bound to a stable identity (an id), never the array index. An index key breaks reconciliation as soon as the list reorders or items are inserted.
- Never put `v-if` and `v-for` on the same element. Precedence is ambiguous and you pay the `v-if` cost per iteration. Filter with a `computed`, or wrap the loop in a `<template v-if>`.
- Keep expressions in the template trivial. Anything with a ternary chain or a method call belongs in a `computed`.
- Use `<template>` wrappers for grouping without an extra DOM node.

```vue
<!-- Instead of v-if on the loop element -->
<li v-for="user in activeUsers" :key="user.id">{{ user.name }}</li>
<!-- where activeUsers is a computed filter -->
```

## Lifecycle

- Register hooks (`onMounted`, `onUnmounted`, `onUpdated`) directly in `setup`. They must be called synchronously, not inside an `await` or a callback.
- Do DOM measurement and third-party init in `onMounted`. Tear down listeners, timers, and subscriptions in `onUnmounted`. Every subscription you open, you close.

## Performance

Measure first. The defaults are fast; most optimizations are noise until a profiler says otherwise.

- `v-memo` and `v-once` skip re-rendering. Use them only on proven hot paths such as a large list row or a static block that never changes. Applied blindly they add bugs, not speed.
- `shallowRef` (and `shallowReactive`) stop deep reactivity conversion. Use them for large immutable structures or data you replace wholesale rather than mutate field by field.
- Split rarely-used or heavy components with `defineAsyncComponent` so they lazy-load. Pair with route-level code splitting.
- Virtualize long lists (`vue-virtual-scroller` or similar). Rendering ten thousand rows is slow no matter how tight the component is.

```ts
const HeavyChart = defineAsyncComponent(() => import('./HeavyChart.vue'))
```

## TypeScript

- Type props and emits with the generic `defineProps<T>()` / `defineEmits<T>()` forms.
- Model impossible states out of existence with discriminated unions. A `status` field plus optional `data` and `error` lets you construct contradictions; a union does not.

```ts
type RequestState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }
```

- No `any`. Use `unknown` for genuinely open types, then narrow.
- Let inference work where the type is obvious. Annotate the boundaries: props, emits, function signatures, store return shapes.

## Testing

The contract in `testing-philosophy.md` holds here: test behavior, not wiring. A component test that only asserts a child was rendered protects nothing.

- Test components through Vue Test Utils or Testing Library. Testing Library pushes you toward asserting what the user sees and does, which is what you want.
- Drive the component the way a user would, clicking, typing, submitting, then assert the rendered output or the emitted event. Do not reach into `vm` internals to check private state.
- Test composables directly as functions. Mount them in a throwaway component only when they depend on lifecycle hooks.
- Mock at boundaries: the network, the clock, the router. Never mock the component under test.

## Quick reference

| Do | Instead of |
|---|---|
| `<script setup>` | Options API for new code |
| `ref` by default | reaching for `reactive` first |
| `toRefs(state)` before destructure | destructuring `reactive` or `props` |
| `computed` for derived state | a `ref` synced by a `watch` |
| `watch` / `watchEffect` for side effects | a watcher that assigns to a ref |
| `defineProps<T>()` typed | runtime `props: { ... }` objects |
| `defineModel()` (3.4+) | manual `modelValue` prop + emit |
| `useX` composable returning refs | a mixin or a helper returning plain values |
| server data in a query/cache layer | server data mirrored in a Pinia store |
| `:key="item.id"` | `:key="index"` |
| `computed` filter, then `v-for` | `v-if` and `v-for` on one element |
| `shallowRef` for large structures | deep reactivity on data you replace wholesale |
| assert rendered output / emitted event | assert a child mock was called |
