# Kubernetes CronJob Not Running: every cause, reproduced and fixed live

🎬 Watch the video on [youtube.com/@CKTheDevOpsGuy](https://www.youtube.com/@CKTheDevOpsGuy)

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f cronjob/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff cronjob/k8s/<scenario>/broken.yaml cronjob/k8s/<scenario>/fixed.yaml
kubectl apply -f cronjob/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Deploy `base.yaml`, `redis.yaml`, `orders-api.yaml`, then a CronJob scenario. Runs are every minute, so wait a minute or two before checking `kubectl get cronjob,jobs -n shop`.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-suspended` | It's suspended | SUSPEND: True |
| 2 | `02-never-matches` | The schedule never matches | valid, but never due |
| 3 | `03-invalid-schedule` | An invalid schedule | rejected when you apply it |
| 4 | `04-time-zone` | It runs at the wrong hour | the schedule has a time zone |
| 5 | `05-forbid-overlap` | Runs get skipped | JobAlreadyActive |
| 6 | `06-job-fails` | It runs, and fails | BackoffLimitExceeded |
| 7 | `07-deadline` | Killed by its deadline | DeadlineExceeded |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
