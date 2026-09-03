# Authentication and Authorization

Two distinct problems. Authentication proves who the caller is. Authorization decides what that caller is allowed to do. Solve both, on every protected path, on the server.

## Authentication vs authorization

- Authentication: identity. "Is this really user 88?"
- Authorization: permission. "Is user 88 allowed to delete order 42?"
- A valid token answers the first question and says nothing about the second. Check both.

## Enforce server-side, every time

- Every protected endpoint verifies identity and permission on the server. Client-side gating is a convenience, not a control.
- Hiding a button in the UI is not authorization. The endpoint behind it must reject an unauthorized call.
- Default to deny. A path with no explicit check is a hole, not a public route.

## Sessions vs tokens

- Server-side sessions: state lives on the server, the client holds an opaque session ID. Easy to revoke, needs shared session storage to scale.
- Tokens (JWT): stateless, the claims travel in the token. Scales without shared state, but hard to revoke before expiry.
- For browser clients, put the credential in an `HttpOnly`, `Secure`, `SameSite` cookie so JavaScript can't read it. For service-to-service, a bearer token in the header is fine.

### JWT handling

- Issue a short-lived access token (minutes) plus a longer-lived refresh token. Rotate the refresh token on use.
- Validate every token before trusting it: verify the signature, then check `exp`, `iss`, and `aud`. A token that only decodes is not a token that's valid.
- Reject `alg: none` and never let the client pick the algorithm. Pin it server-side.
- Keep tokens out of URLs and out of `localStorage`. Both leak.
- Keep a revocation path (short expiry plus a refresh-token denylist) so a compromised session can be cut off.

## Password storage

- Hash passwords with a slow, salted algorithm built for it: argon2id or bcrypt.
- Never store plaintext. Never use a fast general-purpose hash (MD5, SHA-256) for passwords; they're built for speed, which is exactly what an attacker wants.
- Let the library manage the per-password salt. Tune the work factor so a single hash takes real time on your hardware, and raise it as hardware improves.
- On login, compare with a constant-time check. Don't short-circuit on the first mismatched byte.

## Least privilege

- Grant the minimum permission the operation needs. A read endpoint doesn't need write scope.
- Enforce role and permission checks at the operation, tied to the specific resource. "Is an admin" is coarse; "may cancel this order" is the real question.
- Check ownership on every object access. That user 88 is authenticated doesn't mean order 42 is theirs.

## Rate limiting and lockout

- Rate-limit authentication endpoints (login, refresh, password reset) to blunt credential stuffing and brute force.
- Lock out or add backoff after repeated failures on an account. Return the same generic message for wrong password and unknown user so the endpoint doesn't confirm which accounts exist.
- Rate-limit the broader API too, keyed per client, to contain abuse.

## Secure headers

- Send `Strict-Transport-Security` and serve over HTTPS only.
- Set `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, and a restrictive `Referrer-Policy`.
- Scope CORS to known origins. Never reflect an arbitrary `Origin` back with credentials allowed.

## Common attacks

- Injection: use parametrized queries and validate input at the boundary. Never build a query from raw input. (See `database.md`.)
- CSRF: only relevant for cookie-based auth. Use `SameSite` cookies plus a CSRF token for state-changing requests. Header-based bearer auth isn't exposed to CSRF.
- IDOR / broken object-level authorization: verify the caller owns or may access the specific object every time. Don't trust an ID from the request to imply permission.
- Mass assignment: bind input to an explicit DTO and whitelist fields. Don't let a request set `role` or `isAdmin` because the field happens to exist.

## Secrets

- Never log secrets, tokens, passwords, or full card/PII data. Redact them before anything reaches a log sink.
- Keep secrets out of the repository and out of code. Load them from environment or a secrets manager.
- Rotate credentials and signing keys on a schedule and immediately on suspected compromise. Support key rotation without downtime (accept the old and new key during the overlap).

## Quick reference

| Do | Instead of |
|---|---|
| Check identity and permission server-side | Trusting a hidden UI control |
| Default deny on every route | Assuming unlisted routes are safe |
| argon2id / bcrypt for passwords | Plaintext, MD5, or SHA-256 |
| Short access token + rotating refresh | One long-lived token that can't be revoked |
| Verify signature, `exp`, `iss`, `aud` | Trusting a token that merely decodes |
| `HttpOnly` `Secure` cookie in browsers | Token in `localStorage` or the URL |
| Object-level ownership checks | Trusting an ID to imply access (IDOR) |
| Rate limit + lockout on auth endpoints | Unlimited login attempts |
| Whitelist DTO fields | Binding the whole request body |
| Secrets from a vault/env, redacted in logs | Secrets in the repo or printed to logs |
