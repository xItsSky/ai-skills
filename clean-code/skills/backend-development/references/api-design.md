# API Design

Conventions for HTTP/REST APIs that stay predictable as they grow. Framework-agnostic: the same rules hold in NestJS, plain Node, Java, or Spring Boot.

## Resource naming

- Model URLs around resources (nouns), not actions. The HTTP method is the verb.
- Use plural nouns for collections: `/orders`, `/orders/42`, `/orders/42/items`.
- Keep paths lowercase with hyphens: `/purchase-orders`, not `/purchaseOrders` or `/purchase_orders`.
- Nest to show ownership, but stop at two levels. Past that, link by ID instead of deepening the path.
- Reserve non-resource verbs for genuine operations that don't map to CRUD: `POST /orders/42/cancel`. Don't reach for this when a state field update would do.

```
GET    /orders          list
POST   /orders          create
GET    /orders/42       read one
PUT    /orders/42       replace
PATCH  /orders/42       partial update
DELETE /orders/42       remove
```

## HTTP methods and status codes

- `GET` is safe and never mutates. `PUT`, `DELETE`, and `GET` are idempotent; `POST` is not.
- Return the status that matches the outcome, not `200` for everything.

| Outcome | Status |
|---|---|
| Read or update succeeded | `200` |
| Resource created | `201` + `Location` header |
| Accepted for async processing | `202` |
| Success with no body | `204` |
| Malformed request or failed validation | `400` |
| Not authenticated | `401` |
| Authenticated but not allowed | `403` |
| Resource does not exist | `404` |
| Conflict with current state (duplicate, version clash) | `409` |
| Rate limit exceeded | `429` |
| Unexpected server fault | `500` |

- Never return `200` with an error payload inside. The status code is part of the contract.
- Reserve `401` for missing or invalid credentials, `403` for a known caller who lacks permission.

## Error format

- Use one error shape for the whole API. Adopt RFC 9457 (`application/problem+json`), which obsoletes RFC 7807 and keeps the same field set.

```json
{
  "type": "https://api.example.com/problems/insufficient-funds",
  "title": "Insufficient funds",
  "status": 403,
  "detail": "Account 8821 has a balance of 12.00, the transfer requires 50.00.",
  "instance": "/accounts/8821/transfers"
}
```

- `title` is stable and generic; `detail` is specific to this occurrence. Add fields for machine-readable data (e.g. a `errors` array for field validation).
- Never expose stack traces, SQL, internal hostnames, or framework exception names in an error body.

## Validation at the boundary

- Validate and parse every incoming request before it reaches business logic. Reject early with `400` and a per-field list.
- Bind input to a request DTO. Don't accept raw untyped bodies into services.
- Whitelist known fields and strip the rest. An unknown field is a `400`, not a silent pass-through.
- Validate types, ranges, formats, and required-ness at the edge so the domain can assume clean input.

## Contracts separate from persistence

- Request and response DTOs are distinct from database entities. Never serialize an ORM entity straight to the client.
- Map entity to response DTO explicitly. This keeps the wire contract stable when the schema changes and stops accidental leaks of internal columns.
- Expose only what a client needs. Password hashes, internal flags, and foreign keys the client can't use stay out of the response.

## Pagination, filtering, sorting

- Paginate any collection that can grow. Never return an unbounded list.
- Prefer cursor (keyset) pagination for large or fast-moving data; offset pagination drifts and slows down on deep pages.
- Use query parameters and keep them consistent across endpoints: `?limit=50&cursor=...`, `?sort=-createdAt`, `?status=open`.
- Return pagination metadata (next cursor, or total when it's cheap to compute).
- Cap `limit` server-side. A client asking for 100000 gets the max, not an OOM.

## Versioning

- Version from day one. Pick one scheme and hold it: URL prefix (`/v1/orders`) is the most explicit and cache-friendly.
- Bump the version only for breaking changes. Adding an optional field or a new endpoint is backward-compatible and needs no bump.
- Keep the old version alive during a documented deprecation window. Don't break live clients on deploy.

## Idempotency for writes

- `POST` that creates a resource (payments, orders) should accept an `Idempotency-Key` header. Store the key with the result and return the same response on retry instead of creating a duplicate.
- This makes client retries and at-least-once delivery safe.

## Casing, dates, and consistency

- Pick one casing for JSON keys and use it everywhere. `camelCase` is the common default for JSON.
- Timestamps are ISO 8601 in UTC: `2026-08-31T14:05:00Z`. Never send server-local time or ambiguous epochs without units.
- Money is an integer of minor units plus a currency code, or a decimal string. Never a float.
- Booleans are booleans, not `"true"` strings or `0`/`1`.

## Documentation

- Describe every endpoint with OpenAPI. Keep the spec in sync with the code (generate it from the code or annotations where the framework supports it).
- Document status codes, the error shape, auth requirements, and every field. The spec is the contract clients build against.

## Quick reference

| Do | Instead of |
|---|---|
| `GET /orders/42` | `GET /getOrder?id=42` |
| Plural nouns: `/orders` | Verbs in paths: `/createOrder` |
| `201` + `Location` on create | `200` with the body only |
| `403` for forbidden, `401` for unauthenticated | `401` for both |
| RFC 9457 `problem+json` errors | Ad-hoc `{ error: "..." }` shapes per route |
| Request/response DTOs | Serializing ORM entities directly |
| Cursor pagination on large sets | Deep `offset`/`limit` scans |
| ISO 8601 UTC timestamps | Server-local or unit-less epoch times |
| URL version prefix `/v1` | Breaking a live contract in place |
| `Idempotency-Key` on payment writes | Duplicate resources on client retry |
