# Architecture

How to structure an application so business rules stay independent of frameworks, databases, and delivery mechanisms. This covers the cross-cutting design rules. For naming, function size, and composition see `clean-code.md`; for HTTP and REST specifics see the backend `api-design.md`.

## The dependency rule

Source dependencies point inward only. An inner layer never knows about an outer one.

```
Frameworks and drivers    outermost: database, web framework, external APIs
  Interface adapters      controllers, presenters, repository implementations
    Use cases             application-specific business rules
      Entities            enterprise-wide business rules, innermost and most stable
```

- Crossing inward: pass plain data (DTOs, primitives). Never pass an ORM entity or an HTTP request object into a use case or entity.
- Crossing outward: the use case defines an interface (`UserRepository`); the outer layer implements it. The dependency still points inward even though control flows outward.
- Consequence: use cases are testable with no database, no web server, no framework. Only the outermost layer imports Express, TypeORM, NestJS, or Spring.

## Separation of concerns

| Concern | Layer | What lives here |
|---|---|---|
| Business rules | Domain, use cases | Eligibility, pricing, invariant enforcement |
| Orchestration | Use cases, services | Fetch user, check balance, create order, send confirmation |
| Data access | Infrastructure | SQL, ORM repositories, cache clients |
| Delivery | Presentation | Routes, request parsing, response shaping |
| Integrations | Infrastructure | Payment client, mailer, object storage |

Violation signals:

- A query built inside a controller.
- Business logic inside a database query.
- A controller calling `repository.save()` directly, bypassing the use case.
- An HTTP status decision made inside a domain entity.

## Dependency injection

- Never construct a dependency inside the class that uses it. `new PaymentClient()` inside `PaymentService` makes it untestable without the real client.
- Prefer constructor injection: dependencies are explicit, required, and the object is valid once constructed.
- Wire the graph at startup through the framework's container (NestJS, Spring, .NET). Do not `new` a service, repository, or external client in application code.
- Service Locator is an anti-pattern. Looking a dependency up from a global registry hides it and forces the full container into tests.

## Command-query separation

A method either returns a value (a query, no side effects) or changes state (a command, no meaningful return). Never both. `validateInput()` must not also persist. This keeps reasoning and testing simple, and stops surprises where reading a value mutates state.

## Error handling architecture

Use a typed error hierarchy, not string matching on messages.

```
AppError
  ValidationError        field-level input error (400)
  NotFoundError          entity not found (404)
  ConflictError          state conflict or duplicate (409)
  UnauthorizedError      missing or invalid auth (401)
  ForbiddenError         insufficient permission (403)
  InfrastructureError
    DatabaseError
    ExternalServiceError
  UnexpectedError        catch-all for the unknown (500)
```

- Handle an error at the layer that has the context to respond. Infrastructure maps low-level exceptions to domain errors; presentation maps domain errors to status codes.
- Use a Result type for expected failures (`Result<User, ValidationError>`). Reserve exceptions for the genuinely unexpected.
- Centralize unexpected-error handling in one global handler (a NestJS exception filter, Express error middleware, a Spring `@RestControllerAdvice`). It logs with a request id and returns a sanitized response.
- Never expose stack traces, SQL messages, or internal class names to a client.

## Keep the domain model rich

Domain objects hold domain logic: validations, calculations, invariants. A model that is only fields with getters and setters, with all behavior in a service, is anemic.

```
// Anemic: Order is { id, items, status }; OrderService mutates its fields directly.

// Rich:
order.addItem(item)   // enforces capacity and price rules
order.cancel()        // allowed only before shipment
order.total()         // computes total with applicable discounts
```

Services orchestrate across aggregates. They do not own the business logic that belongs on the entity.

## Do / Instead of

| Do | Instead of |
|---|---|
| Depend on an interface the use case owns | call a concrete gateway from the core |
| Pass DTOs across a boundary | pass ORM entities or request objects inward |
| Constructor injection wired by the container | `new` a service or client in app code |
| Query or command, never both | a getter that also mutates state |
| Typed error hierarchy + one global handler | stringly-typed errors and ad hoc try/catch |
| Behavior on the entity | an anemic model with a fat service |
