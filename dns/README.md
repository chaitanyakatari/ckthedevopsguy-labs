# Kubernetes DNS Failures: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/cLwmaKqMT4o

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f dns/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff dns/k8s/<scenario>/broken.yaml dns/k8s/<scenario>/fixed.yaml
kubectl apply -f dns/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Deploy `base.yaml`, `redis.yaml`, `orders-api.yaml` (namespace shop), then `storefront.yaml` or a scenario (namespace web). Watch: `kubectl logs -n web deploy/storefront --tail=2`. Cause 3: `kubectl scale deploy coredns -n kube-system --replicas=0` (restore to 2!). After changing the ConfigMap (causes 1-2), `kubectl rollout restart deploy/storefront -n web`.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-name-typo` | The name is wrong | Could not resolve host |
| 2 | `02-short-name` | A short name, across namespaces | Could not resolve host |
| 3 | `03-coredns-down` | CoreDNS isn't running | Resolving timed out |
| 4 | `04-egress-policy` | A NetworkPolicy blocks DNS | Resolving timed out |
| 5 | `05-dnspolicy-default` | dnsPolicy: Default | "Default" is not the default |
| 6 | `06-host-network` | hostNetwork pods | need ClusterFirstWithHostNet |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
