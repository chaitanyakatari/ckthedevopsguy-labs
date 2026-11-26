# Kubernetes HPA Not Scaling: every cause, reproduced and fixed live

🎬 Watch the video on [youtube.com/@CKTheDevOpsGuy](https://www.youtube.com/@CKTheDevOpsGuy)

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f hpa/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff hpa/k8s/<scenario>/broken.yaml hpa/k8s/<scenario>/fixed.yaml
kubectl apply -f hpa/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Install metrics-server: `kubectl apply -f hpa/k8s/metrics-server.yaml` (v0.9.1 with `--kubelet-insecure-tls`, for kind/local labs only). Apply `load.yaml` to generate CPU load. Cause 1: delete metrics-server first. Cause 5: let it scale up, then `kubectl delete deploy load -n shop`.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-no-metrics-server` | No metrics-server | cpu: <unknown> |
| 2 | `02-no-cpu-request` | No CPU request | missing request for cpu |
| 3 | `03-wrong-target` | It targets the wrong workload | FailedGetScale ... not found |
| 4 | `04-max-replicas` | It hit maxReplicas | ScalingLimited: TooManyReplicas |
| 5 | `05-slow-scale-down` | It won't scale down | a 5-minute stabilization window |
| 6 | `06-replicas-in-manifest` | Your manifest fights the HPA | replicas: 1, applied again and again |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
