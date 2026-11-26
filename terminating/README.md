# Kubernetes Pod Stuck in Terminating: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/WociR47yGRU

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f terminating/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff terminating/k8s/<scenario>/broken.yaml terminating/k8s/<scenario>/fixed.yaml
kubectl apply -f terminating/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Cause 1: apply `01-finalizer/broken.yaml`, then `kubectl delete pod orders-backup -n shop --wait=false`. Causes 2-3: apply, then delete the pod with `--wait=false`. Cause 4: apply `04-namespace/broken.yaml`, then `kubectl delete namespace old-shop --wait=false`. Remove finalizers with `kubectl patch ... --type=json -p='[{"op":"remove","path":"/metadata/finalizers"}]'` when you're done.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-finalizer` | A finalizer nobody removes | the pod waits forever |
| 2 | `02-ignores-sigterm` | The app ignores SIGTERM | it waits the whole grace period |
| 3 | `03-slow-prestop` | A slow preStop hook | runs before SIGTERM is even sent |
| 4 | `04-namespace` | A namespace stuck in Terminating | content with finalizers remaining |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
