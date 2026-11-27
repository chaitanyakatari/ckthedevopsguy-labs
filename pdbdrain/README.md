# kubectl drain Blocked by a PodDisruptionBudget: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/s2DACOfRuUk

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster with **3 worker nodes**
(Kubernetes v1.37), and the error texts in the video are the real ones. A drain needs somewhere for pods to go, so a
single-node cluster won't do.

## Start
```bash
kind create cluster --config pdbdrain/kind.yaml
kubectl delete namespace shop --ignore-not-found
kubectl apply -f pdbdrain/k8s/base.yaml -f pdbdrain/k8s/redis.yaml -f pdbdrain/k8s/orders-api.yaml -f pdbdrain/k8s/pdb.yaml
kubectl get pdb -n shop        # healthy: ALLOWED DISRUPTIONS 1
```
Then apply a scenario's `broken.yaml`, try a drain, compare and fix:
```bash
kubectl drain ck-drain-worker2 --ignore-daemonsets 2>&1 | head -6
diff pdbdrain/k8s/<scenario>/broken.yaml pdbdrain/k8s/<scenario>/fixed.yaml
kubectl apply -f pdbdrain/k8s/<scenario>/fixed.yaml
kubectl drain ck-drain-worker2 --ignore-daemonsets --timeout=60s
kubectl uncordon ck-drain-worker2
```

## Notes for specific causes
Causes 1, 2 and 4: delete the healthy `orders-api` PDB first, then apply `broken.yaml` (it replaces the budget).
Cause 5: delete the `orders-api` Deployment first; `broken.yaml` recreates it with a readiness probe on a path the app
doesn't serve. Cause 6: delete the Deployment first, then drain `ck-drain-worker` (works) and `ck-drain-worker2`
(blocked). `kubectl uncordon ck-drain-worker` gets you unstuck; roll out `fixed.yaml` only once every node is
schedulable. A failed drain leaves the node cordoned: `kubectl uncordon <node>` when you're done.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-min-available-all` | minAvailable equals the replicas | ALLOWED DISRUPTIONS 0 |
| 2 | `02-max-unavailable-zero` | maxUnavailable: 0 | ALLOWED DISRUPTIONS 0 |
| 3 | `03-single-replica` | One replica with minAvailable 1 | ALLOWED DISRUPTIONS 0 |
| 4 | `04-percentage` | minAvailable "80%" of 3 rounds up to 3 | ALLOWED DISRUPTIONS 0 |
| 5 | `05-unhealthy-pods` | Every pod unready | blocked until unhealthyPodEvictionPolicy: AlwaysAllow |
| 6 | `06-replacement-pending` | Required pod anti-affinity mid-upgrade | replacement Pending, next node blocked |
| 7 | `07-two-pdbs` | Two PDBs select the same pods | This pod has more than one PodDisruptionBudget |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
