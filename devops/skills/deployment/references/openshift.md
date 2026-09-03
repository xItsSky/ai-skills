# OpenShift

OpenShift is Kubernetes plus an opinionated layer of additions. Everything in the Kubernetes reference still applies: resource requests and limits, probes, rolling updates, PodDisruptionBudgets, labels, ConfigMaps and Secrets, security contexts, anti-affinity, RBAC. This file covers only the deltas that OpenShift introduces. Read the Kubernetes reference first, then apply what follows on top.

## Routes vs Ingress

Prefer a `Route` for external HTTP and HTTPS on OpenShift. The Route is the native external-traffic object and integrates with the built-in HAProxy router.

TLS termination modes on a Route:

- **edge**: the router terminates TLS and forwards plaintext to the pod. Certificate lives on the Route.
- **passthrough**: the router forwards encrypted traffic untouched. The pod terminates TLS. Use this when the application must own its certificate.
- **reencrypt**: the router terminates TLS, then opens a new TLS connection to the pod. Encrypted end to end with a router-managed edge certificate.

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: my-app
spec:
  to:
    kind: Service
    name: my-app
  port:
    targetPort: 3000
  tls:
    termination: edge
```

Ingress is supported. OpenShift converts an `Ingress` resource into a `Route` behind the scenes. Use a Route directly when you need TLS-mode control or router-specific behavior. Use Ingress when you want portable manifests that also run on plain Kubernetes.

## Security Context Constraints (SCC)

SCC is the OpenShift mechanism that gates what a pod is allowed to do. It is the OpenShift equivalent of the pod security layer and sits alongside the standard `securityContext` fields.

- `restricted-v2` is the default SCC. It assigns a random non-root UID from the project's allocated range.
- Because the UID is assigned at admission, do not hardcode `runAsUser`. Let the SCC pick the UID and keep `runAsNonRoot: true`. A hardcoded UID that falls outside the allowed range is rejected.
- Your image must tolerate an arbitrary UID: group-writable paths, no assumption of UID 0, files owned by the root group (GID 0).
- Request a more permissive SCC only through a ServiceAccount bound by RBAC, never by relaxing the whole namespace.
- Never run as `anyuid` or `privileged` without an explicit, documented justification. These grant fixed UIDs and host access that defeat the default isolation.

Grant an SCC to a ServiceAccount rather than to a user or the whole project.

```bash
oc adm policy add-scc-to-user anyuid -z my-serviceaccount -n my-project
```

## DeploymentConfig vs Deployment

Prefer the standard Kubernetes `Deployment`. It is the current default and works identically to plain Kubernetes.

`DeploymentConfig` is an older OpenShift-specific object. You will still see it in existing clusters. It differs from a Deployment in a few ways:

- **Image-change trigger**: redeploys automatically when a referenced ImageStream tag updates.
- **Config-change trigger**: redeploys when its pod template changes.
- **Lifecycle hooks**: `pre` and `post` hooks that run in a separate pod around a rollout, useful for migrations.

Do not create new DeploymentConfigs. Migrate them to Deployments when you touch them. If you need image-change behavior with a Deployment, drive it from a CI pipeline or an operator instead of the DeploymentConfig trigger.

## Builds: BuildConfig, ImageStream, and S2I

OpenShift can build images inside the cluster.

- **BuildConfig**: defines how to build an image. Build strategies include Docker (from a Dockerfile), Source-to-Image, and custom.
- **Source-to-Image (S2I)**: takes application source plus a language builder image and produces a runnable image without a Dockerfile.
- **ImageStream**: an in-cluster abstraction over image tags. It tracks image references and gives you stable names inside the cluster.

ImageStream tags are what enable image-change triggers and stable in-cluster references. A DeploymentConfig or a BuildConfig can watch an ImageStream tag and react when it moves.

```bash
oc new-app https://github.com/org/repo.git --name=my-app   # S2I build from source
oc start-build my-app                                       # Trigger a build
```

## Projects

An OpenShift `Project` is a Kubernetes namespace wrapped with extra metadata and self-service creation. From the API's point of view a Project maps to a namespace, so namespace-scoped objects and RBAC behave the same.

- The default-namespace rule from the Kubernetes reference still holds: never run production workloads in `default`.
- Create a dedicated Project per environment and team.
- Project creation carries display name, description, and requester annotations that a bare namespace does not.

```bash
oc new-project my-app-production --display-name="My App (production)"
oc project my-app-production   # Switch the active project
```

## The oc CLI

`oc` is the OpenShift CLI. It is a superset of `kubectl`. Every `kubectl` command also works, so `kubectl apply -f` is valid on OpenShift. `oc` adds OpenShift-aware commands on top.

| Task | oc command |
|---|---|
| Apply manifests | `oc apply -f manifest.yaml` |
| List resources | `oc get pods` |
| Create an app from source or image | `oc new-app` |
| Expose a Service as a Route | `oc expose service/my-app` |
| Manage a rollout | `oc rollout status deployment/my-app` |
| Switch the active project | `oc project my-app-production` |

## Integrated Registry and Image Pull

OpenShift ships an integrated container registry that backs ImageStreams.

- The no-`:latest` rule from the Kubernetes reference still applies. Never deploy a mutable `:latest` tag in production.
- Prefer ImageStream tags or SHA digests for pulls. An ImageStream tag can be resolved to a pinned digest, which gives you a stable reference plus the option of image-change triggers.
- In-cluster references through the integrated registry avoid an external round trip and keep pulls inside the cluster network.

## Kubernetes vs OpenShift

| Concern | Kubernetes | OpenShift |
|---|---|---|
| External HTTP/HTTPS | Ingress | Route (Ingress converts to a Route) |
| Pod security gate | Pod Security admission / securityContext | Security Context Constraints (SCC) |
| Workload controller | Deployment | Deployment (preferred); DeploymentConfig (legacy) |
| CLI | `kubectl` | `oc` (superset; `kubectl` also works) |
| Tenancy boundary | Namespace | Project (namespace plus metadata and self-service) |
