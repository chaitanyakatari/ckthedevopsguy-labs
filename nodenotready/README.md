# Kubernetes Node NotReady: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/kBOQxasTQP4

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37), and the
error texts in the video are the real ones. Docker Desktop's built-in Kubernetes works for most labs, but kind is
closest to a cloud cluster.

## Start
```bash
kind create cluster --name ck-lab
kubectl delete namespace shop --ignore-not-found
kubectl apply -f nodenotready/k8s/base.yaml
```
Then apply a scenario's `broken.yaml`, find the problem, compare and fix:
```bash
diff nodenotready/k8s/<scenario>/broken.yaml nodenotready/k8s/<scenario>/fixed.yaml
kubectl apply -f nodenotready/k8s/<scenario>/fixed.yaml
```

## Notes for specific causes
Run on a throwaway cluster. On kind the node is a container: `docker exec <node> systemctl stop kubelet` (cause 1), `... stop containerd` (cause 2), or move `/etc/cni/net.d/*` away (cause 3). Undo with `systemctl start ...`, put the file back and `systemctl restart containerd`.

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | - (no manifest: see the video) | The kubelet stopped | Kubelet stopped posting node status |
| 2 | - (no manifest: see the video) | The container runtime is down | container runtime is down |
| 3 | - (no manifest: see the video) | The pod network isn't ready | cni plugin not initialized |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
