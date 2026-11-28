# Kubernetes: 2 more causes, from the comments

🎬 Watch the video: https://youtu.be/U8N-DLM4oKc

Two causes suggested by Devang Pandya on LinkedIn: a readiness probe failing on a CPU-throttled container, and a pod
stuck in Pending because its volume can't follow it. Both were reproduced on a [kind](https://kind.sigs.k8s.io/)
cluster with **3 worker nodes** (Kubernetes v1.37), and the error texts in the video are the real ones.

Related videos: [Readiness Probe Failed](https://youtu.be/7SBmD49nmiE) ([`readinessprobe/`](../readinessprobe/)) and
[Pod Stuck in Pending](https://youtu.be/r_57sxRIfaE) ([`pending/`](../pending/)).

## Start
```bash
kind create cluster --config fromcomments/kind.yaml
kubectl label node ck-drain-worker topology.kubernetes.io/zone=zone-a --overwrite
kubectl label node ck-drain-worker2 ck-drain-worker3 topology.kubernetes.io/zone=zone-b --overwrite
kubectl delete namespace shop --ignore-not-found
kubectl apply -f fromcomments/k8s/base.yaml -f fromcomments/k8s/redis.yaml
```

## Cause 1: Readiness probe on a throttled container
```bash
kubectl apply -f fromcomments/k8s/01-probe-throttled/broken.yaml
```
The container runs the web server plus six busy workers (they start 100 seconds in) under a 10m CPU limit, and the
probe allows 1 second. Give it about 3 minutes, then:
```bash
kubectl get pods -n shop -l app=orders-api                  # Running, 0/1 READY
kubectl get events -n shop --field-selector reason=Unhealthy -o custom-columns=COUNT:.count,MESSAGE:.message | grep -v refused
kubectl exec -n shop deploy/orders-api -- cat /sys/fs/cgroup/cpu.stat    # nr_throttled close to nr_periods
diff fromcomments/k8s/01-probe-throttled/broken.yaml fromcomments/k8s/01-probe-throttled/fixed.yaml
kubectl apply -f fromcomments/k8s/01-probe-throttled/fixed.yaml
```
Wait over 3 minutes so the workers are busy again: the pod stays 1/1. It is still throttled (the workers use all
they're given), but 500m leaves the web server enough time to answer inside 3 seconds.

## Cause 2: Volume node affinity
Start clean, cordon the only zone-a node, then apply:
```bash
kubectl delete namespace shop --ignore-not-found && kubectl delete pv orders-data --ignore-not-found
kubectl apply -f fromcomments/k8s/base.yaml -f fromcomments/k8s/redis.yaml
kubectl cordon ck-drain-worker
kubectl apply -f fromcomments/k8s/02-volume-zone/broken.yaml
kubectl get pods -n shop -l app=orders-api                  # Pending
kubectl get events -n shop --field-selector reason=FailedScheduling -o custom-columns=MESSAGE:.message
kubectl get pv orders-data -o jsonpath='{.spec.nodeAffinity.required}'; echo
kubectl get nodes -L topology.kubernetes.io/zone
```
The PersistentVolume (a hostPath volume standing in for a cloud disk) can only be used in zone-a, and the only zone-a
node is cordoned. The fix is to give that zone a node the pod can use; here, the maintenance is done:
```bash
kubectl uncordon ck-drain-worker
kubectl get pods -n shop -l app=orders-api -o wide          # Running on ck-drain-worker
```
In a real cluster, cloud disks get this node affinity automatically. For new volumes, a StorageClass with
`volumeBindingMode: WaitForFirstConsumer` creates the volume only after the pod is placed, in that pod's zone.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-probe-throttled` | A 10m CPU limit shared with six busy workers, and a 1 second probe timeout | Readiness probe failed: ... context deadline exceeded (Client.Timeout exceeded while awaiting headers) |
| 2 | `02-volume-zone` | The PV is pinned to zone-a and the only zone-a node is cordoned | 2 node(s) didn't match PersistentVolume's node affinity (before Kubernetes 1.33: volume node affinity conflict) |

When you're done: `kind delete cluster --name ck-drain`.

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
