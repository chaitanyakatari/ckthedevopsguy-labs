# Kubernetes Readiness Probe Failed: every cause, reproduced and fixed live

🎬 Watch the video on [youtube.com/@CKTheDevOpsGuy](https://www.youtube.com/@CKTheDevOpsGuy)

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f readinessprobe/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff readinessprobe/k8s/<scenario>/broken.yaml readinessprobe/k8s/<scenario>/fixed.yaml
kubectl apply -f readinessprobe/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Uses `ckthedevopsguy/orders-api:1.5.0`. Cause 7: deploy `healthy.yaml`, wait until ready, then `kubectl scale deploy redis -n shop --replicas=0`; fix by scaling it back to 1.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-wrong-path` | The probe checks the wrong path | HTTP probe failed with statuscode: 404 |
| 2 | `02-wrong-port` | The probe checks the wrong port | connect: connection refused |
| 3 | `03-timeout` | The probe times out | context deadline exceeded |
| 4 | `04-https-scheme` | HTTPS probe, HTTP app | server gave HTTP response to HTTPS client |
| 5 | `05-localhost-bind` | The app listens on localhost | connection refused, on the right port |
| 6 | `06-exec-missing` | The exec probe's tool isn't there | executable file not found in $PATH |
| 7 | `07-dependency-down` | A dependency is down | HTTP probe failed with statuscode: 503 |
| 8 | `08-slow-start` | Slow start, killed by liveness | use a startupProbe |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
