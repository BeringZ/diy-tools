#!/usr/bin/env python3
"""
maic-launcher.py — MAIC 课程地图启动网关

作用：把「点开课程地图」变成「自动确保服务在跑 → 跳转过去」。

访问 http://127.0.0.1:8910/ 时的行为：
  1. 探测 OpenMAIC（localhost:3000/api/health）
  2. 未启动 → 拉起 PostgreSQL + Next.js 服务（后台，日志见 LOG 路径）
  3. 轮询等待就绪（最长 WAIT_MAX 秒）
  4. 就绪后 302 跳到 http://localhost:3000/level-map.html

前置：PostgreSQL 必须先起（OpenMAIC agent runtime 依赖）。
用法：python3 scripts/maic-launcher.py [--port 8910]
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

MAIC_DIR = "/Users/bering/WorkBuddy/MAIC/OpenMAIC"
MAIC_PORT = 3000
MAIC_HEALTH = f"http://localhost:{MAIC_PORT}/api/health"
MAIC_INDEX = f"http://localhost:{MAIC_PORT}/level-map.html"
PG_CTL = "/opt/homebrew/opt/postgresql@16/bin/pg_ctl"
PG_ISREADY = "/opt/homebrew/opt/postgresql@16/bin/pg_isready"
PG_DATA = "/opt/homebrew/var/postgresql@16"
LOG = "/tmp/maic-launcher.log"
WAIT_MAX = 180

# WorkBuddy 会给 node 进程注入 fs 钩子，拦截 symlink，导致 pnpm / next 启动失败，
# 必须清掉这些变量再启动（见 openmaic skill「启动本地服务」章节）。
NODE_BIN = "/Users/bering/.nvm/versions/node/v24.14.0/bin"
CLEAN_ENV = {
    k: v
    for k, v in os.environ.items()
    if k not in ("NODE_OPTIONS", "CODEBUDDY_BROKERED_FS_HOOK_ENABLED")
}
CLEAN_ENV["PATH"] = f"{NODE_BIN}:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def maic_healthy(timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(MAIC_HEALTH, timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def pg_running() -> bool:
    try:
        return subprocess.run(
            [PG_ISREADY], capture_output=True, timeout=10
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def start_pg() -> None:
    if pg_running():
        log("PostgreSQL 已在运行")
        return
    log("启动 PostgreSQL…")
    try:
        subprocess.run(
            [PG_CTL, "-D", PG_DATA, "-l", "/tmp/pg.log", "start"],
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as e:
        log(f"PostgreSQL 启动异常（可忽略，课堂浏览不依赖）: {e}")
    for _ in range(15):
        if pg_running():
            log("PostgreSQL 就绪")
            return
        time.sleep(1)
    log("PostgreSQL 未在 15s 内就绪（继续尝试启动 OpenMAIC）")


def start_maic() -> bool:
    if not os.path.isdir(MAIC_DIR):
        log(f"目录不存在: {MAIC_DIR}")
        return False
    out = open(LOG, "a", encoding="utf-8")
    out.write(f"\n===== 启动 OpenMAIC {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
    out.flush()
    try:
        subprocess.Popen(
            ["pnpm", "dev"],
            cwd=MAIC_DIR,
            env=CLEAN_ENV,
            stdout=out,
            stderr=out,
            start_new_session=True,
        )
    except (OSError, subprocess.SubprocessError) as e:
        log(f"pnpm dev 启动失败: {e}")
        return False
    log("已拉起 pnpm dev（Next.js 冷启动约 30-90s）")
    return True


def ensure_maic() -> bool:
    if maic_healthy():
        log("OpenMAIC 已在运行")
        return True
    log("OpenMAIC 未运行，开始拉起")
    start_pg()
    if not start_maic():
        return False
    deadline = time.time() + WAIT_MAX
    waited = 0
    while time.time() < deadline:
        time.sleep(3)
        waited += 3
        if maic_healthy():
            log(f"OpenMAIC 就绪（等待 {waited}s）")
            return True
        if waited % 15 == 0:
            log(f"等待中… {waited}s / {WAIT_MAX}s")
    log(f"等待超时（{WAIT_MAX}s），请查看 {LOG}")
    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "MAICLauncher/1.0"

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, code: int, html: str) -> None:
        body = html.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            ok = ensure_maic()
            if ok:
                self.send_response(302)
                self.send_header("Location", MAIC_INDEX)
                self.end_headers()
            else:
                self._html(503, FAIL_HTML)
            return

        if path == "/health":
            healthy = maic_healthy()
            self._json(200 if healthy else 503, {
                "maic": "up" if healthy else "down",
                "url": MAIC_INDEX,
                "log": LOG,
            })
            return

        self._json(404, {"error": "not found", "paths": ["/", "/health"]})

    def log_message(self, fmt: str, *args) -> None:
        log("http " + (fmt % args))


FAIL_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>MAIC 启动中…</title>
<meta http-equiv="refresh" content="8"><style>
body{background:#0f1117;color:#e6e9f0;font-family:-apple-system,"PingFang SC",sans-serif;
display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:24px}
.box{max-width:520px;text-align:center}
h1{font-size:22px;margin:0 0 12px}
p{color:#9aa3b5;font-size:14px;line-height:1.8}
code{background:#171a23;padding:2px 6px;border-radius:5px;color:#6ea8fe;font-size:12px}
.spin{display:inline-block;width:16px;height:16px;border:2px solid #262b38;
border-top-color:#6ea8fe;border-radius:50%;animation:sp .8s linear infinite;vertical-align:-3px;margin-right:8px}
@keyframes sp{to{transform:rotate(360deg)}}
</style></head><body><div class="box">
<h1><span class="spin"></span>OpenMAIC 启动中</h1>
<p>Next.js 冷启动通常需要 30-90 秒。<br>本页会在 8 秒后自动重试，成功后自动跳转到课程地图。</p>
<p>若长时间无响应，请查看日志：<br><code>tail -f /tmp/maic-launcher.log</code></p>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description="MAIC 课程地图启动网关")
    ap.add_argument("--port", type=int, default=8910)
    ap.add_argument("--check", action="store_true", help="只检查状态，不启动服务")
    args = ap.parse_args()

    if args.check:
        healthy = maic_healthy()
        print("MAIC:", "up" if healthy else "down")
        print("PG:", "up" if pg_running() else "down")
        return 0 if healthy else 1

    srv = HTTPServer(("127.0.0.1", args.port), Handler)
    log(f"网关已启动: http://127.0.0.1:{args.port}/  →  {MAIC_INDEX}")
    log(f"健康检查: http://127.0.0.1:{args.port}/health")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        log("网关退出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
