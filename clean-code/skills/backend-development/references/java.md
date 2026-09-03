# Java

Modern Java (21+ LTS): records, sealed types, pattern matching, and immutability as the default. The patterns below assume that baseline. Where a rule depends on a version, the version is called out.

The current LTS lines are 17, 21, and 25. Records and sealed types are stable from 17, but record patterns and pattern matching for `switch` only finalized on the 21 line, so treat 21 as the floor for the full pattern-matching style shown here. On 17 you still get records and sealed interfaces; fall back to a chain of `instanceof` checks in place of `switch` deconstruction rather than depending on preview syntax.

## Immutable data with records

- Use a `record` for any data carrier: DTOs, value objects, event payloads, method results.
- Records give you `equals`, `hashCode`, `toString`, and final fields for free. Do not hand-write those on a class when a record fits.
- Validate and normalize in a compact constructor.

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount);
        Objects.requireNonNull(currency);
        if (amount.scale() > 2) {
            throw new IllegalArgumentException("amount exceeds minor unit precision");
        }
    }
}
```

- A record is not for entities with mutable state or a JPA `@Entity`. Use it for the immutable view, not the persistence layer.

## Sealed hierarchies

- Close a hierarchy with `sealed` (Java 17+, refined for pattern matching on 21) when the set of subtypes is known and finite. This lets the compiler enforce exhaustiveness.
- Pair sealed interfaces with records to model a sum type.

```java
public sealed interface PaymentResult permits Approved, Declined, Pending {}

public record Approved(String reference) implements PaymentResult {}
public record Declined(String reason) implements PaymentResult {}
public record Pending(Instant retryAfter) implements PaymentResult {}
```

- Prefer sealed types over an enum plus a status field when each case carries different data.

## Pattern matching

- Use pattern matching in `switch` over a sealed type (stable on Java 21). Omit `default` so the compiler flags a missing case when the hierarchy grows. On 17, fall back to a chain of `instanceof` checks.

```java
String describe(PaymentResult result) {
    return switch (result) {
        case Approved(var reference) -> "approved: " + reference;
        case Declined(var reason)    -> "declined: " + reason;
        case Pending(var retryAfter) -> "pending until " + retryAfter;
    };
}
```

- Use `instanceof` pattern matching instead of a cast after a type check.

```java
if (event instanceof OrderPlaced placed) {
    process(placed.orderId());
}
```

- Add `when` guards for conditional branches rather than nesting `if` inside a case.

## Optional

- Return `Optional<T>` from a method that may legitimately have no result. Never return `null` from such a method.
- Do not use `Optional` for fields, constructor parameters, or method parameters. It costs an allocation and signals nothing useful there; use overloads or a nullable argument with a clear contract.
- Do not call `get()` without a preceding presence check. Use `map`, `orElse`, `orElseThrow`, or `ifPresent`.

```java
return repository.findById(id)
    .map(this::toDto)
    .orElseThrow(() -> new UserNotFoundException(id));
```

- Do not wrap a collection in `Optional`. Return an empty list instead.

## Immutability and final

- Treat fields as `final` by default. Reach for a mutable field only when the state genuinely changes over the object's life.
- Return unmodifiable collections from getters. Copy on the way in and on the way out for defensive boundaries.
- Prefer constructing a new value over mutating an existing one.

## Streams

- Use streams for transformation pipelines: map, filter, reduce, group. They read well when each step is one clear operation.
- Keep the pipeline flat. If a lambda grows past a line or two, extract a named method and reference it.
- Do not use a stream where a plain `for` loop is clearer, and never use `forEach` to mutate external state as a substitute for a loop.
- Prefer `toList()` (Java 16+) over `collect(Collectors.toList())` for an unmodifiable result.

```java
List<String> activeEmails = users.stream()
    .filter(User::isActive)
    .map(User::email)
    .sorted()
    .toList();
```

## Exceptions

- Throw an exception that names the failure. `UserNotFoundException` beats a bare `RuntimeException`.
- Use unchecked exceptions for programming errors and unrecoverable conditions. Reserve checked exceptions for cases a caller can reasonably handle.
- Never swallow an exception. An empty catch block hides bugs. If you catch, act: recover, translate, or rethrow with context.
- Do not catch `Exception` or `Throwable` to be safe. Catch the specific type you can handle.
- Preserve the cause when wrapping: `throw new AppException("...", cause)`.

## Try-with-resources

- Manage every `AutoCloseable` with try-with-resources. Do not close resources in a `finally` block by hand.

```java
try (var connection = dataSource.getConnection();
     var statement = connection.prepareStatement(sql)) {
    return statement.executeQuery();
}
```

## Generics

- Never use a raw type. `List` is `List<String>` or `List<?>`, never bare `List`.
- Use bounded wildcards for API flexibility: `? extends` for producers, `? super` for consumers.

## var

- Use `var` only when the type is obvious from the right-hand side: `var users = new ArrayList<User>()`.
- Do not use `var` when it hides the type: `var result = service.process()` tells the reader nothing. Write the type.
- Never use `var` for a numeric literal where the width matters.

## Naming

- Classes and records in `PascalCase`; methods and fields in `camelCase`; constants in `UPPER_SNAKE_CASE`.
- Name by intent, not by type. `expiredOrders`, not `orderList2`.
- Boolean methods read as a predicate: `isActive`, `hasAccess`, `canRetry`.
- Do not prefix interfaces with `I` or suffix implementations with `Impl` unless one implementation among several needs a distinguishing name.

## equals and hashCode

- Let a record generate them. That is the reason records exist.
- On a non-record class, generate both together or neither. A mismatched pair breaks hash-based collections.
- Base equality on identity fields only, and keep those fields immutable.

## Dependency injection

- Inject collaborators through the constructor. Depend on interfaces, not concrete singletons.
- Avoid static singletons and service locators. They hide dependencies and block testing.
- A class that reaches into a global static state cannot be tested in isolation. Pass the dependency in.

## Methods

- One method, one job. If the name needs "and", split it.
- Keep methods short enough to read without scrolling. Extract a named helper before a method sprouts nested branches.
- Return early to avoid deep nesting. Guard clauses at the top, the main path unindented.

## Quick reference

| Do | Instead of |
|---|---|
| `record Point(int x, int y)` | class with fields, getters, `equals`, `hashCode` |
| `sealed interface` + records | enum with a type-specific payload field |
| `switch` pattern match, no `default` | chain of `instanceof` and casts |
| `if (o instanceof User u)` | `if (o instanceof User) { User u = (User) o; }` |
| return `Optional<T>` | return `null` |
| `Optional` as return only | `Optional` field or parameter |
| return empty list | return `Optional<List<T>>` |
| `final` field by default | mutable field by default |
| `.toList()` | `.collect(Collectors.toList())` |
| specific `AppException` | bare `RuntimeException` |
| try-with-resources | manual `finally { close() }` |
| `List<User>` | raw `List` |
| `var x = new HashMap<K,V>()` | `var x = service.call()` |
| constructor injection | static singleton / service locator |
