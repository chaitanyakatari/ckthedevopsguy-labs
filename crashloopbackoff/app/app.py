"""orders-api: small HTTP service used across the CrashLoopBackOff episodes.

Startup sequence (each step is a real failure point):
  1. read required config (DATABASE_URL)
  2. warm the in-memory product cache (CACHE_WARM_MB)
  3. connect to Redis (REDIS_HOST / REDIS_PORT)
  4. serve HTTP on APP_PORT (default 8080): /healthz, /orders
"""
import json
import os
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


def log(level, msg, **kv):
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "level": level, "svc": "orders-api", "msg": msg}
    entry.update(kv)
    print(json.dumps(entry), flush=True)


def require_env(name):
    value = os.environ.get(name)
    if not value:
        log("FATAL", f"required environment variable {name} is not set", hint="check the Secret/ConfigMap mounted into the pod")
        sys.exit(1)
    return value


def warm_cache():
    mb = int(os.environ.get("CACHE_WARM_MB", "32"))
    log("INFO", "warming product cache", size_mb=mb)
    cache = []
    for _ in range(mb):
        cache.append(bytearray(1024 * 1024))  # touch real memory, 1 MiB at a time
    log("INFO", "product cache ready", size_mb=mb)
    return cache


def connect_redis():
    host = os.environ.get("REDIS_HOST", "redis")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    for attempt in range(1, 4):
        try:
            with socket.create_connection((host, port), timeout=2) as s:
                s.sendall(b"PING\r\n")
                reply = s.recv(64)
            log("INFO", "connected to redis", host=host, port=port, reply=reply.decode().strip())
            return
        except OSError as e:
            log("ERROR", "redis connection failed", host=host, port=port, attempt=attempt, error=str(e))
            time.sleep(1)
    log("FATAL", "giving up on redis after 3 attempts", host=host, port=port)
    sys.exit(1)


def migrate():
    log("INFO", "running schema migrations")
    for step in ["001_create_orders", "002_add_status_index", "003_add_customer_fk"]:
        log("INFO", "applied migration", migration=step)
        time.sleep(0.3)
    log("INFO", "migrations complete, exiting")
    sys.exit(0)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            body = {"status": "ok"}
        elif self.path == "/orders":
            body = {"orders": [{"id": 1042, "status": "shipped"}, {"id": 1043, "status": "pending"}]}
        else:
            self.send_response(404)
            self.end_headers()
            return
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        log("INFO", "http", request=fmt % args)


def main():
    if "--migrate" in sys.argv:
        migrate()
    log("INFO", "starting orders-api", version=os.environ.get("APP_VERSION", "1.4.2"))
    require_env("DATABASE_URL")
    _cache = warm_cache()
    connect_redis()
    port = int(os.environ.get("APP_PORT", "8080"))
    log("INFO", "listening", port=port)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
