# Kubernetes CrashLoopBackOff: 6 real causes, broken and fixed live

🎬 Watch the video: https://youtu.be/wVieweYn-cM

The app is **orders-api**, a small Python web service in the `shop` namespace. It reads `DATABASE_URL`
from a Secret, connects to Redis, and serves `/healthz` and `/orders` on port 8080.

## The image
Pull it:
```bash
docker pull ckthedevopsguy/orders-api:1.4.2
```
or build it yourself from [`app/`](app/):
```bash
docker build -t ckthedevopsguy/orders-api:1.4.2 app
```

## The 3 commands to run every time
```bash
kubectl get pods -n shop -l app=orders-api
kubectl describe pod -n shop -l app=orders-api | grep -A5 'Last State'
kubectl logs -n shop deploy/orders-api --tail=3
```

## Try each cause
Start clean, deploy the base, then a broken manifest:
```bash
kubectl delete namespace shop --ignore-not-found
kubectl apply -f k8s/base.yaml
kubectl apply -f k8s/redis.yaml          # skip this one for cause 5
kubectl apply -f k8s/01-missing-secret/broken.yaml
```
Find the problem, compare, and fix:
```bash
diff k8s/01-missing-secret/broken.yaml k8s/01-missing-secret/fixed.yaml
kubectl apply -f k8s/01-missing-secret/fixed.yaml
```

| # | Folder | What breaks | Exit code |
|---|---|---|---|
| 1 | `01-missing-secret` | the Secret key was renamed (`DB_URL` vs `DATABASE_URL`) | 1 |
| 2 | `02-exits-immediately` | the Deployment runs a one-off migration and exits; fix = `migrate-job.yaml` + fixed Deployment | 0 |
| 3 | `03-oomkilled` | memory limit too low for the cache warm-up | 137 |
| 4 | `04-liveness-probe` | liveness probe checks `/health`, the app serves `/healthz` | 137 |
| 5 | `05-dependency-down` | Redis was never deployed; fix = `kubectl apply -f k8s/redis.yaml` + init container | 1 |
| 6 | `06-service-links` | Kubernetes injects `REDIS_PORT=tcp://...` from the `redis` Service; fix = `enableServiceLinks: false` | 1 |

## Exit codes cheat sheet
| Code | Meaning |
|---|---|
| 0 | process finished: wrong command or a one-off task in a Deployment |
| 1 | the app failed: config error or missing dependency |
| 137 | killed: out of memory, or a failed liveness probe |
