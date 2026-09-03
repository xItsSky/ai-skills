---
name: deployment
description: Use when writing or reviewing Kubernetes or OpenShift deployment manifests and configuration. Triggers on editing YAML with apiVersion and kind, Deployment, Service, Ingress, Route, Helm charts, or kustomization, and when using kubectl or oc. Applies production best practices for resources, probes, security, rollout, and RBAC.
---

# Deployment

Production best practices for shipping workloads to Kubernetes and OpenShift. Detect the platform, apply the Kubernetes baseline, and add the OpenShift specifics when they apply.

## Step 1: Detect the platform

- OpenShift when the `oc` CLI is in use, or manifests use `Route`, `DeploymentConfig`, `BuildConfig`, `ImageStream`, or `SecurityContextConstraints`, or the project targets an OpenShift cluster.
- Kubernetes otherwise: `kubectl`, plain `Deployment`, `Service`, `Ingress`, a Helm chart, or a `kustomization.yaml`.

## Step 2: Apply the guidance

- Always read `references/kubernetes.md`. It is the baseline for both platforms.
- On OpenShift, also read `references/openshift.md` for the deltas: Routes, security context constraints, DeploymentConfig, builds, and the `oc` workflow.

## Non-negotiables

- Set memory requests and limits, and CPU requests, on every container.
- Every workload has readiness and liveness probes that check internal state only.
- Harden the security context: run as non-root, drop all capabilities, and use a read-only root filesystem where possible.
- Never deploy `:latest`. Pin a version tag or a digest.
- Secrets never live in ConfigMaps. RBAC grants least privilege, never `*`.
