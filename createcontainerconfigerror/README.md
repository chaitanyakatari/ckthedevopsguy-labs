# Kubernetes CreateContainerConfigError: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/bpZgjtk2178

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f createcontainerconfigerror/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff createcontainerconfigerror/k8s/<scenario>/broken.yaml createcontainerconfigerror/k8s/<scenario>/fixed.yaml
kubectl apply -f createcontainerconfigerror/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Cause 6 deploys only Redis (`06-run-as-non-root/broken.yaml`). Cause 7 creates the Secret in `default` on purpose.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-secret-missing` | The Secret does not exist | secret "..." not found |
| 2 | `02-secret-key-missing` | The key is not in the Secret | couldn't find key ... in Secret |
| 3 | `03-configmap-missing` | The ConfigMap does not exist | configmap "..." not found |
| 4 | `04-configmap-key-case` | Keys are case-sensitive | couldn't find key ... in ConfigMap |
| 5 | `05-envfrom-missing` | envFrom points at nothing | the whole ConfigMap is missing |
| 6 | `06-run-as-non-root` | runAsNonRoot vs a root image | container has runAsNonRoot and image will run as root |
| 7 | `07-wrong-namespace` | Right Secret, wrong namespace | it exists, just not here |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
