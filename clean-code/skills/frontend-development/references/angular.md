# Angular

Modern Angular (v20+): standalone components, signals, native control flow, `inject()`. The patterns below assume that baseline. Where a rule depends on a version, the version is called out.

## Project structure

```
src/app/
├── core/         Global singletons: services, stores, layout
├── shared/       Atoms and utilities reusable across the app
├── feature/      Business features, self-contained
└── app.config.ts Bootstrap and providers
```

Two rules keep the graph acyclic:

- `shared/` may be imported by `feature/`, never the reverse.
- A `feature/` never imports another `feature/`. Shared needs move down into `shared/`.

### Core layer

```
core/
├── components/       Global layout: header, error pages
└── providers/
    ├── data-services/  Raw HTTP (repositories), no business logic
    ├── services/       Application logic and orchestration
    ├── stores/         Global state via @ngrx/signals (signalStore)
    └── helpers/        Technical utilities for core
```

- Data-services do HTTP and nothing else.
- Services orchestrate data-services and hold reusable logic.
- Stores use `signalStore` and are provided at the root. A core store never depends on a feature store.

### Shared layer

```
shared/
├── components/   Generic atoms and molecules (form-error, key-value)
├── composable/   inject()-based helpers, CVA, pure functions
├── directives/
├── models/       Interfaces and types only, no classes with logic
└── pipes/
```

- Shared components are headless or only loosely bound to the UI kit. They expose `input()` / `output()`.
- Composables (`*.composable.ts`) are pure functions or `inject()` helpers. No components, no directives.
- Models are `type`/`interface` only.
- Pipes are `pure: true` by default. An impure pipe must be justified in a comment.
- Every shared entity has a `*.spec.ts`.

### Feature layer

```
feature/
├── feature.routes.ts
└── <domain>/                 cases/, calendar/, dashboard/
    ├── <domain>.routes.ts
    ├── <domain>.resolver.ts
    ├── list/                 Page component
    ├── details/
    │   ├── components/       Sections and organisms of the page
    │   └── details.component.*
    └── shared/               Shared within this domain only
        └── <domain>.configuration.ts
```

- Each page is a standalone component. It holds no HTTP logic; it delegates to a store or service.
- A domain's `shared/` holds only what its own views share. It never bubbles up to `app/shared/`.
- Resolvers fetch route data. They transform nothing.
- Configurations (`*.configuration.ts`) centralize domain constants: statuses, dropdown options.

## Routing

- Each domain owns its `*.routes.ts`.
- Lazy loading is mandatory: load domains through `loadChildren` or `loadComponent`.
- Declare guards and resolvers in the `Route[]` definitions, not in modules.

## TypeScript

- Strict type checking on.
- Let inference work when the type is obvious.
- No `any`. Use `unknown` when a type is genuinely open, then narrow.

## Components

- Standalone only. Do not set `standalone: true` in the decorator; it is the default from v20.
- Do not set `changeDetection: OnPush` explicitly; it is the default from v22.
- One responsibility per component. Keep them small.
- Use `input()` and `output()` functions, not the decorators.
- Use `computed()` for derived state.
- Inline templates for small components; external template/style paths are relative to the `.ts` file.
- Put host bindings in the `host` object of the decorator. Do not use `@HostBinding` or `@HostListener`.
- Use `NgOptimizedImage` for static images. It does not apply to inline base64.

## Forms

- Prefer Signal Forms (`@angular/forms/signals`) for new forms; stable from v22, with signal state, typed field access, and schema validation.
- Without Signal Forms, use Reactive forms, not template-driven.

## State

- Signals for local component state.
- `computed()` for anything derived. Keep transformations pure.
- Mutate signals with `set` or `update`, never `mutate`.

## Templates

- Keep them declarative. Push logic into the component or a computed.
- Native control flow (`@if`, `@for`, `@switch`), not the structural directives.
- Bind with `[class.x]` and `[style.x]`, not `ngClass` / `ngStyle`.
- Use the `async` pipe for observables.
- Do not assume globals like `new Date()` are available in the template.

## Services

- One responsibility per service.
- Singletons: prefer the `@Service` decorator (v22+) over `@Injectable({ providedIn: 'root' })` for new code.
- Inject with `inject()`, not constructor parameters.

## Quick reference

| Do | Instead of |
|---|---|
| `input()` / `output()` | `@Input()` / `@Output()` |
| `host: { ... }` | `@HostBinding` / `@HostListener` |
| `@if` / `@for` / `@switch` | `*ngIf` / `*ngFor` / `*ngSwitch` |
| `[class.active]` | `ngClass` |
| `signal.update(...)` | `signal.mutate(...)` |
| `inject(Foo)` | `constructor(private foo: Foo)` |
| `loadComponent` | eager route component |
