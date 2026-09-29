# Myriade on Kubernetes

Reference manifests (kustomize) for running Myriade and its code-execution sandbox
on a Kubernetes cluster. Docker Compose (`setup/install.sh`) remains the primary
install path; these manifests carry the same guarantees in Kubernetes terms. Adapt
them to your own GitOps tooling.

```
base/              app + sandbox + NetworkPolicy (Pod Security "restricted"-compatible)
overlays/bwrap/    per-job bubblewrap confinement for the sandbox (needs node + cluster support)
overlays/bwrap-dbt/  the same, plus confined dbt in the app pod (needs idmap-capable volumes)
secret.example.yaml
```

## Install

Requires Kubernetes 1.30+ (`preStop.sleep`; the overlay also uses `appArmorProfile`
and user namespaces).

1. Provide PostgreSQL (a managed instance is recommended) reachable from the cluster.
2. Create the Secret from `secret.example.yaml` (never commit the filled-in copy):
   `kubectl apply -f my-secret.yaml`
3. Pin the release (`images[].newTag` in `base/kustomization.yaml`, or in your own
   overlay; use the same version for both images), then apply:
   ```
   kubectl apply -k base          # or overlays/bwrap, or overlays/bwrap-dbt
   ```
4. Expose the `myriade` Service (port 8080) with your Ingress. Chat streams over
   Server-Sent Events: disable response buffering and allow long-lived responses
   (e.g. `nginx.ingress.kubernetes.io/proxy-buffering: "off"`,
   `proxy-read-timeout: "3600"`).
5. Enable the `code_execution` feature flag for the organization.

## What the manifests guarantee

**One app pod, never two.** The backend keeps schedulers, SSE fan-out and chat stop
signals in process. `replicas: 1` with `strategy: Recreate` is required: a rolling
update would briefly run two pods, executing nightly jobs twice and splitting live
events. Scale the app vertically.

**Uploaded files survive pod replacement** on the `myriade-blobs` PVC
(`/var/lib/myriade/blobs`). Migrations run at app start-up.

**The sandbox cannot reach anything.** The `sandbox-no-egress` NetworkPolicy lets
only the app pod call it and blocks every outbound connection. It is the primary
containment for model-written code and **only works if your CNI enforces
NetworkPolicy** — verify before going live (e.g. run a job that opens a socket).

**Jobs are isolated from each other.** Check `GET http://sandbox:8080/health`:

| `isolation` | Meaning |
|---|---|
| `serial` (base) | No bwrap: each runner pod executes one job at a time and wipes every process and file it left before the next one. Capacity = sandbox replicas. |
| `bwrap` (overlay) | Each job runs in its own bubblewrap namespaces; up to 4 concurrent jobs per pod. |
| `none` | **Not isolated**: a job can read other jobs' data. Happens only with `SANDBOX_ISOLATION=none`, or if the runner is not PID 1 of its container (do not set `shareProcessNamespace`). |

Seeds (query results, uploads) travel to the sandbox over HTTP; no volume is shared
between the app and the sandbox pods.

## Operating notes

- **Capacity.** A busy runner answers 429; the backend retries on a new connection
  for up to 150 s (longer than the longest job), so the Service can route the job
  to an idle replica. A connection refused by a terminating pod is retried once. Add sandbox
  replicas (base) or raise `SANDBOX_MAX_CONCURRENCY` (overlay) if users wait.
- **Restarts.** A job in flight when its sandbox pod dies is lost (the user sees an
  error and the agent can retry). `terminationGracePeriodSeconds: 150` lets a job
  (120 s max) finish during rollouts and drains.
- **Process count.** Compose caps sandbox processes with `pids_limit`; Kubernetes
  has no per-pod equivalent — set the kubelet `podPidsLimit` on sandbox nodes.
- **Debugging.** A serial runner kills every process in its container between
  jobs, so `kubectl exec` sessions into a sandbox pod end when a job finishes.
- **Stuck pod.** If a serial runner cannot wipe what a job left behind, it refuses
  jobs and fails its health checks (503), including after a container restart
  (`/tmp` is an emptyDir that survives it): delete the pod to get a fresh one.
- **Logs.** Both pods log to stdout; use your cluster's log collection. The sandbox
  needs no outbound access for it.

## The `bwrap` overlay

Restores per-job namespaces and concurrent jobs on the sandbox. It relaxes the same
three things the Compose override does, in Kubernetes terms:

- `seccompProfile: Localhost` → install the profile shipped in the app image on
  every node at `<kubelet seccomp root>/myriade/dbt-sandbox.json` (default root:
  `/var/lib/kubelet/seccomp`):
  `docker run --rm --entrypoint cat myriadeai/myriade:<version> /app/docker/seccomp/dbt-sandbox.json > dbt-sandbox.json`
- `appArmorProfile: Unconfined`.
- `procMount: Unmasked`, which requires `hostUsers: false` (user namespaces).

Requirements: user-namespace and ProcMountType support in your Kubernetes version
and container runtime, nodes on Linux 6.3+ (the pod's `/dev/shm` is a tmpfs, which
supports idmapped mounts from 6.3), and a Pod Security level of the
namespace must allow them (`privileged`: `baseline` rejects Unconfined AppArmor and
Unmasked procMount). With the overlay the runner sets `SANDBOX_ISOLATION=bwrap` and
**refuses to start** if bwrap cannot engage, so a misconfigured cluster fails
visibly instead of silently degrading.

**dbt.** The backend runs dbt subprocesses inside the app pod, confined by bwrap
only if the app pod gets the same relaxations: that is `overlays/bwrap-dbt`. It puts
the app pod in a user namespace too, so **every volume it mounts — the blobs PVC
included — must support idmapped mounts** (many NFS/CSI backends do not): otherwise
the app pod never starts. Without it, dbt runs unconfined inside the app pod (the
backend logs a warning); only enable the dbt integration once you accept that.
