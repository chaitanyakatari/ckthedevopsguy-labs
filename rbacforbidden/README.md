# Kubernetes RBAC Forbidden: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/LdSjAUdjD7M

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f rbacforbidden/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff rbacforbidden/k8s/<scenario>/broken.yaml rbacforbidden/k8s/<scenario>/fixed.yaml
kubectl apply -f rbacforbidden/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Apply `base.yaml` and `reporter.yaml`, then a scenario. Call the API from the pod: `kubectl exec -n shop reporter -- /opt/bin/k8s-api /api/v1/namespaces/shop/pods`. Cause 6 creates a ClusterRole/ClusterRoleBinding: delete them afterwards. Cause 7: apply `rbac.yaml` + `broken.yaml`, fix with `kubectl replace --force -f 07-no-token/fixed.yaml`.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-no-binding` | A Role, but no RoleBinding | cannot list resource "pods" |
| 2 | `02-missing-verb` | The verb is missing | get is not list |
| 3 | `03-wrong-apigroup` | The wrong API group | deployments live in "apps" |
| 4 | `04-subresource` | A subresource isn't covered | pods/log, pods/exec are separate |
| 5 | `05-wrong-subject` | The binding names someone else | a subject in the wrong namespace |
| 6 | `06-cluster-scope` | Cluster-wide resources | forbidden ... at the cluster scope |
| 7 | `07-no-token` | No token at all | User "system:anonymous" |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
