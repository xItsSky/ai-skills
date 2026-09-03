# Code Documentation

Documentation that lives next to the code and stays true as the code changes. This is about doc comments on the public surface, not prose guides. For inline comments and the why-not-what rule, see `clean-code.md`. For HTTP contract docs, see backend `api-design.md`.

## What to document

- Every public service method, utility, and exported function carries a doc comment: JSDoc for TypeScript and JavaScript, Javadoc for Java, the language equivalent elsewhere.
- Document the non-obvious parameters, the return value, and the exceptions or errors a caller must handle. Skip the obvious ones rather than restating the signature.
- Do not document private internals for the sake of coverage. A doc comment that repeats the code is noise that rots out of sync.

```ts
/**
 * Charges a customer for an order and records the payment.
 *
 * @param orderId - Order to charge. Must be in `PENDING` state.
 * @param idempotencyKey - Prevents a double charge on retry.
 * @returns The recorded payment, including the provider reference.
 * @throws OrderNotPayableError when the order is not in `PENDING`.
 */
async chargeOrder(orderId: string, idempotencyKey: string): Promise<Payment> {
```

## Keep it honest

- Update the doc comment in the same change as the code. A stale comment is worse than none because it misleads with authority.
- Describe behavior and contract, not implementation steps. The caller reads the doc; the diff shows the how.
- Document thrown exceptions and error cases explicitly. They are part of the contract a caller depends on.

## API documentation

- Expose an OpenAPI description for every HTTP endpoint. Frameworks generate it from decorators: `@nestjs/swagger` (`@ApiOperation`, `@ApiResponse`, `@ApiProperty` on DTO fields) for NestJS, springdoc for Spring Boot.
- Annotate every input and every DTO property so the generated spec matches the real contract. See `api-design.md` for what the spec must state.

## Project docs

- Read the repository's docs folder before building something that may already be documented.
- Update it when an endpoint, module, behavior, or config changes. Add to it when something is missing. Documentation is part of a finished feature, not a follow-up.

## Do / Instead of

| Do | Instead of |
|---|---|
| JSDoc/Javadoc on every public method | undocumented public API |
| Document params, return, and thrown errors | restate the signature in prose |
| Update the doc in the same commit as the code | leave a stale comment behind |
| Generate API docs from decorators | hand-written docs that drift |
| Document the why and the non-obvious | comment every trivial line |
