# Database

Data-layer conventions for relational and document stores. The persistence engine changes; most of these rules don't.

## Model for access patterns

- Design the schema around how the data is read and written, not around an abstract entity diagram.
- In SQL, normalize first, then denormalize deliberately where a hot read path demands it. Know why each denormalization exists.
- In NoSQL, model for the query up front. Document stores reward shaping data to match reads; joins are expensive or absent, so embed what's read together and reference what isn't.
- List the top queries before you settle the schema. If a query needs a full scan to answer, the model is wrong.

## Indexing

- Index the columns that filter, join, and sort in real queries. An unindexed `WHERE` on a large table is a scan.
- Match composite index column order to the query's predicate order. A `(tenant_id, created_at)` index serves a filter on `tenant_id` sorted by `created_at`; the reverse order doesn't.
- Don't over-index. Every index costs write throughput and storage, and a rarely-used index earns nothing. Drop indexes no query uses.
- Verify with the query planner (`EXPLAIN`), not by guessing.

## Parametrized queries only

- Always bind input as parameters. Never concatenate or interpolate user input into a query string.

```sql
-- Do
SELECT id, email FROM users WHERE tenant_id = $1 AND status = $2;

-- Instead of
"SELECT id, email FROM users WHERE tenant_id = " + tenantId
```

- This holds for NoSQL too: pass values through the driver's parameter API, never build query objects from raw string input.

## Select what you need

- List the columns you use. Avoid `SELECT *`.
- Explicit columns keep the wire payload small, let covering indexes work, and stop a new column from silently changing every result.

## Prevent N+1

- Fetching a list and then querying each row's relation one at a time is the N+1 trap. It turns one request into hundreds.
- Load related data in one query with a join, or batch the follow-up (eager loading, `IN (...)`, a dataloader).
- Watch the query log in tests. A list endpoint that fires a query per item is a defect, not a performance nuance.

## Transactions

- Wrap writes that must succeed or fail together in one transaction. Partial writes that break an invariant are worse than a rejected request.
- Keep transactions short. Do no network calls, no external I/O, and no user-wait work while a transaction holds locks.
- Read outside the transaction, decide, then open the transaction for the write when you can.
- Pick the isolation level on purpose. Know whether you need to guard against lost updates or phantom reads.

## Migrations

- Every schema change is a versioned migration in source control. No manual edits to a live schema.
- Migrations are forward-only. To undo, write a new migration; don't rewrite history.
- Make them backward-compatible with the running code so deploys don't require downtime: add a nullable column, backfill, then switch reads, then drop the old column in a later release.

## Connection pooling

- Use a connection pool. Opening a connection per request exhausts the database.
- Size the pool to the database's limit, not to the app's concurrency wish. Too many connections starve the server.
- Set acquire and idle timeouts so a leaked connection surfaces instead of hanging the app.

## Persistence separate from domain

- Keep ORM entities or document schemas out of the API contract and out of business signatures where practical. Map at the boundary.
- The domain shouldn't break because a column was renamed for storage reasons.

## Pagination with stable ordering

- Order by a unique, stable key (or a tuple ending in one). Ordering by a non-unique column returns rows in an arbitrary, shifting sequence across pages.
- Prefer keyset pagination (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 50`) over large `OFFSET`. Deep offsets scan and discard every skipped row.

## Deletes

- Prefer a soft delete (`deleted_at` timestamp or `status`) when the row has audit, legal, or referential value. Filter it out on read.
- Hard delete when there's no reason to keep the data and retention rules require its removal.
- Whichever you pick, apply it consistently. A mix of both in one table breaks every count and join.

## Consistency in NoSQL

- Be explicit about the consistency you get. Many stores default to eventual consistency; a read right after a write may not see it.
- Choose strong consistency for the reads that can't tolerate staleness (a balance check), and accept eventual consistency where a short lag is fine (a view counter).
- Don't assume cross-document atomicity unless the store guarantees it. Design so a single document holds what must change together.

## Quick reference

| Do | Instead of |
|---|---|
| Parametrized queries | String-concatenated input |
| `SELECT id, email` | `SELECT *` |
| Join or batch related loads | One query per row (N+1) |
| Index columns used in filters/joins/sorts | Indexing everything, or nothing |
| Short transactions around invariants | Long transactions holding locks over I/O |
| Versioned, forward-only migrations | Manual edits to a live schema |
| Keyset pagination on large sets | Deep `OFFSET` scans |
| Order by a unique, stable key | Order by a non-unique column |
| Connection pool sized to the DB | A new connection per request |
| Explicit consistency choice in NoSQL | Assuming reads see the last write |
