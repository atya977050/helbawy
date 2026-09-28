from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

os.chdir(PUBLIC)

server = ThreadingHTTPServer(
    ("127.0.0.1", 8080),
    SimpleHTTPRequestHandler
)

print("Generated project: http://127.0.0.1:8080")
server.serve_forever()
