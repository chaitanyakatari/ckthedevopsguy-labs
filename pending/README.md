# Kubernetes Pod Stuck in Pending: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/r_57sxRIfaE

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f pending/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff pending/k8s/<scenario>/broken.yaml pending/k8s/<scenario>/fixed.yaml
kubectl apply -f pending/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Cause 3 needs the node labelled: `kubectl label node <node> disktype=ssd`. Cause 4 needs a taint: `kubectl taint node <node> dedicated=payments:NoSchedule` (remove with `kubectl taint node <node> dedicated-`). Cause 8 needs a cordon: `kubectl cordon <node>` (undo: `kubectl uncordon <node>`). Cause 5: delete the stuck PVC before applying the fix (storageClassName can't change). Cause 6: apply the fix with `kubectl replace --force -f` (anti-affinity is symmetric, a rolling update deadlocks).

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-insufficient-cpu` | Not enough CPU | Insufficient cpu |
| 2 | `02-insufficient-memory` | Not enough memory | Insufficient memory |
| 3 | `03-node-selector` | No node matches the selector | didn't match Pod's node affinity/selector |
| 4 | `04-taint` | A taint the pod doesn't tolerate | had untolerated taint(s) |
| 5 | `05-storage-class` | The volume can't be bound | unbound immediate PersistentVolumeClaims |
| 6 | `06-anti-affinity` | Anti-affinity rules | didn't match pod anti-affinity rules |
| 7 | `07-host-port` | The host port is taken | didn't have free ports |
| 8 | `08-cordoned-node` | The node is cordoned | node(s) were unschedulable |
| 9 | `09-scheduler-name` | A scheduler that doesn't exist | Pending, with no events at all |
| 10 | `10-resource-quota` | There's no pod at all | exceeded quota |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
