# Kubernetes ImagePullBackOff: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/Q9iivK18sqQ

The app is **orders-api** (`ckthedevopsguy/orders-api:1.4.2`), a small Python web service in the `shop` namespace.
Every broken manifest here fails with the **real** error text you get on EKS, GKE, AKS or kubeadm.

## Use a kind cluster
Docker Desktop's built-in Kubernetes pulls through its own registry mirror, which changes some of the error
messages. [kind](https://kind.sigs.k8s.io/) pulls with plain containerd, like a cloud cluster:
```bash
kind create cluster --name ck-lab
```

## How to diagnose it
```bash
kubectl get pods -n shop -l app=orders-api
kubectl describe pod -n shop -l app=orders-api | grep 'Failed to pull' | tail -1
```
`kubectl logs` can't help here: the container never started. The answer is in the pod's **Events**.

## Try each cause
Run these from the root of this repo:
```bash
kubectl delete namespace shop --ignore-not-found
kubectl apply -f imagepullbackoff/k8s/base.yaml -f imagepullbackoff/k8s/redis.yaml
kubectl apply -f imagepullbackoff/k8s/01-tag-not-found/broken.yaml
```
Find the problem, compare, and fix:
```bash
diff imagepullbackoff/k8s/01-tag-not-found/broken.yaml imagepullbackoff/k8s/01-tag-not-found/fixed.yaml
kubectl apply -f imagepullbackoff/k8s/01-tag-not-found/fixed.yaml
```

| # | Folder | Status | The message to look for | Fix |
|---|---|---|---|---|
| 1 | `01-tag-not-found` | ImagePullBackOff | `... not found` | Use a tag that was really pushed |
| 2 | `02-repo-not-found` | ImagePullBackOff | `pull access denied, repository does not exist or may require authorization` | Fix the name (a private repo gives the same message) |
| 3 | `03-registry-host` | ImagePullBackOff | `dial tcp: lookup docker.iio ...: no such host` | Fix the registry host |
| 4 | `04-bad-credentials` | ImagePullBackOff | `failed to fetch oauth token ... 401 Unauthorized` | Refresh the pull secret (or drop it for a public image) |
| 5 | `05-wrong-architecture` | ImagePullBackOff | `no match for platform in manifest: not found` | Use a multi-arch image (`docker buildx --platform linux/amd64,linux/arm64`) |
| 6 | `06-never-pull` | ErrImageNeverPull | `is not present with pull policy of Never` | `imagePullPolicy: IfNotPresent` |
| 7 | `07-invalid-name` | InvalidImageName | `repository name ... must be lowercase` | Lowercase the image name |

Cause 5 needs an **arm64** node (Apple silicon, Graviton). On an amd64 machine `1.4.2-amd64` pulls fine.
Cause 6 needs the image to be missing from the node first:
`docker exec ck-lab-control-plane crictl rmi docker.io/ckthedevopsguy/orders-api:1.4.2`

## Seen in production (not reproducible on a laptop)
| Message | Cause | Fix |
|---|---|---|
| `429 Too Many Requests` / `toomanyrequests` | Registry rate limit (Docker Hub limits anonymous pulls per IP) | Authenticate pulls, use a mirror or your own registry |
| `x509: certificate signed by unknown authority` | The node doesn't trust the private registry's certificate | Add the CA to the container runtime on every node |
| `dial tcp ...: i/o timeout` | The node can't reach the registry | Firewall, proxy, NAT gateway or VPC endpoint |

Private registries: the pull secret must be in the **pod's namespace** (or attached to its ServiceAccount),
and ECR login tokens expire after 12 hours, so on EKS let the node IAM role pull from ECR.

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
