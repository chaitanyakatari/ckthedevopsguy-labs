# Kubernetes Ingress 502, 503, 504: every cause, reproduced and fixed live

🎬 Watch the video: https://youtu.be/RBaryU1dW6o

Every broken manifest here was reproduced on a [kind](https://kind.sigs.k8s.io/) cluster (Kubernetes v1.37) with
**ingress-nginx** (chart 4.15.1, controller v1.15.1) and **Envoy Gateway** v1.10.0 in front of the same app, and the
error pages and log lines in the video are the real ones.

> The community ingress-nginx project was archived in March 2026 (no more releases). It still runs in a lot of
> clusters, so these are the errors you'll meet. The last part of the video shows the same bugs on Envoy Gateway with
> the Gateway API.

## What you need
kind, kubectl, helm and Docker. The app (`shop-web`) is a tiny Python server in `app/`: you build it yourself and load
it into kind, so the manifests use `imagePullPolicy: Never`.

## Start
```bash
kind create cluster --config ingress/kind.yaml          # cluster ck-ingress: host 127.0.0.1:8880 -> nginx, :8890 -> Envoy

docker build -t ckthedevopsguy/shop-web:1.0 ingress/app
kind load docker-image ckthedevopsguy/shop-web:1.0 --name ck-ingress

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version 4.15.1 \
  -n ingress-nginx --create-namespace -f ingress/ingress-nginx-values.yaml --wait

kubectl apply -f ingress/k8s/base.yaml -f ingress/k8s/shop-web.yaml -f ingress/k8s/ingress.yaml
kubectl rollout status -n shop deploy/shop-web
curl -si http://shop.localhost:8880/                    # HTTP/1.1 200 OK ... ok from shop-web-...
```
No hosts file needed: curl sends `*.localhost` to 127.0.0.1 by itself.

Optional, for the Envoy Gateway part:
```bash
helm upgrade --install eg oci://docker.io/envoyproxy/gateway-helm --version v1.10.0 \
  -n envoy-gateway-system --create-namespace --wait
kubectl apply -f ingress/k8s/gateway.yaml -f ingress/k8s/httproute.yaml
curl -si http://shop.localhost:8890/                    # 200 through Envoy
```

## Break, read, fix
```bash
kubectl apply -f ingress/k8s/<scenario>/broken.yaml
curl -si http://shop.localhost:8880/                    # the path in the table below
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller --tail=2
diff ingress/k8s/<scenario>/broken.yaml ingress/k8s/<scenario>/fixed.yaml
kubectl apply -f ingress/k8s/<scenario>/fixed.yaml
```
Start each scenario from the healthy state (apply `shop-web.yaml` and `ingress.yaml` again, and
`kubectl delete networkpolicy -n shop --all`).

Things to know:
- For scenarios that change the Deployment (03, 04, 05, 10), delete it first and apply `broken.yaml`:
  `kubectl delete deploy -n shop shop-web`. A rolling update of a broken template keeps the old, working pods serving.
  Then wait a few seconds after the new pods are Running, or you'll see a 503 (no endpoints yet) instead of the 502.
- The 503 warnings (`does not have any active Endpoint`, `Error obtaining Endpoints`) are logged at each controller
  sync, not per request: `kubectl logs -n ingress-nginx deploy/ingress-nginx-controller --since=5m | grep 'active Endpoint'`.
- ingress-nginx retries `error` and `timeout` on the next endpoint, 3 tries: the access log shows `502, 502, 502`, and a
  5 s read timeout makes the client wait 15 s.
- 09: a NetworkPolicy only blocks new connections. Restart the Deployment after applying it
  (`kubectl rollout restart -n shop deploy/shop-web`), or open keepalive connections keep some requests working.
- 10 is statistical. Run 5 parallel clients during a restart and count the codes:
  ```bash
  rm -f codes.txt
  for i in 1 2 3 4 5; do ( end=$(( $(date +%s) + 40 )); while [ $(date +%s) -lt $end ]; do
    curl -s -o /dev/null -m 20 -w '%{http_code}\n' 'http://shop.localhost:8880/sleep?s=1' >> codes.txt; done ) & done
  sleep 3; kubectl rollout restart -n shop deploy/shop-web; wait; sort codes.txt | uniq -c
  ```

## The causes
| # | Folder | What breaks | What you'll see |
|---|---|---|---|
| 1 | `01-selector-mismatch` | The Service selector asks for `app: shop-web-v2` | 503 Service Temporarily Unavailable · `Service "shop/shop-web" does not have any active Endpoint.` |
| 2 | `02-pods-not-ready` | The readiness probe checks `/health`, the app serves `/healthz` | 503, the same warning, pods 0/1 |
| 3 | `11-wrong-service-name` | The Ingress backend names `shop-web-svc` | 503 · `Error obtaining Endpoints for Service "shop/shop-web-svc": no object matching key ... in local store` |
| 4 | `03-listen-localhost` | The app binds 127.0.0.1 | 502 Bad Gateway · `connect() failed (111: Connection refused) while connecting to upstream` |
| 5 | `04-wrong-container-port` | containerPort 8081 named `http` behind `targetPort: http` (app on 8080) | 502, the same Connection refused, upstream port 8081, pods 1/1 |
| 6 | `05-backend-closes` | The app closes the connection on `/checkout` | 502 · `upstream prematurely closed connection while reading response header from upstream` |
| 7 | `06-header-too-big` | `/bigheader?kb=8` sets an 8 KB cookie, the header buffer is 4k by default | 502 · `upstream sent too big header while reading response header from upstream` |
| 8 | `07-backend-protocol-https` | `backend-protocol: "HTTPS"` to a plain HTTP app | 502 · `[crit] ... SSL_do_handshake() failed ... while SSL handshaking to upstream` |
| 9 | `08-read-timeout` | `proxy-read-timeout: "5"`, `/sleep?s=8` takes 8 s | 504 Gateway Time-out after 15 s · `upstream timed out (110: Operation timed out) while reading response header from upstream` |
| 10 | `09-networkpolicy` | A deny-all ingress NetworkPolicy on the app pods | 504 after 15 s · `upstream timed out (110: Operation timed out) while connecting to upstream` |
| 11 | `10-rollout-gap` | No readiness probe, no preStop, the app exits at once on SIGTERM | a few 502 and 504 during `kubectl rollout restart`, 0 after the fix |

### Envoy Gateway (port 8890)
| Bug | Folder | What you'll see |
|---|---|---|
| App on 127.0.0.1 | `03-listen-localhost` | 503 · `upstream connect error or disconnect/reset before headers. reset reason: remote connection failure` |
| Selector typo | `01-selector-mismatch` | 503 with `content-length: 0` |
| Slow page, `/sleep?s=20` | `eg-03-route-timeout` (start from `httproute.yaml`) | 504 `upstream request timeout` after Envoy's default 15 s |
| Wrong backendRef | `eg-04-wrong-backendref` | 500 Internal Server Error with `content-length: 0` |

## The app
`app/server.py`: `/`, `/healthz`, `/sleep?s=N`, `/bigheader?kb=N`, `/die`. Env: `BIND` (default 0.0.0.0), `PORT`
(8080), `STARTUP_DELAY` (seconds before it listens), `GRACEFUL=1` (drain on SIGTERM; default: exit at once),
`DIE_ON=/checkout` (those paths close the connection without a response).

Need help with Kubernetes, CI/CD or cloud costs? **[ckthedevopsguy.com](https://ckthedevopsguy.com)**
