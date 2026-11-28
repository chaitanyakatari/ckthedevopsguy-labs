# Kubernetes Pod Evicted: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/HBmxbUFjAyA

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster with **2 worker nodes**
(Kubernetes v1.37), and the error texts in the video are the real ones.

On this version `kubectl get pods` shows an evicted pod as **STATUS Error**. The word `Evicted` is in the pod's
`.status.reason`, and `.status.message` says which resource ran out:
```bash
kubectl get pods -n shop -o custom-columns=POD:.metadata.name,STATUS:.status.phase,REASON:.status.reason,NODE:.spec.nodeName
kubectl get pods -n shop -l app=<app> --field-selector=status.phase=Failed -o jsonpath='{.items[0].status.message}'; echo
```

## Start
```bash
kind create cluster --config evicted/kind.yaml
kubectl delete namespace shop --ignore-not-found
kubectl apply -f evicted/k8s/base.yaml -f evicted/k8s/redis.yaml -f evicted/k8s/orders-api.yaml
kubectl get pods -n shop -o wide        # healthy: orders-api on ck-evict-worker, redis on ck-evict-worker2
```
Then apply a scenario's `broken.yaml`, wait for the eviction, compare and fix:
```bash
kubectl apply -f evicted/k8s/<scenario>/broken.yaml
diff evicted/k8s/<scenario>/broken.yaml evicted/k8s/<scenario>/fixed.yaml
kubectl apply -f evicted/k8s/<scenario>/fixed.yaml
kubectl delete pods -n shop --field-selector=status.phase=Failed      # evicted pods never go away on their own
```
Causes 1 and 2 need nothing else.

## Causes 3 to 5: make the node run low
Filling a whole node takes a while, so the video sets ONE kubelet eviction threshold on `ck-evict-worker` just below
what the node has free. Same kubelet, same eviction code path, less waiting. Back up the kubelet config first:
```bash
docker exec ck-evict-worker cp /var/lib/kubelet/config.yaml /root/kubelet-config.orig
```
See what the node has free (memory in Mi, disk in Mi, free process IDs):
```bash
kubectl get --raw /api/v1/nodes/ck-evict-worker/proxy/stats/summary | python3 -c "import json,sys; n=json.load(sys.stdin)['node']; \
print(n['memory']['availableBytes']//2**20, n['fs']['availableBytes']//2**20, n['rlimit']['maxpid']-n['rlimit']['curproc'])"
```
Set one threshold under `evictionHard` (the video used free memory minus 1000Mi, free disk minus 1500Mi, free PIDs
minus 1500), replacing kind's own line for that signal, then restart the kubelet. Example for memory:
```bash
docker exec ck-evict-worker sh -c "cp /root/kubelet-config.orig /var/lib/kubelet/config.yaml && \
  sed -i '/^  memory.available:/d; s/^evictionHard:/evictionHard:\n  memory.available: 6712Mi/' /var/lib/kubelet/config.yaml && \
  systemctl restart kubelet"
docker exec ck-evict-worker grep -A1 evictionHard /var/lib/kubelet/config.yaml
```
Use `nodefs.available: 358966Mi` for disk and `pid.available: "59130"` for PIDs (with your own numbers).
Check the node: `kubectl get node ck-evict-worker -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}'`.

Things to know:
- The kubelet keeps a pressure condition for **5 minutes** after the node recovers (`evictionPressureTransitionPeriod`).
  Wait it out before you judge the fix.
- While the node has DiskPressure or PIDPressure it is tainted (`node.kubernetes.io/disk-pressure`, `pid-pressure`) and
  new pods stay Pending.
- Cause 4: delete the evicted `log-shipper` pod (its emptyDir goes with it), wait 5 minutes, then apply `fixed.yaml`.
  Cause 5: `kubectl scale deploy worker-pool -n shop --replicas=0`, clean up, wait 5 minutes, then apply `fixed.yaml`.
- On kind every node shares one Docker VM, so memory, disk and PIDs are counted VM-wide. Keep the margins above.
- When you're done, put the original config back:
  `docker exec ck-evict-worker sh -c "cp /root/kubelet-config.orig /var/lib/kubelet/config.yaml && systemctl restart kubelet"`

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-container-storage` | The container writes 100Mi with an ephemeral-storage limit of 50Mi | Pod ephemeral local storage usage exceeds the total limit of containers 50Mi. |
| 2 | `02-emptydir-limit` | It writes 100Mi into an emptyDir with sizeLimit 20Mi | Usage of EmptyDir volume "cache" exceeds the limit "20Mi". |
| 3 | `03-memory-pressure` | A pod with no memory request allocates 1500Mi on a node low on memory | The node was low on resource: memory. ... request is 0, has larger consumption of memory. |
| 4 | `04-disk-pressure` | A pod writes 2500Mi into an emptyDir with no sizeLimit | The node was low on resource: ephemeral-storage. ... request is 0 ... |
| 5 | `05-pid-pressure` | A pod starts 3000 processes at once | The node was low on resource: pids. |

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
