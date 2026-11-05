"""Локальное приложение: окно (pywebview) или браузер + маленький HTTP-сервер на 127.0.0.1."""
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import CREDENTIALS, ROOT, TOKEN, XLSX_PATH
from .db import connect, get_meta
from .report import company_rows

UI = Path(__file__).with_name("ui.html")
TASKS = {
    "sync": ["-m", "jobtracker.sync"],
    "rerate": ["-m", "jobtracker.sync", "--rerate", "--force"],
    "report": ["-m", "jobtracker.sync", "--report-only"],
}
state = {"running": None, "log": [], "code": None}
lock = threading.Lock()


def _closed(status):
    return status.startswith("Отказ") or status == "Offer"


def data():
    conn = connect()
    rows = company_rows(conn)
    for r in rows:
        r["closed"] = _closed(r["status"])
    return {
        "rows": rows,
        "last_sync": get_meta(conn, "last_sync"),
        "setup": {
            "credentials": CREDENTIALS.exists(),
            "token": TOKEN.exists(),
            "api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        },
    }


def run_task(name):
    with lock:
        if state["running"]:
            return False
        state.update(running=name, log=[], code=None)

    def work():
        p = subprocess.Popen([sys.executable, "-u", *TASKS[name]], cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, env={**os.environ, "PYTHONUNBUFFERED": "1"})
        for line in p.stdout:
            state["log"].append(line.rstrip())
        p.wait()
        state.update(code=p.returncode, running=None)

    threading.Thread(target=work, daemon=True).start()
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json", code=200):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _local(self):
        return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self._local():
            return self._send("{}", code=403)
        if self.path == "/":
            return self._send(UI.read_text(), "text/html")
        if self.path == "/api/data":
            return self._send(json.dumps(data(), ensure_ascii=False))
        if self.path == "/api/status":
            return self._send(json.dumps({"running": state["running"], "code": state["code"],
                                          "log": state["log"][-200:]}, ensure_ascii=False))
        self._send("{}", code=404)

    def do_POST(self):
        if not self._local() or self.headers.get("X-JT") != "1":
            return self._send("{}", code=403)
        name = self.path.removeprefix("/api/run/")
        if self.path.startswith("/api/run/") and name in TASKS:
            return self._send(json.dumps({"started": run_task(name)}))
        if self.path == "/api/open-xlsx":
            if not XLSX_PATH.exists():
                run_task("report")
            subprocess.Popen(["open", str(XLSX_PATH)])
            return self._send("{}")
        self._send("{}", code=404)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_port}/"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        import webview
        webview.create_window("Job Tracker", url, width=1240, height=820, min_size=(900, 600))
        webview.start()
    except ImportError:
        webbrowser.open(url)
        threading.Event().wait()


if __name__ == "__main__":
    main()
