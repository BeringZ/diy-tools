#!/bin/bash
# 双击运行：启动 MAIC 课程地图网关
# 用法：访达里双击本文件，或终端执行 ./start-maic.command

cd "$(dirname "$0")" || exit 1

# 本地探测必须绕过 HTTP 代理：全局代理（Clash / WorkBuddy 透明代理等）会把
# 127.0.0.1 的请求也转发出去，导致 curl 拿到 "upstream connect failed" 而误判网关没跑。
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

PY=/Users/bering/.workbuddy/binaries/python/versions/3.13.12/bin/python3
LAUNCHER=scripts/maic-launcher.py
PORT=8910
PING="http://127.0.0.1:${PORT}/ping"
URL="http://127.0.0.1:${PORT}/"
OUT=/tmp/maic-launcher-stdout.log

alive() { curl -sf -m 2 --noproxy '*' "$PING" > /dev/null 2>&1; }

# 1) 网关已在跑 → 直接开浏览器
if alive; then
    echo "网关已在运行，打开课程地图…"
    open "$URL"
    exit 0
fi

# 2) 端口被占但 /ping 不通 → 僵死/旧版网关残留，杀掉后重来
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1; then
    PIDS=$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null)
    echo "清理端口 ${PORT} 上的残留进程: ${PIDS}"
    for p in $PIDS; do kill "$p" 2>/dev/null; done
    sleep 1
fi

echo "启动 MAIC 网关（首次会拉起 OpenMAIC，约 30-90 秒）…"
nohup "$PY" "$LAUNCHER" --port "$PORT" > "$OUT" 2>&1 &

# 3) 等网关自身就绪（只探测 /ping，最多 20s）
for i in $(seq 1 40); do
    sleep 0.5
    if alive; then
        echo "网关就绪，打开课程地图…"
        open "$URL"
        exit 0
    fi
    # 端口已无人监听 = 网关确实没起来，别再空等（比 pgrep 可靠：pgrep 会误匹配残留 shell）
    if ! lsof -nP -iTCP:"$PORT" -sTCP:LISTEN > /dev/null 2>&1; then
        echo "网关进程已退出，最后 15 行输出："
        tail -15 "$OUT" 2>/dev/null
        echo
        echo "若报 Address already in use：lsof -nP -iTCP:${PORT} -sTCP:LISTEN"
        read -r -p "按回车关闭…"
        exit 1
    fi
done

echo "网关启动超时，最后 15 行输出："
tail -15 "$OUT" 2>/dev/null
echo
echo "详细日志: tail -f /tmp/maic-launcher.log"
read -r -p "按回车关闭…"
exit 1
