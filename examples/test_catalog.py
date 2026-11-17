import functools
import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class CatalogTest(unittest.TestCase):
    def test_local_command_collects_real_http_fixture(self):
        root = Path(__file__).resolve().parent
        with ThreadingHTTPServer(
            ("127.0.0.1", 0),
            functools.partial(SimpleHTTPRequestHandler, directory=str(root / "fixture")),
        ) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                result = subprocess.run(
                    [sys.executable, str(root / "catalog" / "main.py"), "--local",
                     "--url", f"http://127.0.0.1:{server.server_port}/"],
                    check=True, capture_output=True, encoding="utf-8",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
                self.assertEqual(json.loads(result.stdout), [
                    {"sku": "FH-001", "title": "航海笔记本", "price": 29.9, "stock": 120},
                    {"sku": "FH-002", "title": "港湾马克杯", "price": 49.0, "stock": 75},
                    {"sku": "FH-003", "title": "灯塔桌面收纳盒", "price": 89.5, "stock": 32},
                ])
            finally:
                server.shutdown()
                thread.join()


if __name__ == "__main__":
    unittest.main()
