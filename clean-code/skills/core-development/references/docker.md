# Docker

An image is a build artifact, and it should be small, reproducible, and boring. Every layer you add is attack surface, cache you can invalidate, or bytes you ship. The rules below cover authoring Dockerfiles and images, not orchestration.

## Base images

- Use official or verified-publisher images. Do not build on a random base from a stranger.
- Prefer a minimal variant: `-slim` or `-alpine` over the full distribution image. Less in the base means less to patch.
- Pin a specific tag. Never `latest`: it floats, and a rebuild silently pulls a different image.
- For supply-chain integrity, pin the tag plus a digest so the exact bytes are locked:

```dockerfile
FROM node:20.9.0-alpine@sha256:<hash>
```

## Multi-stage builds

Use a multi-stage build whenever there is a build step. The final image must not carry compilers, dev dependencies, or build tooling. Build in one stage, copy only the artifact into a clean runtime stage.

```dockerfile
# build stage
FROM node:20.9.0-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# runtime stage
FROM node:20.9.0-alpine AS runtime
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/dist ./dist
USER node
CMD ["node", "dist/main.js"]
```

## Layer ordering and cache

- Order instructions from least to most frequently changing. Copy the dependency manifest and install before copying source, so a code change does not bust the dependency layer.
- Combine related commands into one `RUN` and clean up in the same layer. A file removed in a later layer still ships in the earlier one.
- Prepend `set -o pipefail &&` to any `RUN` that uses a pipe, so a failure mid-pipe fails the build.

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

## One concern per image

- Give each image a single job: one service, one entrypoint. Do not pack an app, a database, and a cron daemon into one container.
- Split responsibilities into separate images and let the runtime compose them.

## Non-root user

- Run as a non-root user in production. A compromised process should not be root inside the container.
- Use explicit numeric UID and GID; names may not resolve the same way across bases.
- Never install `sudo`.

```dockerfile
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser
USER appuser
```

## .dockerignore

Keep a `.dockerignore` next to the Dockerfile. Without it, `COPY . .` ships `.git`, `.env`, local dependency folders, and build junk into the image and the build context.

```
.git
.env
.env.*
node_modules
*.log
coverage
dist
```

## Secrets

- Never bake a secret into an image with `ARG`, `ENV`, `RUN`, or `COPY`. It persists in layer history and is extractable with `docker history --no-trunc`.
- For a build-time secret (a private registry token, an SSH key), use a BuildKit secret mount. It is available during the `RUN` and never written to a layer.
- Inject runtime secrets from the environment or orchestrator at deploy time.

```dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci --omit=dev
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

## Image size and attack surface

- Install only what you run. Use `--no-install-recommends` (apt) or `--no-cache` (apk), and drop package caches in the same layer.
- Do not install a full toolchain into the runtime stage; that is the build stage's job.
- Fewer packages means fewer CVEs to track and a smaller image to pull.

## ARG vs ENV

- `ARG` is build-time only: version numbers, build flags. It is gone at runtime.
- `ENV` persists into the running container: config the app reads at startup.
- Prefer `COPY`; it is explicit. Use `ADD` only to unpack a local tar archive, never for remote URLs.

## ENTRYPOINT vs CMD

- Use exec form (JSON array) for both. Shell form makes `/bin/sh` PID 1, so `SIGTERM` is never forwarded to your process.
- `ENTRYPOINT` sets the fixed executable; `CMD` supplies default, overridable arguments.
- Ensure signals reach your process and zombies get reaped. Use a lightweight init (`tini`, `dumb-init`) as PID 1 when the runtime does not do it for you.

```dockerfile
# shell form: /bin/sh is PID 1, SIGTERM is dropped
CMD node dist/main.js

# exec form: your process is PID 1
ENTRYPOINT ["node"]
CMD ["dist/main.js"]
```

## Healthchecks

- Add a `HEALTHCHECK` so the runtime knows whether the container is actually serving, not just running.
- Keep the check cheap. Hit a lightweight liveness endpoint; no database calls.
- Set `--start-period` to cover slow startup so early probes do not mark a booting container unhealthy.

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Reproducible builds

- Pin base images by digest and dependencies by lockfile so the same source produces the same image.
- Label images with OCI metadata so an image traces back to its source and version.

```dockerfile
LABEL org.opencontainers.image.source="https://github.com/org/repo"
LABEL org.opencontainers.image.version="1.2.3"
```

## Do / Instead of

| Do | Instead of |
|---|---|
| Pin tag + digest | `FROM image:latest` |
| Multi-stage, copy the artifact | ship compilers in the runtime image |
| Manifest before source | `COPY . .` before installing deps |
| `USER appuser` | run as root |
| BuildKit secret mount | secret in `ARG` / `ENV` / `RUN` |
| `.dockerignore` | send `.git` and `.env` into the context |
| Exec-form `ENTRYPOINT`/`CMD` | shell form that drops `SIGTERM` |
| `HEALTHCHECK` with `--start-period` | no health signal |
| `--no-install-recommends`, clean cache | leave package caches in the layer |
| One service per image | app + db + cron in one container |
