# Node.js

Conventions for Node.js backends on an active LTS line (20 or 22). Node runs one thread for your JavaScript. Almost every rule here follows from that: keep the event loop free, handle every async failure, and shed load under pressure. Framework-specific structure lives in `nestjs.md`; validation, auth, and persistence detail live in the `api-design.md`, `auth-security.md`, and `database.md` siblings.

The baseline assumes a global `fetch`, `AbortController`, `AbortSignal.timeout`, the Web Streams API, and `node:`-prefixed core imports, all stable on Node 20 and 22. Where a rule depends on a version, it is called out inline. On an older line, check availability before using these: global `fetch` and `AbortController` land as stable on Node 18+; before that, pull `fetch` from `undici` and `AbortController` from a polyfill. `AbortSignal.timeout` arrived later than the controller itself, so on an early 18 build fall back to a manual `setTimeout` that calls `abort()`.

## Modules

- Default to ESM (`import`/`export`) with `"type": "module"` in `package.json`. It is the standard module system and the one the examples here use.
- Prefix core imports with `node:` (`node:fs`, `node:stream/promises`). The prefix is unambiguous and blocks a userland package from shadowing a builtin.
- Under ESM there is no `__dirname` or `require`; derive paths from `import.meta.url`, and use `import.meta.dirname` where the runtime provides it (Node 20.11+ / 21.2+). On a CommonJS codebase, keep `require`/`module.exports` consistent rather than mixing the two.

## Async

- Use `async`/`await`. It reads top to bottom and keeps error handling in one place.
- Never use callbacks for new code. Wrap legacy callback APIs with `util.promisify` once, at the edge.
- Run independent async work concurrently with `Promise.all`. Sequential `await` in a loop is only correct when each step depends on the previous.
- Use `Promise.allSettled` when partial failure is acceptable and you need every result.

```ts
// independent work runs together
const [user, orders] = await Promise.all([
  users.findById(id),
  orders.findByUser(id),
]);
```

## Never block the event loop

- One synchronous CPU-heavy call stalls every other request. Keep handlers non-blocking.
- Offload heavy computation to a worker thread, a child process, or a queue. Hashing, image work, large parsing, and crypto all qualify.
- Avoid synchronous filesystem and crypto calls (`readFileSync`, `pbkdf2Sync`) on the request path. Use the async variants.
- Watch out for accidental O(n²) work and giant JSON parses inside a request; they block just as hard as an infinite loop.

## Handle every rejection and stream error

- Every promise has a failure path. Await it inside a `try/catch` or attach a `.catch`. An unhandled rejection can crash the process.
- Streams emit `error` events that do not surface as exceptions. Attach an `error` handler to every stream, or use `stream.pipeline` which propagates and cleans up.
- Register `process.on('unhandledRejection')` and `process.on('uncaughtException')` as a last-resort net that logs and exits. They are safety nets, not error handling.

```ts
import { pipeline } from 'node:stream/promises';

await pipeline(source, transform, destination); // errors propagate, resources close
```

## Errors

- Throw `Error` instances, never strings. Preserve the stack.
- Define typed error classes for domain failures (`NotFoundError`, `ValidationError`) so callers can branch on type instead of parsing messages.
- Distinguish operational errors (a failed request, a bad input) from programmer errors (a bug). Recover from the first, crash on the second.
- Route errors to one central handler that decides the response and the log. Do not swallow errors in scattered `catch` blocks that only log and continue.
- Preserve the cause with `new Error(msg, { cause })` when wrapping.

## Logging

- Use a structured logger (`pino`, `winston`) that emits JSON. Structured logs are queryable; `console.log` is not.
- No `console.log` in production paths. It is unstructured, synchronous on some streams, and hard to level.
- Attach context: a request or correlation id, not raw secrets or tokens.
- Log at the right level and let the environment set the threshold. Debug noise off in production.

## Configuration and secrets

- Read all config and secrets from the environment. Nothing sensitive in the repo.
- Validate the environment once at startup against a schema. Exit immediately on a missing or malformed value; a process that boots with bad config fails later and worse.
- Parse env into a typed config object and pass that around. Do not read `process.env` deep in the code.

## Graceful shutdown

- Listen for `SIGTERM` and `SIGINT`. Orchestrators send `SIGTERM` before killing the container.
- On signal: stop accepting new connections, let in-flight requests finish within a timeout, close the DB pool and other resources, then exit.
- Set a hard deadline. If draining hangs, force-exit so the process does not linger.

```ts
process.on('SIGTERM', async () => {
  server.close();            // stop new connections
  await drainInFlight(15_000);
  await db.close();
  process.exit(0);
});
```

## Backpressure and streams

- Stream large payloads instead of buffering them into memory. `pipe`/`pipeline` respect backpressure automatically.
- Do not read a whole file or response into a string when you can stream it through.
- When you write to a stream manually, honour the return value of `write` and wait for `drain`. Ignoring it lets memory grow without bound.

## Cancellation and timeouts

- Use `AbortController` to cancel in-flight work: `fetch`, timers, streams, and any API that takes a `signal`.
- Put a timeout on every outbound network call. A slow dependency should fail your request, not hang it forever.
- For a plain timeout, `AbortSignal.timeout(ms)` is the one-liner; use a manual controller when you also need to abort on another event, and `AbortSignal.any([...])` to combine signals (added mid-20 line; on an older build, wire a manual `setTimeout` + `abort()` instead).
- Propagate the incoming request's signal down the call chain so a client disconnect cancels the work it triggered.

```ts
// combine a request timeout with the caller's own signal
return await fetch(url, {
  signal: AbortSignal.any([req.signal, AbortSignal.timeout(5_000)]),
});
```

## Avoid global mutable state

- No mutable module-level state shared across requests. It leaks data between users and breaks under concurrency.
- Pass dependencies explicitly. Request-scoped data travels with the request or through `AsyncLocalStorage`, not a shared variable.
- Reserve module-level constants for genuinely immutable config.

## Layering without a framework

Even in plain Node, keep the same separation NestJS enforces:

- **Routes/controllers** parse the HTTP request and shape the response. No business rules.
- **Services** hold business logic. They know nothing about HTTP.
- **Repositories** own data access behind a small interface.

This keeps services unit-testable without a server and lets you swap the HTTP layer or the database without touching business logic.

## Security basics

- Validate and sanitize every input at the boundary. Never trust the client. See `api-design.md`.
- Never `eval` or `new Function` on input, and avoid dynamic `require` from user data.
- Keep dependencies patched. Run `npm audit` in CI and pin with a lockfile; most Node vulnerabilities arrive through the tree.
- Set request size limits and timeouts so a single client cannot exhaust memory or connections.

## Quick reference

| Do | Instead of |
|---|---|
| `async`/`await` | Callbacks or long `.then` chains |
| `Promise.all` for independent work | Sequential `await` in a loop |
| Offload CPU work to a worker | Heavy compute on the event loop |
| `stream.pipeline` | Manual `pipe` without error handling |
| Typed error classes + central handler | Throwing strings, scattered `catch` |
| Structured JSON logger | `console.log` in production |
| Validate env at startup | Reading `process.env` lazily and hoping |
| Drain on `SIGTERM` | Hard exit that drops requests |
| `AbortSignal.timeout` / `AbortController` | Unbounded outbound calls |
| ESM + `node:` core imports | CommonJS by default, bare `fs` imports |
| Explicit dependencies / `AsyncLocalStorage` | Global mutable state |
