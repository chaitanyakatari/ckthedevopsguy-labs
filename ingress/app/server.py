"""shop-web: a tiny HTTP app for the Ingress 502/503/504 lab.
Env: BIND (default 0.0.0.0), PORT (default 8080), STARTUP_DELAY seconds before listening (default 0),
     GRACEFUL=1 -> on SIGTERM stop accepting, finish in-flight requests, then exit (default: exit at once).
     DIE_ON=/checkout,... -> those paths behave like /die (an app bug that drops the connection)
Paths: /  /healthz  /sleep?s=N  /bigheader?kb=N  /die (closes the connection without a response)
"""
import os, signal, socket, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOST = socket.gethostname()
DIE_ON = set(p for p in os.environ.get("DIE_ON", "").split(",") if p)

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *a):
        sys.stdout.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % a)); sys.stdout.flush()
    def send(self, code, body, headers=()):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain"); self.send_header("Content-Length", str(len(b)))
        for k, v in headers: self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/":
            self.send(200, "ok from %s\n" % HOST)
        elif u.path == "/healthz":
            self.send(200, "healthy\n")
        elif u.path == "/sleep":
            s = float(q.get("s", ["1"])[0]); time.sleep(s)
            self.send(200, "slept %ss on %s\n" % (s, HOST))
        elif u.path == "/bigheader":
            kb = int(q.get("kb", ["8"])[0])
            self.send(200, "cookie of %dKB from %s\n" % (kb, HOST), [("Set-Cookie", "session=" + "x" * (kb * 1024))])
        elif u.path == "/die" or u.path in DIE_ON:
            self.log_message("%s: closing the connection without a response", u.path)
            self.connection.shutdown(socket.SHUT_RDWR); self.connection.close()
            self.close_connection = True
        else:
            self.send(404, "not found\n")
    def do_POST(self):   # same paths; POST matters because nginx does not retry a non-idempotent request
        n = int(self.headers.get("Content-Length") or 0)
        if n: self.rfile.read(n)
        self.do_GET()

def main():
    bind, port = os.environ.get("BIND", "0.0.0.0"), int(os.environ.get("PORT", "8080"))
    delay = float(os.environ.get("STARTUP_DELAY", "0"))
    if delay:
        print("starting in %ss" % delay, flush=True); time.sleep(delay)
    srv = ThreadingHTTPServer((bind, port), H)
    if os.environ.get("GRACEFUL") == "1":
        srv.daemon_threads = False          # server_close() waits for in-flight requests
        def term(*_):
            print("SIGTERM: draining", flush=True)
            threading.Thread(target=srv.shutdown).start()
        signal.signal(signal.SIGTERM, term)
    else:
        signal.signal(signal.SIGTERM, lambda *_: os._exit(0))   # die at once, mid-request or not
    print("listening on %s:%d" % (bind, port), flush=True)
    srv.serve_forever(); srv.server_close(); print("drained, bye", flush=True)

if __name__ == "__main__":
    main()
