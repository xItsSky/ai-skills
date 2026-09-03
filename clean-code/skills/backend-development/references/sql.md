# SQL

Engine-specific depth for relational databases, targeting PostgreSQL and MySQL 8+. The `database.md` sibling covers the cross-store rules (parametrized queries, N+1, keyset pagination, short transactions, forward-only migrations, connection pooling, keeping persistence out of the domain). This file does not repeat them. It goes into the parts that are actually relational: how indexes are used, how to read a plan, how isolation and locking behave, and how to change a schema without taking the table down. Differences between Postgres and MySQL are called out inline where they matter.

## Column types and constraints

The schema is your first and cheapest validation layer. Push invariants into it so bad data cannot exist, rather than trusting every code path to check.

- Make columns `NOT NULL` by default. Add `NULL` only when absence is a real business state, not a placeholder for "not filled in yet".
- Pick the narrowest type that holds the value. Use a real `timestamptz` (Postgres) or `DATETIME`/`TIMESTAMP` (MySQL) for instants, `numeric`/`DECIMAL` for money, never `float`. Store enums as a constrained type, not free text.
- Use `CHECK` constraints for domain rules the type cannot express, and name them: `CONSTRAINT orders_total_positive CHECK (total > 0)`. Remember a `CHECK` passes on `NULL`, so pair it with `NOT NULL` when null must be rejected.
- Define foreign keys. They enforce referential integrity that application code drifts away from. Choose the `ON DELETE` action on purpose: `RESTRICT` to block, `CASCADE` for true composition (`orders` to `order_items`), `SET NULL` for an optional link. Never leave it to the default without deciding.
- Prefer identity columns (`BIGINT GENERATED ALWAYS AS IDENTITY` in Postgres, `BIGINT AUTO_INCREMENT` in MySQL) or a UUID with a natural default. In Postgres, `SERIAL` is legacy; use identity.

```sql
CREATE TABLE orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
    status      TEXT        NOT NULL,
    total       NUMERIC(12,2) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT orders_status_valid CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled')),
    CONSTRAINT orders_total_positive CHECK (total > 0)
);
```

## Indexing strategy

`database.md` says to index filter/join/sort columns. The relational specifics are about column order and what actually makes an index usable.

- In a composite index, order the columns equality-first, then the range or sort column: `(tenant_id, created_at)` serves `WHERE tenant_id = $1 ORDER BY created_at`. A query can use a leading prefix of the index but not a trailing column alone, so `WHERE created_at = $1` gets nothing from that index.
- A covering index answers the query from the index alone, with no table lookup. In Postgres use `INCLUDE` for the non-key payload; in MySQL, add the columns to the index and rely on the clustered primary key already being present.

```sql
-- Index-only scan: email lookup returns full_name without touching the heap
CREATE INDEX idx_users_email ON users (email) INCLUDE (full_name);
```

- Use a partial index when queries only ever touch a subset: `CREATE INDEX idx_orders_pending ON orders (created_at) WHERE status = 'pending'`. It is smaller and cheaper to maintain. (Postgres only; MySQL has no partial index, use a generated column or a narrower table.)
- Know when an index will not be used: a leading wildcard `LIKE '%foo'`, a function or cast on the indexed column (`WHERE lower(email) = ...` needs an expression index on `lower(email)`), an `OR` across different columns, a type mismatch between the column and the bound parameter, or a predicate so unselective the planner prefers a scan.
- After bulk loads, refresh planner statistics (`ANALYZE` in Postgres) so the optimizer sees reality.

## Read the query plan

Never guess at performance. Ask the engine what it does.

- Postgres: `EXPLAIN` shows the estimated plan; `EXPLAIN (ANALYZE, BUFFERS)` runs the query and shows real row counts, timing, and buffer reads.
- MySQL: `EXPLAIN` shows the plan; `EXPLAIN ANALYZE` gives measured timings on 8.0+.
- Read for the access method first. A `Seq Scan` / `ALL` on a large table where you expected an index lookup means the index is missing, unusable, or ignored.
- Compare estimated rows to actual rows. A large gap points to stale statistics and a plan built on a bad guess.
- Watch for a nested loop over a large outer set (the plan shape behind an N+1), an unexpected sort that a matching index would remove, and spills to disk on hashes or sorts.

## Normalization, then deliberate denormalization

- Normalize to 3NF first. It removes update anomalies and the redundant copies that drift out of sync.
- Denormalize only against evidence: a computed aggregate read far more often than it changes, or a join whose cost stays high after indexing. When you do, own the consistency, keep the derived copy correct with a trigger or a well-defined write path, and write down why it exists.
- Never build an Entity-Attribute-Value table. It throws away types, constraints, and the planner. For semi-structured data use `JSONB` (Postgres) or a `JSON` column (MySQL), indexed with GIN where you query into it.

## Set-based thinking and joins

- Express work as one set-based statement, not a row-by-row loop in application code. `UPDATE ... FROM`, `INSERT ... SELECT`, and a single join beat fetching rows to mutate them one at a time.
- Choose the join type deliberately. `INNER` drops unmatched rows; `LEFT` keeps the left side with `NULL` on no match. A `LEFT JOIN` whose `WHERE` clause filters the right table on a non-null value silently becomes an inner join, a common bug.
- Beware the fan-out: joining one row to many multiplies the result set, so an aggregate over a multi-join can double-count. Aggregate in a subquery or CTE before joining, or count `DISTINCT`.

## CTEs and window functions

- Use a CTE (`WITH`) to name and stack the steps of an analytical query so it reads top to bottom instead of nesting inward. In Postgres 12+ and MySQL 8+ a plain CTE is inlined and optimized like a subquery; add `MATERIALIZED` in Postgres only when you want it computed once on purpose.
- Reach for window functions instead of self-joins or correlated subqueries for running totals, rankings, and per-group comparisons. They keep every row while computing across a frame.

```sql
SELECT
    user_id,
    created_at,
    total,
    SUM(total) OVER (PARTITION BY user_id ORDER BY created_at) AS running_total,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS recency_rank
FROM orders;
```

## Isolation levels and the anomalies they prevent

Pick the level for the invariant you need to protect. Postgres and MySQL/InnoDB both default to a level that still allows some anomalies.

| Level | Dirty read | Non-repeatable read | Phantom read | Lost update / write skew |
|---|---|---|---|---|
| READ COMMITTED | No | Possible | Possible | Possible |
| REPEATABLE READ | No | No | No in Postgres; InnoDB blocks most via gap locks | Possible (write skew) |
| SERIALIZABLE | No | No | No | No |

- Postgres defaults to READ COMMITTED; MySQL/InnoDB defaults to REPEATABLE READ. Do not assume the default matches across engines.
- READ COMMITTED is fine for single-row OLTP writes.
- REPEATABLE READ gives a stable snapshot for multi-statement reads and reports. It does not stop write skew, where two transactions each read then write on the other's blind spot.
- SERIALIZABLE is the safe choice for ledgers and any logic where a serialization anomaly corrupts data. Postgres enforces it optimistically and aborts a loser with a serialization failure, so wrap the transaction in retry logic (SQLSTATE `40001` in Postgres, deadlock/serialization errors in InnoDB).

## Locking and deadlock avoidance

- A deadlock happens when two transactions grab the same rows in opposite order. Prevent it by acquiring locks in a consistent order everywhere (for example, always lock by ascending `id`).
- Use `SELECT ... FOR UPDATE` to lock the rows you are about to change, and only those rows. Add `SKIP LOCKED` for queue-style consumers so workers step over rows another worker already holds, and `NOWAIT` when you would rather fail fast than wait.
- Keep the lock window tiny. Do the reads and the thinking first, open the transaction, write, commit. Never hold a lock across a network call.
- Set a `statement_timeout` (Postgres) or `max_execution_time` / `innodb_lock_wait_timeout` (MySQL) in production so a stuck statement dies instead of pinning locks and blocking vacuum.

## Avoid SELECT *

- Name the columns. `database.md` covers why for the wire and covering indexes; the relational cost is also that `SELECT *` fetches wide `TEXT`/`JSONB` blobs you did not want and breaks the moment a column is added or reordered under a positional client.

## Safe schema changes on large tables

The migration mechanics (versioned, forward-only, expand/contract) live in `database.md`. Here is what breaks on a big table and how to avoid it.

- Adding a column with a constant default is instant on Postgres 11+ and MySQL 8+ (metadata-only). Adding one with a volatile default rewrites the table; do it in steps instead.
- Build indexes without blocking writes: `CREATE INDEX CONCURRENTLY` in Postgres (it cannot run inside a transaction, and a failed build leaves an `INVALID` index to drop and retry), and rely on MySQL 8's online DDL (`ALGORITHM=INPLACE, LOCK=NONE`) or a tool like `gh-ost`/`pt-online-schema-change` for the changes that would otherwise lock.
- Add `NOT NULL` in stages: add the column nullable, backfill in batches, add a `CHECK (col IS NOT NULL)` validated separately, then set `NOT NULL`. This avoids a full-table lock and rewrite.
- Backfill in bounded batches (a few thousand rows per transaction), not one giant statement that holds locks and bloats the WAL/undo log.
- Adding or validating a foreign key can take a long lock. In Postgres, add it `NOT VALID` first, then `VALIDATE CONSTRAINT` in a separate step that takes only a share lock.

## Do / Instead of

| Do | Instead of |
|---|---|
| `NOT NULL` by default, `NULL` only when meaningful | Nullable everything and check in code |
| Named `CHECK` constraints for domain rules | Validating only in the application |
| Foreign keys with a deliberate `ON DELETE` | Orphan rows enforced by hope |
| Composite index ordered equality-then-range | Column order that ignores the query shape |
| Covering / `INCLUDE` index for hot reads | A heap lookup on every row |
| `EXPLAIN (ANALYZE, BUFFERS)` before tuning | Guessing which query is slow |
| Normalize, then denormalize with evidence | Preemptive denormalization or an EAV table |
| One set-based statement | A row-by-row loop in app code |
| CTEs and window functions for analytics | Nested subqueries and self-joins |
| SERIALIZABLE + retry for ledger logic | Trusting the default isolation level |
| Lock rows in a consistent order, `FOR UPDATE ... SKIP LOCKED` | Ad hoc lock order that deadlocks |
| `CREATE INDEX CONCURRENTLY` / online DDL | A blocking `ALTER` on a live large table |
| Batched backfill, staged `NOT NULL` | One statement that locks and rewrites |
