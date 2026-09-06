#!/usr/bin/env python3
"""
sync-level-map.py — 把 OpenMAIC 课程索引页同步到 bering room 个人主页（Portal/diy-tools）

源文件: /Users/bering/WorkBuddy/MAIC/OpenMAIC/public/level-map.html （由 update-classroom-index.py 生成，勿手改）
目标:   ../level-map.html （部署到 https://beringz.github.io/diy-tools/level-map.html）

改写内容（源文件不动，改写只发生在输出副本上）:
  1. 课程链接 href="/classroom/<id>" → href="http://localhost:3000/classroom/<id>"
     （GitHub Pages 是子路径部署，根相对链接会失效；改绝对链接后，
       白林本机打开即可直接跳进本地 OpenMAIC 互动课堂）
  2. 注入顶部横幅：快照说明 + 返回 bering room 入口
  3. 隐藏「生成监控」面板（公网快照无生成 API，无意义）
  4. 浏览统计/折叠等 localStorage 功能保持原样（maic-classroom-stats 等）

用法（无参数）:
  python3 scripts/sync-level-map.py
"""
import re
import sys
from datetime import datetime
from pathlib import Path

SRC = Path("/Users/bering/WorkBuddy/MAIC/OpenMAIC/public/level-map.html")
DST = Path(__file__).resolve().parent.parent / "level-map.html"
PORTAL_URL = "https://beringz.github.io/diy-tools/"

BANNER_CSS = """
<style>
/* === bering room 同步注入（sync-level-map.py）=== */
#br-banner {
  position: sticky; top: 0; z-index: 999;
  display: flex; align-items: center; gap: 12px;
  padding: 9px 22px;
  background: linear-gradient(90deg, rgba(110,168,254,.14), rgba(126,224,163,.12));
  border-bottom: 1px solid var(--line);
  font-size: 13px; color: var(--sub);
}
#br-banner b { color: var(--text); font-weight: 700; }
#br-banner .br-host { color: var(--accent); font-family: ui-monospace, Menlo, monospace; font-size: 12px; }
#br-banner a.br-back {
  margin-left: auto; white-space: nowrap;
  color: var(--accent); text-decoration: none; font-weight: 600;
}
#br-banner a.br-back:hover { text-decoration: underline; }
@media (max-width: 720px) { #br-banner { flex-wrap: wrap; } #br-banner .br-desc { display: none; } }
#monitor { display: none !important; }
</style>
"""

BANNER_HTML = (
    '<div id="br-banner">'
    '<span><b>🎓 MAIC 课程地图</b></span>'
    '<span class="br-desc">静态快照 · 点击课程会在本机 '
    '<span class="br-host">localhost:3000</span> 打开互动课堂（需 OpenMAIC 服务在线）</span>'
    f'<a class="br-back" href="{PORTAL_URL}" target="_self">← 返回 bering room</a>'
    '</div>'
)


def main() -> int:
    if not SRC.exists():
        print(f"[ERROR] 源文件不存在: {SRC}")
        return 1

    html = SRC.read_text(encoding="utf-8")
    src_courses = re.search(r"课堂索引 · (\d+) 课", html)
    n_courses = src_courses.group(1) if src_courses else "?"

    # 1) 课程链接改写为本地 OpenMAIC 绝对地址
    html, n_links = re.subn(
        r'href="/classroom/', 'href="http://localhost:3000/classroom/', html
    )

    # 2) 注入样式（</head> 前）
    html = html.replace("</head>", BANNER_CSS + "</head>", 1)

    # 3) 注入横幅（<body> 后）+ 更新标题
    html = re.sub(r"(<body[^>]*>)", r"\1" + BANNER_HTML, html, count=1)
    html = html.replace(
        "<title>", "<title>bering room · ", 1
    ) if False else html  # 保留原标题，避免信息丢失
    html = html.replace(
        "</title>", f" · bering room 快照 {datetime.now().strftime('%Y-%m-%d')}</title>", 1
    )

    DST.write_text(html, encoding="utf-8")
    print(f"[OK] 同步完成: {SRC.name} → {DST}")
    print(f"     课程数: {n_courses} | 改写课程链接: {n_links} 个")
    print(f"     输出大小: {DST.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
