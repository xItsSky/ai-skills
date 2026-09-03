# Redis

Conventions for Redis as a cache and derived store. The generic data-layer rules live in `database.md`; this file covers what is specific to an in-memory, single-threaded key-value engine. Frame everything around one fact: Redis is fast because it is single-threaded and holds data in memory. That gives you microsecond operations and takes away the freedom to run heavy commands or treat it as durable truth.

## Pick the data structure for the access pattern

Redis is not just strings. Choosing the wrong structure forces awkward code and wastes memory.

- **String** for a single value or a serialized blob: a cached response, a counter (`INCR`), a flag.
- **Hash** for an object with fields you read or update individually. Cheaper and clearer than storing one JSON string you rewrite whole.
- **List** for a queue or a bounded recent-items log (`LPUSH` + `LTRIM`).
- **Set** for membership and uniqueness: has this user been seen, dedupe a batch.
- **Sorted set** for anything ranked or time-ordered: leaderboards, a priority queue, a rate-limit window keyed by score.
- **Stream** for an append-only event log with consumer groups, when you need at-least-once delivery and replay rather than a plain list.

## Consistent key naming

- Namespace keys with a delimiter, conventionally a colon: `user:1042:session`, `cache:product:88`.
- Keep the scheme uniform across the codebase so keys are greppable and a prefix scan targets exactly one concern.
- Encode the type or purpose in the prefix. `ratelimit:ip:203.0.113.4` tells you what it is and what removes it.
- Never build a key from unescaped user input that could collide across namespaces.

## Always set a TTL, know the eviction policy

- Give every cache and ephemeral key an expiry. A cache without a TTL is a memory leak with good intentions.

```
SET cache:product:88 "<payload>" EX 300
EXPIRE session:abc123 1800
```

- Do not leave `SET` without `EX`/`PX` on keys that should not live forever.
- Understand `maxmemory-policy`. When memory fills, it decides what happens: `noeviction` starts rejecting writes, `allkeys-lru`/`allkeys-lfu` evict across everything, `volatile-*` only evict keys that carry a TTL.
- A pure cache usually wants an `allkeys-*` policy. A store mixing cache and must-keep data wants `volatile-*` so the durable keys survive, which only works if you actually set TTLs on the disposable ones.

## Never KEYS in production, use SCAN

- `KEYS pattern` walks the entire keyspace in one blocking pass. On a large instance it freezes the server for everyone while it runs.
- Use `SCAN` with a cursor and a `COUNT` hint. It returns keys in small batches and lets other commands interleave.

```
# Do
SCAN 0 MATCH cache:product:* COUNT 100

# Instead of
KEYS cache:product:*
```

- The same warning applies to `SMEMBERS`, `HGETALL`, and `LRANGE 0 -1` on huge collections. Use the `SSCAN`/`HSCAN`/`ZSCAN` cursor variants.

## Pipeline and atomic multi-step operations

- Batch independent commands into a pipeline so one round trip carries many operations. Latency, not CPU, is usually the bottleneck; a pipeline collapses N round trips into one.
- A pipeline is not atomic. For "these steps must run together with nothing in between", use `MULTI`/`EXEC` or a Lua script.
- Prefer a Lua script when the logic reads a value and decides what to write from it. The script runs atomically on the server, so no other command interleaves, and you avoid a read/modify/write race across the network.

```
# Atomic check-and-set via Lua (single server-side execution)
EVAL "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end" 1 lock:job:7 token-xyz
```

## Respect the single thread

- One command runs at a time. A slow command blocks every other client until it finishes.
- Avoid commands whose cost grows with the data: a large `SUNIONSTORE`, a full-range `ZRANGE`/`LRANGE`, `SORT` on a big collection, an unbounded `SMEMBERS`.
- Prefer bounded, indexed access: `ZRANGE` a page at a time, `SCAN` variants for iteration, structures sized so no single call is expensive.
- If you need heavy set math or ranking over large data, question whether Redis is the right tool for that part of the workload.

## Cache misses and stampedes

- Redis is a cache or a derived store, not the source of truth. Code every read to handle a miss by falling back to the origin, not by failing.
- A stampede happens when a hot key expires and every request rebuilds it at once, hammering the origin. Guard against it:
  - Take a short lock (`SET lock:key token NX EX 10`) so one request rebuilds while the others wait or serve stale.
  - Add jitter to TTLs so many keys do not expire on the same tick.
  - Optionally refresh a hot key early, before it expires, so it never goes cold under load.
- Design the origin to survive a full cache flush. If losing the cache takes the database down, the cache became a dependency you cannot afford.

## Persistence: RDB vs AOF

- **RDB** snapshots the dataset periodically. Compact and fast to restore, but a crash loses everything since the last snapshot.
- **AOF** logs every write and replays it on restart. Far less data lost, at the cost of a larger file and some write overhead; its `fsync` policy trades durability against speed.
- Many production setups run both: AOF for recovery, RDB for fast restarts and backups. Even so, treat Redis as replayable from the source rather than the last word on any data you cannot afford to lose.

## Connection pooling

- Use a connection pool. One connection per request exhausts file descriptors and pays the handshake cost on every call.
- Size the pool to the workload and reuse connections across requests. Blocking commands (`BLPOP`, `XREAD BLOCK`) tie up a connection for their duration, so budget separate connections for them.
- In a cluster, use a cluster-aware client so it routes each key to the right node and follows redirections.

## Distributed locks: know the limits

- A `SET key token NX EX ttl` lock is fine for reducing duplicate work and coordinating best-effort tasks. It is not a guarantee of mutual exclusion.
- A single-instance lock can be lost on failover, and any TTL can expire mid-operation while the holder still believes it owns the lock. Under GC pauses or network delay two clients can hold "the same" lock at once.
- Always release with a token check (delete only if the value is still yours, via the Lua compare-and-delete above) so you never delete a lock a later client acquired.
- If correctness genuinely depends on the lock, do not lean on Redis alone. Use a fencing token the protected resource can validate, or a system built for consensus. Treat multi-instance lock algorithms as advanced and contested, not a default.

## Quick reference

| Do | Instead of |
|---|---|
| Match the structure to the access pattern | A JSON string for everything |
| Namespaced, greppable keys (`user:1042:session`) | Ad hoc, inconsistent key names |
| TTL on every cache/ephemeral key | `SET` with no expiry |
| Chosen `maxmemory-policy` | Default eviction, discovered under load |
| `SCAN` and the cursor variants | `KEYS` / full `HGETALL` in production |
| Pipeline to cut round trips | One request per command |
| `MULTI`/`EXEC` or Lua for atomic steps | Read/modify/write racing over the network |
| Bounded, paged access | Full-range `ZRANGE`, big `SUNIONSTORE` on one thread |
| Handle misses, lock/jitter against stampedes | Assume the key is always warm |
| Connection pool, cluster-aware client | A new connection per request |
| Token-checked release, fencing where it matters | A plain lock trusted for correctness |
