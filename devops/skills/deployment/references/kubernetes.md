# Kubernetes

Defaults for running workloads on Kubernetes in production. Set them while you write the manifests. Retrofitting resource limits, probes, and security contexts onto a live cluster is far more work than getting them right the first time.

## Resource Requests and Limits

Set memory requests AND limits on every container. Set CPU requests. Consider leaving CPU limits off. CPU is compressible, so a hard limit causes throttling even when the node has spare capacity.

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"   # Equal to request means Guaranteed QoS (last to be evicted)
    # No CPU limit intentionally
```

QoS eviction order, first to last: `BestEffort` (no requests), then `Burstable` (requests below limits), then `Guaranteed` (requests equal limits).

- Use a namespace `LimitRange` to enforce defaults for containers that omit explicit values.
- Use a `ResourceQuota` per namespace to cap total CPU, memory, and object counts.

## Probes

Three probes do three different jobs. Do not conflate them.

- **Readiness probe** controls traffic routing. A failure removes the pod from Service endpoints. It does not restart the container.
- **Liveness probe** controls restart. A failure kills and restarts the container.
- **Startup probe** gates liveness and readiness during a slow start. Use it when startup takes more than about 30 seconds.

```yaml
readinessProbe:
  httpGet:
    path: /readyz
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /livez
    port: 3000
  initialDelaySeconds: 30
  periodSeconds: 20
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /livez
    port: 3000
  failureThreshold: 30    # 30 * 10s = 300s maximum startup window
  periodSeconds: 10
```

Rules:

- Never include external dependencies (database, third-party APIs) in readiness or liveness checks.
- `/readyz` checks internal state only. An external outage should not make your pod unready.
- `/livez` returns success as long as the process is alive and not deadlocked.
- `failureThreshold` must be at least 3 to tolerate transient failures.
- Use HTTP probes for HTTP services. A TCP probe only confirms a port is open.

## Rolling Update Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0   # Zero-downtime: no pod is removed before a new one is ready
```

Both values cannot be `0` at the same time. When a brief unavailability is acceptable and you want a faster rollout, use `maxUnavailable: 1, maxSurge: 0`.

## Pod Disruption Budgets

Set a PDB for every production Deployment with 2 or more replicas.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
spec:
  minAvailable: 2
  unhealthyPodEvictionPolicy: AlwaysAllow   # Prevents drain hanging on unhealthy pods
  selector:
    matchLabels:
      app: my-app
```

A PDB protects against voluntary disruptions only: node drain, cluster upgrade. Use pod anti-affinity for protection against involuntary failures.

## Namespace Organization

- Never use the `default` namespace for production workloads.
- Organize by environment (`staging`, `production`) and by team.
- Attach a `LimitRange` and a `ResourceQuota` to every namespace.
- Namespaces are logical boundaries only. Use NetworkPolicies for network isolation.

## Recommended Labels

Apply these to every resource (Deployment, Service, and the rest) and to the pod template spec.

```yaml
labels:
  app.kubernetes.io/name: my-app
  app.kubernetes.io/instance: my-app-production
  app.kubernetes.io/version: "1.2.3"
  app.kubernetes.io/component: api
  app.kubernetes.io/part-of: vesta
  app.kubernetes.io/managed-by: argocd
  owner: team-backend
  environment: production
```

Use annotations for non-identifying metadata: runbook URLs, Slack channels, descriptions. Annotations cannot be used in selectors.

## ConfigMaps vs Secrets

- Never store sensitive data in a ConfigMap. ConfigMaps are unencrypted in etcd.
- Mount Secrets as volumes, not as environment variables. Env vars show up in `kubectl describe pod` and in crash logs.
- Enable etcd encryption at rest for Secrets.
- For production-grade rotation and auditing, use the External Secrets Operator backed by HashiCorp Vault or AWS Secrets Manager.
- Use a separate Secret per application. Never share one Secret across an entire namespace.

## Security Context

Hardened baseline for every container.

```yaml
spec:
  securityContext:               # Pod-level
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: app
    securityContext:             # Container-level
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: RuntimeDefault
```

- `readOnlyRootFilesystem: true`. Mount `emptyDir` volumes for paths that need write access, such as `/tmp`.
- `capabilities.drop: ["ALL"]`. Add back only what the app specifically requires.
- `seccompProfile.type: RuntimeDefault` blocks around 40 dangerous syscalls.
- Never set `privileged: true` unless the workload genuinely needs hardware access.

## Image Pull Policy

- Never use `:latest` in production. It makes rollback unreliable and version tracking impossible.
- Use specific semver tags (`v1.42.0`) or SHA digests (`image@sha256:abc...`).
- With a specific tag, `IfNotPresent` (the default) is correct. There is no need to set it explicitly.

## High Availability: Pod Anti-Affinity

Guarantee that no two replicas land on the same node.

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: my-app
      topologyKey: kubernetes.io/hostname
```

For zone-level HA, use `topology.kubernetes.io/zone` as the `topologyKey`.

Use `topologySpreadConstraints` for balanced distribution with some skew tolerance.

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: my-app
```

## Service Types

| Type | Use |
|---|---|
| `ClusterIP` (default) | All internal service-to-service communication |
| `LoadBalancer` | External access for TCP services that cannot go through Ingress |
| `NodePort` | Dev and testing only, never production |

For HTTP and HTTPS external traffic, use an Ingress rather than `LoadBalancer`. One cloud load balancer per service gets expensive at scale.

## Ingress

- Always set `ingressClassName` explicitly.
- Terminate TLS at the Ingress level. Provision certificates with cert-manager.
- Never expose cluster-internal services (databases, caches) through an Ingress.

## RBAC

- Start with zero permissions and add only what is required. Never grant `*` verbs or `*` resources.
- Prefer `Role` (namespace-scoped) over `ClusterRole` unless cross-namespace access is genuinely needed.
- Create a dedicated ServiceAccount per workload. Never share the `default` ServiceAccount.
- Set `automountServiceAccountToken: false` on the default SA.
- Never bind `cluster-admin` to an application ServiceAccount.

```yaml
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]   # Not "*"
```

## Do / Instead of

| Do | Instead of |
|---|---|
| Set memory requests and limits, and CPU requests | leave containers unbounded |
| Leave CPU limits off | throttle on spare capacity with hard CPU limits |
| Keep external dependencies out of probes | fail liveness when a database blips |
| Use `maxUnavailable: 0` for zero-downtime rollouts | drop pods before replacements are ready |
| Add a PDB for every multi-replica Deployment | let a node drain take all replicas at once |
| Deploy to a dedicated namespace | run production in `default` |
| Mount Secrets as volumes | expose them as environment variables |
| Enable etcd encryption at rest | keep Secrets in plaintext in etcd |
| Run as non-root with dropped capabilities | run `privileged` without justification |
| Pin a semver tag or digest | deploy `:latest` |
| Spread replicas with anti-affinity | let two replicas share one node |
| Route external HTTP through Ingress with TLS | expose one `LoadBalancer` per service |
| Grant least-privilege RBAC per workload | bind `cluster-admin` to app ServiceAccounts |
