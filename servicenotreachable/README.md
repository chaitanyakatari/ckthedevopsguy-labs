# Kubernetes Service Not Reachable: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/FU7Ysfl8gZw

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f servicenotreachable/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff servicenotreachable/k8s/<scenario>/broken.yaml servicenotreachable/k8s/<scenario>/fixed.yaml
kubectl apply -f servicenotreachable/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Apply `base.yaml`, `redis.yaml`, `client.yaml`, then a scenario. Causes 6 and 7 use `healthy.yaml` (7 also `07-other-namespace/web-client.yaml`): the mistake is in the caller's URL. Cause 8: apply `healthy.yaml` then `08-network-policy/broken.yaml`. NetworkPolicy needs a CNI that enforces it (kind's kindnet does).

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-selector-mismatch` | The selector matches nothing | no endpoints |
| 2 | `02-wrong-targetport` | The targetPort is wrong | endpoints exist, nothing listens |
| 3 | `03-localhost-bind` | The app listens on localhost | everything looks right |
| 4 | `04-named-port` | A named targetPort that doesn't exist | endpoints, but no port |
| 5 | `05-not-ready` | The pod isn't ready | endpoints exist, but not ready |
| 6 | - (no manifest: see the video) | Calling the container port | Connection timed out |
| 7 | `07-other-namespace` | Calling from another namespace | Could not resolve host |
| 8 | `08-network-policy` | A NetworkPolicy blocks it | Connection timed out |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
