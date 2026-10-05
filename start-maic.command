#!/bin/bash
# 双击运行：启动 MAIC 课程地图网关
# 用法：在访达里双击本文件，或终端执行 ./start-maic.command

cd "$(dirname "$0")" || exit 1

PY=/Users/bering/.workbuddy/binaries/python/versions/3.13.12/bin/python3
PORT=8910
URL="http://127.0.0.1:${PORT}/"

# 网关已在跑就直接打开浏览器
if curl -s -m 2 "http://127.0.0.1:${PORT}/health" > /dev/null 2>&1; then
    echo "网关已在运行，打开浏览器…"
    open "$URL"
    exit 0
fi

echo "启动 MAIC 网关（首次会拉起 OpenMAIC，约 30-90 秒）…"
nohup "$PY" scripts/maic-launcher.py --port "$PORT" > /tmp/maic-launcher-stdout.log 2>&1 &

# 等网关端口就绪
for i in $(seq 1 20); do
    sleep 0.5
    if curl -s -m 1 "http://127.0.0.1:${PORT}/health" > /dev/null 2>&1; then
        echo "网关就绪，打开浏览器…"
        open "$URL"
        exit 0
    fi
done

echo "网关启动超时，请查看 /tmp/maic-launcher.log"
read -r -p "按回车关闭…"
exit 1
