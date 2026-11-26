# Kubernetes PVC Stuck in Pending: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/X_J2yib00B0

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f pvcpending/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff pvcpending/k8s/<scenario>/broken.yaml pvcpending/k8s/<scenario>/fixed.yaml
kubectl apply -f pvcpending/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Cause 2: `kubectl annotate storageclass standard storageclass.kubernetes.io/is-default-class=false --overwrite` (restore to true). Cause 4: apply `static-pv.yaml` first. Cause 5: apply `static-pv.yaml` and `05-released-pv/old-claim.yaml`, wait until Bound, delete the old claim, then apply `broken.yaml`. Cause 6: `kubectl scale deploy local-path-provisioner -n local-path-storage --replicas=0` (restore to 1). Causes 1, 3, 4: delete the PVC before applying the fix.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-storageclass-missing` | The StorageClass doesn't exist | storageclass ... not found |
| 2 | `02-no-default-class` | No class, and no default | no storage class is set |
| 3 | `03-access-mode` | An access mode it can't provide | ReadWriteMany on block storage |
| 4 | `04-static-pv-too-small` | No PersistentVolume matches | a pre-created volume that's too small |
| 5 | `05-released-pv` | A Released volume | already bound to a different claim |
| 6 | `06-provisioner-down` | The provisioner isn't running | waiting for a volume to be created |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
