# Spring Boot

Conventions for a Spring Boot 3.x service on Java 21+. The rules assume a layered application with a clear boundary between the web edge, business logic, and persistence.

Boot 3 requires Java 17 as its floor and moved the persistence and validation APIs from the `javax.*` namespace to `jakarta.*`; the imports in this file assume that. On Boot 2 the same patterns hold, but the annotations live under `javax.persistence` and `javax.validation`, and `ProblemDetail` is not available, so use a custom error body there. Where a rule depends on a version, it is called out inline.

## Layered architecture

```
controller  →  service  →  repository
   (web)       (logic)      (data)
```

- Controllers handle HTTP: bind the request, validate, delegate, shape the response. Nothing more.
- Services own the business logic and the transaction boundary.
- Repositories own persistence. They run queries and return entities.
- The dependency arrow points one way. A repository never calls a service; a service never touches `HttpServletRequest`.

## Dependency injection

- Constructor injection only. Declare collaborators `final` and let the constructor set them.
- Do not use field `@Autowired`. It hides dependencies, blocks `final`, and forces reflection in tests.
- With one constructor, Spring wires it automatically. No annotation needed.

```java
@Service
public class OrderService {
    private final OrderRepository orders;
    private final PaymentClient payments;

    public OrderService(OrderRepository orders, PaymentClient payments) {
        this.orders = orders;
        this.payments = payments;
    }
}
```

## Controllers

- Keep controllers thin. No business logic, no repository calls, no transaction management.
- Accept and return DTOs, never entities. Use records for both request and response bodies.
- Validate request bodies with `@Valid` and Bean Validation constraints. Let the framework reject bad input before your code runs.

```java
@PostMapping
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
    var order = orderService.place(request);
    return ResponseEntity.status(CREATED).body(order);
}

public record CreateOrderRequest(
    @NotBlank String customerId,
    @NotEmpty List<@Valid OrderLine> lines
) {}
```

## Entities stay out of the API

- Never serialize a JPA entity to the client and never bind a request straight onto one. The API contract and the schema evolve for different reasons; coupling them leaks persistence details and invites lazy-loading traps.
- Map entity to DTO in the service or a dedicated mapper. Keep the mapping explicit.

## Transactions

- Put `@Transactional` on the service method, not the controller and not the repository.
- Mark read paths `@Transactional(readOnly = true)`. It lets the provider skip dirty checking and signals intent.
- Keep the transaction scoped to the unit of work. Do not hold one open across a remote call or a slow external I/O.
- Self-invocation does not go through the proxy, so an internal call to a `@Transactional` method in the same bean gets no transaction. Split the method out.

## Repositories

- Use Spring Data interfaces. Declare the query surface; let derived queries and `@Query` do the work.
- Return `Optional<T>` for single lookups and `Page<T>` for collections.
- Keep business logic out of repositories. A repository fetches and stores; it does not decide.

## Configuration

- Bind related properties into a typed `@ConfigurationProperties` class. Validate them with Bean Validation at startup.
- Do not scatter `@Value` across the codebase. It spreads config knowledge and skips validation.
- Use Spring profiles for environment differences. Keep secrets out of committed files; supply them through the environment.

```java
@ConfigurationProperties(prefix = "payment")
@Validated
public record PaymentProperties(
    @NotNull URI endpoint,
    @Positive Duration timeout
) {}
```

## Error handling

- Centralize exception-to-response mapping in one `@RestControllerAdvice`. Do not catch and format errors in each controller.
- Return a consistent error body across the API. Prefer RFC 9457 `ProblemDetail` (Boot 3+); on Boot 2 return a custom error record instead.
- Map domain exceptions to the right status: not-found to 404, validation to 400, conflict to 409.

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    public ProblemDetail handleNotFound(EntityNotFoundException ex) {
        var problem = ProblemDetail.forStatus(NOT_FOUND);
        problem.setTitle("Resource not found");
        problem.setDetail(ex.getMessage());
        return problem;
    }
}
```

## Domain logic placement

- Business rules live in the service layer. Not in controllers, not in repositories, not in mappers.
- A controller that branches on business conditions is doing the service's job. Move the decision down.

## Immutability

- Prefer immutable DTOs (records) and immutable configuration.
- Do not expose mutable internal state through a response object. Build the response from the current state and return it.

## Pagination

- Never return an unbounded collection from an endpoint. Accept `Pageable` and return `Page<T>`.
- Set a sane default and maximum page size. Cap the size the client can request.

```java
@GetMapping
public Page<OrderResponse> list(@PageableDefault(size = 20) Pageable pageable) {
    return orderService.findAll(pageable);
}
```

## N+1 queries

- Watch for the N+1 pattern: one query for the parents, then one per child association during rendering.
- Fetch associations you need in a single query with an entity graph (`@EntityGraph`) or a fetch join. Do not rely on eager mapping globally.
- Keep associations `LAZY` by default and load eagerly per use case where the data is actually needed.

```java
@EntityGraph(attributePaths = "lines")
List<Order> findByCustomerId(String customerId);
```

## Testing

The coverage contract and what counts as a real test live in `core-development/references/testing-philosophy.md`. Spring specifics:

- Use slice tests to keep them fast and focused. `@WebMvcTest` for the web layer with `MockMvc`; `@DataJpaTest` for repositories and queries.
- Reserve `@SpringBootTest` for integration tests that need the full context wired.
- Drive controller tests through `MockMvc`: assert status, response body, and validation failures. Mock the service.
- Test persistence against a real database with Testcontainers, not an in-memory substitute. H2 hides dialect and constraint behavior that breaks in production.
- Write a test that catches the N+1 regression: assert the query count for a known fetch.

## Quick reference

| Do | Instead of |
|---|---|
| constructor injection, `final` fields | field `@Autowired` |
| thin controller, logic in service | business logic in controller |
| DTO records at the API edge | JPA entity as request/response |
| `@Valid` + Bean Validation | manual `if` checks in the controller |
| `@Transactional` on the service | `@Transactional` on controller/repository |
| `@Transactional(readOnly = true)` for reads | read-write transaction for a query |
| `@ConfigurationProperties` | scattered `@Value` |
| one `@RestControllerAdvice` + `ProblemDetail` | per-controller try/catch |
| `Pageable` + `Page<T>` | unbounded `List<T>` endpoint |
| `@EntityGraph` / fetch join | lazy association hit in a loop |
| Testcontainers real DB | H2 in-memory for JPA tests |
| slice tests (`@WebMvcTest`, `@DataJpaTest`) | `@SpringBootTest` for everything |
