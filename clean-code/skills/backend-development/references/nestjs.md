# NestJS

Conventions for NestJS 10 and 11 on an active Node LTS line (see `nodejs.md` for the runtime baseline). The layering matters more than any single decorator: HTTP stays in controllers, business rules live in services, data access hides behind repositories. Auth, validation, and persistence detail belong to the `api-design.md`, `auth-security.md`, and `database.md` siblings; this file covers how the pieces fit together.

Almost nothing here is version-specific; the decorators and DI model are stable across 10 and 11. Where a difference matters, it is called out inline. The largest change on 11 is the default HTTP adapter moving to Express 5, which tightens route path parsing (wildcards now need a named form such as `*splat`) and query parsing; the layering rules below are unaffected.

## Module organization

Organize by feature domain, not by technical type. One module per domain, each owning its controller, service, repository, DTOs, and entities.

```
src/
├── users/
│   ├── users.module.ts
│   ├── users.controller.ts
│   ├── users.service.ts
│   ├── users.repository.ts
│   ├── dto/
│   └── entities/
├── orders/
│   └── ...
└── shared/          Cross-cutting: guards, interceptors, filters, config
```

- A module exports only what other modules need. Keep the rest private.
- Import a module to consume its exported providers. Do not reach into another module's internals.
- The `AppModule` wires top-level modules and global providers. It holds no business logic.

## Dependency injection

- Register providers in the module's `providers` array. Export the ones other modules depend on.
- Use constructor injection. It makes dependencies explicit and keeps them testable.
- Depend on interfaces or tokens when you need to swap implementations. Use a custom provider token for anything with more than one backing implementation.
- Scope providers as singletons unless request or transient scope is genuinely required; request scope forces the whole dependency chain to be rebuilt per request.

## Controllers, services, repositories

Three layers, one responsibility each.

- **Controllers** handle HTTP and nothing else: route binding, reading params and body, returning a response. No business rules, no data queries.
- **Services** hold business logic and orchestration. They know nothing about HTTP. A service returns domain values or throws domain exceptions, never `Request`/`Response` objects.
- **Repositories** own data access. They translate between the persistence layer and domain objects. Services call repositories; controllers never touch them.

```ts
@Controller('orders')
export class OrdersController {
  constructor(private readonly orders: OrdersService) {}

  @Post()
  create(@Body() dto: CreateOrderDto) {
    return this.orders.create(dto);
  }
}
```

- If a controller method has an `if` in it beyond a trivial guard, the logic belongs in the service.

## DTOs and validation

- Every request body and query is a DTO class with `class-validator` decorators.
- Enable a global `ValidationPipe` with `whitelist`, `forbidNonWhitelisted`, and `transform`.

```ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
    transformOptions: { enableImplicitConversion: false },
  }),
);
```

- `whitelist` strips unknown properties. `forbidNonWhitelisted` rejects them outright so bad payloads fail loudly.
- `transform` turns plain payloads into DTO instances and coerces primitives. Keep implicit conversion off and be explicit with `@Type()`.
- Separate DTOs per operation (`CreateUserDto`, `UpdateUserDto`). Do not reuse one DTO for create and update.

## Entities stay separate from DTOs

- Entities model persistence. DTOs model the API contract. They change for different reasons, so keep them apart.
- Never expose an entity directly in a response. Map to a response DTO so internal fields and relations do not leak.
- Never bind a request straight onto an entity. Validate a DTO, then map.

## Guards

- Guards decide whether a request proceeds. Use them for authentication and authorization.
- Keep the auth logic in the guard; keep the roles or permissions data in the service or token. See `auth-security.md` for the strategy detail.
- Apply guards at the narrowest scope that fits: method, controller, then global.

## Interceptors

- Use interceptors for cross-cutting concerns that wrap the request lifecycle: logging, timing, response shaping, caching, transaction boundaries.
- An interceptor observes and transforms; it does not hold business logic.
- Reach for a global interceptor when the concern is uniform across the app, a bound one when it is local.

## Pipes

- Pipes validate and transform inputs at the parameter boundary.
- Use built-in pipes (`ParseIntPipe`, `ParseUUIDPipe`) for path and query params.
- Write a custom pipe only when the transformation is reusable and input-shaped. Business transformations belong in services.

## Exception filters and error responses

- Throw `HttpException` subclasses (`NotFoundException`, `ForbiddenException`) from services to signal failure. Do not return error-shaped success responses.
- Register one global exception filter that produces a consistent error body across the app: a stable shape with status, message, and a correlation identifier.
- Map domain exceptions to HTTP status in the filter or a small mapping layer, not scattered through controllers.
- Never leak stack traces or internal messages to clients. Log the detail, return a safe message.

## Configuration

- Load config through `ConfigModule`, set global.
- Validate environment variables at startup with a schema. Fail fast on a missing or malformed variable rather than crashing later.
- Access config through `ConfigService`, never `process.env` scattered across the code.
- Keep secrets out of the repo and out of default values. See `auth-security.md`.

```ts
ConfigModule.forRoot({
  isGlobal: true,
  validate: validateEnv, // throws on invalid env
});
```

## Circular dependencies

- Circular dependencies are a design smell. Fix the boundary before reaching for `forwardRef`.
- Extract the shared piece into a third module or move it down into a shared module.
- If two services call each other, one of them owns the wrong responsibility.

## Testing

Follow the contract in `core-development/references/testing-philosophy.md`. NestJS specifics:

- Unit test services with `Test.createTestingModule`, providing mocked repositories and collaborators. Assert the returned value or the state change, not that a mock was called.
- Mock at the boundary: repositories, external clients, the clock. Do not mock the service under test.
- Cover controllers with e2e tests through `supertest`, exercising the real validation pipe, guards, and filters. These prove the wiring the unit tests deliberately skip.
- A service that needs the whole module bootstrapped to test one method has too many dependencies. Fix the seams.

## Quick reference

| Do | Instead of |
|---|---|
| Business logic in services | Logic in controllers |
| Repository for data access | Queries inside services or controllers |
| Response DTO mapped from entity | Return the entity directly |
| Separate create/update DTOs | One DTO reused for both |
| `ValidationPipe` with whitelist + forbidNonWhitelisted | Manual `if` checks on the body |
| Throw `HttpException` from services | Return `{ error: ... }` objects |
| Global exception filter | Per-controller try/catch |
| `ConfigService` with validated env | `process.env.X` scattered around |
| Fix the module boundary | `forwardRef` to patch a cycle |
| Constructor injection | Manual instantiation or service locator |
