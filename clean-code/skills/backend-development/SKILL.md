---
name: backend-development
description: Use when writing, reviewing, or refactoring backend or server code (HTTP APIs, controllers, services, data access, background jobs, authentication, or authorization) in NestJS, Node.js, Java, Spring Boot, or Python. Also use for backend testing, database access, and API design.
---

# Backend Development

Detect once, read once, then write. Reading references one at a time is the
slowest thing this skill can do: each extra turn costs more than the file.

## Step 1: Detect everything in one command

```bash
find . -maxdepth 3 -name package.json -not -path '*/node_modules/*' -print -exec \
  grep -oE '"(@nestjs/core|express|fastify|koa|typeorm|prisma|pg|mysql2|mongoose|@elastic/elasticsearch|redis|ioredis|typescript)": *"[^"]*"' {} \;
find . -maxdepth 2 \( -name pom.xml -o -name build.gradle -o -name pyproject.toml \
  -o -name requirements.txt -o -name nx.json -o -name Dockerfile \) -print
```

Never open a lockfile whole; they run to megabytes. For a resolved version, grep
the one package: `grep -m1 -A2 '"node_modules/@nestjs/core"' package-lock.json`.
Apply only the rules matching that version; for support status and upgrades see
core `references/versioning-and-migration.md`.

## Step 2: Read every match in one batch

Read all applicable rows **in a single message**. A one-file fix needs the stack
row alone; a feature crossing layers needs all of them.

| Signal | Stack | Read |
|---|---|---|
| `@nestjs/core` | NestJS | `references/nestjs.md` |
| `spring-boot-starter*` in `pom.xml`/`build.gradle` | Spring Boot | `references/spring-boot.md` |
| `pom.xml`/`build.gradle`, no Spring Boot | Java | `references/java.md` |
| `express`/`fastify`/`koa`, no NestJS | Node.js | `references/nodejs.md` |
| `requirements.txt`, `pyproject.toml`, or `.py` files | Python | `references/python.md` |

| When you are | Also read |
|---|---|
| Designing or changing an endpoint | `references/api-design.md` |
| Reading or writing persisted data (any store) | `references/database.md` |
| Using PostgreSQL, MySQL, or another SQL database | `references/database.md` + `references/sql.md` |
| Using MongoDB | `references/database.md` + `references/mongodb.md` |
| Using Elasticsearch | `references/database.md` + `references/elasticsearch.md` |
| Using Redis | `references/database.md` + `references/redis.md` |
| Handling identity or access control | `references/auth-security.md` |
| Writing or updating tests | `references/integration-testing.md` + core `references/baseline.md` |

Store signals: `pg`, `mysql2`, `typeorm`, `prisma` mean SQL; `mongoose` MongoDB;
`@elastic/elasticsearch` Elasticsearch; `redis` or `ioredis` Redis.

Fold the shared baseline into the same batch: `core-development` for TypeScript,
testing, git, and security; core `references/nx.md` when `nx.json` appeared;
core `references/docker.md` when a `Dockerfile` did; core
`references/architecture.md` for layering and error handling.

## Non-negotiables

- Validate every input at the trust boundary. Never trust the client.
- Enforce authentication and authorization on the server, on every protected path.
- HTTP concerns in controllers, business rules in services, data access in repositories.
- Tests assert behavior and contracts, never internal wiring.
- Vet a dependency before installing it. On a known vulnerability, stop and get approval. See core `references/baseline.md`.
- Apply the rules matching the detected version. Flag end-of-life versions and propose upgrades, but never change a version without approval.
