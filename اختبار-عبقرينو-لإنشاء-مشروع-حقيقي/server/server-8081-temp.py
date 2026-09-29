from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PUBLIC = ROOT / "public"

class GeneratedHandler(SimpleHTTPRequestHandler):

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def do_GET(self):
        if self.path == "/api/health":
            return self.send_json({"ok": True, "service": "abqaryno-generated-api"})
        return super().do_GET()

    def do_POST(self):
        return self.send_json({
            "ok": False,
            "error": "API not found"
        }, 404)

os.chdir(PUBLIC)

server = ThreadingHTTPServer(
    ("127.0.0.1", 8081),
    GeneratedHandler
)

print("Generated project: http://127.0.0.1:8080")
server.serve_forever()
