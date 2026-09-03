# MongoDB

Document-store depth for MongoDB 7 and 8. The `database.md` sibling covers what is common to every store: parametrized access, N+1, keyset pagination, short transactions, forward-only migrations, connection pooling, and keeping persistence out of the domain. This file does not repeat them. It covers the decisions that are specific to a document model: how to shape documents for the access pattern, when to embed and when to reference, how compound and multikey indexes are ordered, how the aggregation pipeline replaces application joins, and how read/write concern and transactions actually behave.

## Model for the access pattern

- Design the document around the query that reads it, not around a normalized entity diagram. In a document store, the win comes from a single read returning everything a screen needs.
- Write down the top reads and writes before settling the shape. If answering a common query needs several round trips or an in-app join, the model is wrong.
- Data read together should live together. Data written on different schedules, or shared across parents, should be separate.

## Embed vs reference

The central tradeoff. Embedding buys single-read locality; referencing buys independent lifecycle and bounded document size.

Embed when:

- The relationship is one-to-one or one-to-few with a bounded count.
- The child is always read with the parent (a user and their address).
- The child is not shared across parents and is not queried on its own.

Reference when:

- The relationship is one-to-many with an unbounded or large child count.
- The child is updated on its own schedule, so embedding would rewrite the whole parent on every change.
- The child is shared across parents (many-to-many).
- Only a slice of the children is needed per query, so embedding would drag the rest along.
- The document would otherwise approach the 16 MB BSON limit.

## Avoid unbounded array growth

- Never embed an array that grows without a ceiling. Comments on a post, events on a device, and log lines all trend toward the 16 MB document limit and wreck multikey index performance long before that.
- Move an unbounded relationship to its own collection with a reference field. Where you genuinely need append locality (time-series buckets), cap the array and roll over to a new bucket document with the outlier or bucket pattern.

## Index design and the ESR rule

`database.md` covers indexing filter/sort fields in general. Here is what is specific to documents.

- Every production query needs an index. A `COLLSCAN` in `explain("executionStats")` on a real collection is a defect, not a tuning note.
- Order compound index fields by ESR: Equality fields first, then the Sort field, then Range fields. A query filtering on `status`, sorting by `createdAt`, and ranging on `price` wants the index `{ status: 1, createdAt: 1, price: 1 }`.

```js
db.orders.createIndex({ status: 1, createdAt: -1, total: 1 });
// serves: find({ status: "paid", total: { $gte: 100 } }).sort({ createdAt: -1 })
```

- Prefer one compound index over several single-field indexes when queries filter on the same fields together. A query can use a leading prefix of a compound index, so `{ a: 1, b: 1 }` also serves a filter on `a` alone.
- Indexing an array field makes it a multikey index. It holds one entry per array element, so it grows with array length and cannot cover a query. Watch the array size before indexing into it.
- Use a partial index (`partialFilterExpression`) when queries only touch a subset, and a sparse index for a field most documents lack. Both keep the index small.
- Drop indexes no query uses. Check `$indexStats` or the Atlas Performance Advisor. Every index taxes every write.

## Aggregation over application-side joins

- Do multi-stage work in the aggregation pipeline, close to the data, rather than pulling documents into the app to join and reduce them.
- Put `$match` and `$project` first so the pipeline sheds documents and fields before any expensive stage, and so `$match` can use an index.
- `$lookup` is a join and behaves like one. It is fine for occasional reporting; in a hot read path, model the data so the read does not need it (embed or a deliberate reference denormalization).
- The per-stage memory limit is 100 MB. Reaching for `allowDiskUse: true` is a signal to add a `$match` or an index, not the default setting.
- Never use `$where`. It runs arbitrary JavaScript, cannot use an index, and is a security hole.

## Schema validation

- The flexible schema is a liberty, not a licence to skip validation. Attach a JSON Schema validator to every collection so required fields, types, and enums are enforced by the database.
- Set `validationLevel: "strict"` and `validationAction: "error"` for new collections. For a collection you are retrofitting, start with `"warn"`, fix the violators, then tighten to `"error"`.

```js
db.createCollection("orders", {
  validator: { $jsonSchema: {
    bsonType: "object",
    required: ["userId", "status", "total", "createdAt"],
    properties: {
      status: { enum: ["pending", "paid", "shipped", "cancelled"] },
      total:  { bsonType: "decimal", minimum: 0 }
    }
  }},
  validationLevel: "strict",
  validationAction: "error"
});
```

## Write concern

- Keep the modern default `{ w: "majority" }`. It acknowledges a write only once a majority of replicas hold it, so a failover cannot roll it away. Do not lower it without a written reason.
- For writes that must survive a crash, add journaling and a timeout: `{ w: "majority", j: true, wtimeout: 5000 }`. Always set `wtimeout` with `w: "majority"`, or a write can block indefinitely when the majority is unreachable.
- `w: 1` acknowledges from the primary only and can be lost on failover; use it only for high-throughput, non-critical writes. `w: 0` is fire-and-forget, acceptable only for truly disposable data like telemetry.

## Read concern and read preference

- Read concern controls what a read is allowed to see. `"majority"` returns only data that cannot be rolled back. `"local"` may return not-yet-durable writes. For read-your-own-write inside a session, pair `"majority"` with causal consistency.
- Read preference controls where the read goes. `primary` (default) is the only correct choice for read-after-write and transactions. `secondaryPreferred` and `nearest` scale reads and cut latency but can return stale data from async replication; bound the lag with `maxStalenessSeconds`.
- Be explicit about which you want. Serving a balance check from a lagging secondary is a correctness bug, not an optimization.

## Transactions: when to use them and when not to

- The document model is designed so that a single-document write is already atomic. Reach for a multi-document transaction only when an invariant genuinely spans documents or collections and cannot be expressed in one document.
- First try to remove the need. If two documents must always change together, that is often a sign they should be one document.
- Multi-document transactions cost more: they hold locks, run against the primary, and have a runtime cap (60 seconds by default). Keep them short and small.
- Retry on `TransientTransactionError` and `UnknownTransactionCommitResult`. These are expected under contention, and the driver's transaction callback API retries them for you.

## Avoid large skip-based pagination

- `database.md` covers keyset pagination generally. In MongoDB specifically, `skip(n)` still walks and discards the first `n` documents, so deep pages get linearly slower.
- Page by a range on a unique, indexed sort key instead: `find({ _id: { $gt: lastId } }).sort({ _id: 1 }).limit(50)`. For a compound sort, carry the full tuple of the last document as the cursor.

## TTL indexes for expiry

- Use a TTL index to expire ephemeral documents automatically: sessions, verification tokens, short-lived logs. A background task deletes documents once the indexed date passes.

```js
db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 });
```

- The field must be a BSON date (or an array of dates, where the earliest governs). The reaper runs about once a minute, so expiry is approximate, not instant. Do not use TTL where a hard deadline is a security requirement without an application-side check as well.

## Do / Instead of

| Do | Instead of |
|---|---|
| Shape the document for the query | Normalize as if it were relational |
| Embed one-to-few read together | Embed an unbounded, independently-written child |
| Reference or bucket unbounded relations | Arrays that grow forever toward 16 MB |
| Order compound indexes by ESR | Arbitrary field order in the index |
| Understand multikey cost before indexing arrays | Blindly indexing a large array field |
| Aggregation pipeline near the data | Pulling documents to join in the app |
| `$lookup` only off the hot path | A join on every read |
| JSON Schema validator on every collection | Trusting every writer to send clean data |
| `{ w: "majority" }`, `wtimeout` set | Lowering write concern with no reason |
| Explicit read concern and preference | Assuming a secondary read is fresh |
| Single-document atomicity first | A multi-document transaction by default |
| Range-cursor pagination on an indexed key | Deep `skip(n)` scans |
| TTL index for ephemeral data | A cron job hand-deleting expired rows |
