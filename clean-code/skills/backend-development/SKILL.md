---
name: backend-development
description: Use when writing, reviewing, or refactoring backend or server code (HTTP APIs, controllers, services, data access, background jobs, authentication, or authorization) in NestJS, Node.js, Java, or Spring Boot. Also use for backend testing, database access, and API design.
---

# Backend Development

Load only the guidance that matches the project. Detect the framework and language first, read the one reference that fits, then pull in cross-cutting references as the task needs them. Do not read files for stacks the project does not use.

## Step 1: Detect the stack

Before writing code, inspect the project:

1. Read `package.json` (Node ecosystem) or `pom.xml` / `build.gradle` (JVM).
2. Match the strongest signal in the table. Read that one file.
3. Read the resolved version from the lockfile or the resolved dependency tree, not the declared range. Apply only the rules that match that version. For support status and upgrade proposals, see the `core-development` skill's `references/versioning-and-migration.md`.

| Signal in the project | Stack | Read |
|---|---|---|
| `@nestjs/core` | NestJS | `references/nestjs.md` |
| `spring-boot-starter*` in `pom.xml`/`build.gradle` | Spring Boot | `references/spring-boot.md` |
| `pom.xml`/`build.gradle`, no Spring Boot | Java | `references/java.md` |
| `express`/`fastify`/`koa`, no NestJS | Node.js | `references/nodejs.md` |

## Step 2: Add cross-cutting references as the task requires

| When you are | Also read |
|---|---|
| Designing or changing an endpoint | `references/api-design.md` |
| Reading or writing persisted data (any store) | `references/database.md` |
| Using PostgreSQL, MySQL, or another SQL database | `references/database.md` + `references/sql.md` |
| Using MongoDB | `references/database.md` + `references/mongodb.md` |
| Using Elasticsearch | `references/database.md` + `references/elasticsearch.md` |
| Using Redis | `references/database.md` + `references/redis.md` |
| Handling identity or access control | `references/auth-security.md` |
| Writing or updating tests | `references/integration-testing.md` + core `references/testing-philosophy.md` |

Detect the data store from dependencies: `pg`, `mysql`, `typeorm`, or `prisma` for SQL; `mongoose` or `mongodb` for MongoDB; `@elastic/elasticsearch` for Elasticsearch; `redis` or `ioredis` for Redis. Read `database.md` for the general rules, plus the engine reference that matches.

## Step 3: Apply the shared baseline

For TypeScript rules, the testing contract, git workflow, and security, follow the `core-development` skill. In an NX monorepo (`nx.json` present), also read core `references/nx.md`. For layering and error-handling design, see core `references/architecture.md`.

## Non-negotiables

- Validate every input at the trust boundary. Never trust the client.
- Enforce authentication and authorization on the server, on every protected path.
- Keep HTTP concerns in controllers, business rules in services, data access in repositories.
- Tests assert behavior and contracts, never internal wiring.
- Before installing a dependency, vet it for known vulnerabilities. If any are found, report them and wait for approval. See core `references/security-baseline.md`.
- Detect the framework and language version and apply the rules that match it. Flag end-of-life versions and propose upgrades, but never change a version without approval.
