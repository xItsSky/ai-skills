# Elasticsearch

Conventions for Elasticsearch as a search and analytics store. The generic data-layer rules live in `database.md`; this file covers what is specific to an inverted-index engine. The first rule frames all the others: Elasticsearch is where you search and aggregate, not where you keep the truth. Keep the system of record in your primary database and index a projection of it into Elasticsearch. When the index is wrong, you rebuild it from the source.

## Define explicit mappings

- Set the mapping for an index before you write to it. Dynamic mapping infers types from the first document it sees, and one odd early document locks the field into the wrong type for the life of the index.
- Turn dynamic mapping off (`"dynamic": "strict"`) on indices where the shape is known. A rejected unexpected field is better than a silently misparsed one.
- Decide each field's type, its indexing, and whether it needs `doc_values` on purpose.

```json
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "id":         { "type": "keyword" },
      "title":      { "type": "text", "analyzer": "standard" },
      "status":     { "type": "keyword" },
      "created_at": { "type": "date" },
      "price":      { "type": "scaled_float", "scaling_factor": 100 }
    }
  }
}
```

## text vs keyword

This is the choice you make most, and getting it wrong quietly breaks either search or aggregation.

- Use `text` for full-text search. The value is analyzed into tokens, so `"Red Running Shoes"` matches a query for `running`. A `text` field cannot be aggregated or sorted efficiently and is not meant for exact matching.
- Use `keyword` for exact match, filtering, sorting, and aggregations. The value is stored whole and untouched, so it groups and sorts cleanly but does not match on individual words.
- When a field needs both, index it as `text` with a `keyword` sub-field.

```json
{
  "tag": {
    "type": "text",
    "fields": { "raw": { "type": "keyword" } }
  }
}
```

- Search on `tag`, aggregate and sort on `tag.raw`. Reaching for the wrong one is the usual cause of "why is my aggregation empty" and "why does my search miss".

## Query context vs filter context

- A query in **query context** answers "how well does this match" and computes a relevance `_score`. Use it for the parts the user actually searches on.
- A query in **filter context** answers "does this match, yes or no". It skips scoring and its results are cached, so repeated filters get much cheaper.
- Put exact constraints (status, date range, tenant, category) in `filter`. Keep only the real full-text relevance in `must`.

```json
{
  "query": {
    "bool": {
      "must":   [ { "match": { "title": "wireless headphones" } } ],
      "filter": [
        { "term":  { "status": "active" } },
        { "range": { "created_at": { "gte": "now-30d" } } }
      ]
    }
  }
}
```

- Scoring a term filter that only ever means yes or no wastes work and defeats the filter cache.

## Analyzers and normalizers

- An analyzer turns `text` into tokens: it splits, lowercases, and can stem or strip stop words. The same analyzer runs at index time and query time, so the two must agree or matches vanish.
- Choose the analyzer for the language and the search behavior you want. A language analyzer stems (`running` to `run`); the standard analyzer does not.
- A normalizer is the `keyword` equivalent: it applies simple, token-free changes such as lowercasing so `"Active"` and `"active"` compare equal, without breaking the value into words.
- Test an analyzer with the analyze API before you rely on it. Do not assume how a value tokenizes.

## Pagination: avoid deep from/size

- `from`/`size` is fine for the first few shallow pages. It does not scale: every shard has to build and sort `from + size` hits, so page 10,000 is enormous work and hits the `max_result_window` ceiling.
- For deep pagination and stable "next page" navigation, use `search_after` with a sort that ends in a unique tiebreaker (for example a sort on `created_at` then `_id`).
- Pair `search_after` with a point-in-time so the view stays consistent while you page across a changing index.
- For full exports, page with `search_after` over a point-in-time. Scroll still exists for the same job but is the older approach; prefer PIT for new code.

## Bulk indexing and the refresh tradeoff

- Index in batches through the bulk API, not one document per request. One request that carries many actions cuts round trips by orders of magnitude.
- Size batches by payload, not a fixed count. A few megabytes per bulk request is a reasonable starting point; measure and adjust.
- A new document is not searchable until a refresh. The default refreshes about once a second, which costs work on write-heavy indices.
- For a large load, raise or disable `refresh_interval` during the load and restore it after. Do not force `refresh=true` on every write to "see it immediately"; that throttles throughput badly.

## Shards and replicas

- A primary shard is a unit of data; a replica is a copy for redundancy and read capacity. Search cost scales with the number of shards it must touch.
- Oversharding is the common mistake: many tiny shards add per-shard overhead to every query and bloat cluster state. Aim for shards in the tens-of-gigabytes range rather than many small ones.
- Set primary shard count at index creation; you cannot change it later without a reindex. Replica count you can change live.
- Size shards for the data you expect, not the data you have on day one. For time-based data, roll over to a new index rather than growing one index without bound.

## Aggregations and their cost

- Aggregations run in memory on `doc_values`, so a high-cardinality `terms` aggregation over millions of buckets can consume serious heap.
- Aggregate on `keyword`, `date`, and numeric fields. Do not aggregate on analyzed `text`.
- Bound what you request: set a sensible `size` on `terms`, and prefer a `composite` aggregation to page through a large set of buckets instead of pulling them all at once.
- Nested and deeply pipelined aggregations multiply the cost. Profile a heavy one before shipping it.

## Aliases and zero-downtime reindexing

- Point your application at an alias, never at a concrete index name. The alias is the stable name; the index behind it can change.
- A mapping change on an existing field usually cannot be applied in place. Create a new index with the corrected mapping, reindex into it, then atomically swing the alias over. Readers never see a gap.
- Use index lifecycle management to roll indices over by age or size and to move older data through hot, warm, and cold tiers automatically. This keeps active shards small and retires old data on a schedule.

## Mapping changes require a reindex

- You can add a new field to a mapping. You generally cannot change an existing field's type or analyzer in place.
- To change a field, build a new index and reindex into it. Plan for this: an alias plus the reindex API makes it a routine, downtime-free operation instead of an outage.

## Quick reference

| Do | Instead of |
|---|---|
| Explicit mapping, `dynamic: strict` | Rely on dynamic mapping from the first document |
| `text` for search, `keyword` for exact/agg/sort | One field type for both jobs |
| Exact constraints in `filter` context | Scoring every clause in `must` |
| `search_after` with a PIT for deep pages | Deep `from`/`size` pagination |
| Bulk API in sized batches | One index request per document |
| Tune `refresh_interval` for big loads | Force `refresh=true` on every write |
| Shards sized in tens of GB | Many tiny shards (oversharding) |
| Alias in front of the index, reindex to change mapping | Application pointed at a concrete index name |
| Bounded aggregations on `keyword`/numeric fields | Unbounded `terms` on analyzed `text` |
| Elasticsearch as a search projection | Elasticsearch as the system of record |
