# bering room ✏️

白林的 DIY 工具集门户 —— 用 vibe coding 折腾出来的小工具、小游戏与小实验，都堆在这间小房间里。

> 单文件纯静态门户（零依赖），数据集中在 `index.html` 内嵌的 `PROJECTS` 数组，新增项目加一行即可。

## 🎨 设计

- **风格**：涂鸦彩绘（浅色纸底、扁平卡片 + 深蓝描边 + 硬阴影、手绘圆角、背景 doodle）
- **配色**：海洋渐变 `#00C9FF → #92FE9D → #00B4D8 → #0077B6 → #003049`
- **字体**：标题 Caveat（手写体）/ 正文 Inter / 色值与路径 Geist Mono

## 🌐 可见性

- 仓库 `BeringZ/diy-tools` 为 **公开（public）**，站点可公开访问
- 曾短暂设为私有（见日志 v3.1），后改回公开恢复线上访问（v3.2）

## 🚀 部署

- 仓库：`BeringZ/diy-tools`（公开）
- 站点：`https://beringz.github.io/diy-tools/`
- 本地使用：直接双击 `index.html`（本地模式下 file:// 路径可直接点击打开）

## 📝 修改日志 (Changelog)

### 2026-08-01 · v4 — 左侧侧边栏目录
- 新增左侧侧边栏目录：鼠标靠近屏幕左边缘自动呼出，列出「可用 / 待办」全部项目，点击平滑滚动定位到对应卡片
- 涂鸦风样式（白色纸卡片 + 深蓝描边 + Caveat 手绘标题），顶部含「回到顶部」项
- 目录与搜索过滤联动（搜索时只显示匹配项）
- 移动端以 ☰ 按钮呼出（hover 不可用），点击页面空白处或 Esc 关闭

### 2026-08-01 · v3.2 — 仓库改回公开
- `BeringZ/diy-tools` 由私有改回 **public**，重新启用 GitHub Pages，线上站点恢复访问
- README 同步更新

### 2026-08-01 · v3.1 — 仓库短暂转为私有
- 曾将仓库设为 **private**（仅自己可见），公开 Pages 站点随之下线（HTTP 404）
- 私有化导致免费计划下 Pages 配置被移除；后经确认改回公开（v3.2）

### 2026-08-01 · v3 — 可用项目「使用」按钮直达工具本体
- 可用项目按钮从「打开」（跳转 GitHub 仓库页）改为 **「使用」—— 直接运行工具本体**
- Algora 算法可视化部署至其仓库 GitHub Pages：`https://beringz.github.io/algora-visualizer/`（网页模式直接使用）
- 数据模型升级：`useWeb`（线上使用地址）/ `useLocal`（本地 file://）/ `repo`（仓库副按钮）
- 「使用」按钮：本地模式优先打开本地文件，网页模式打开线上部署版
- 推送期间 `github.com` 主站 CONNECT 502，改用 GitHub API 提交，网络恢复后 fetch 对齐

### 2026-08-01 · v2 — 涂鸦彩绘风改造 + 更名
- 品牌名更名 **bering room**
- 视觉从暗色毛玻璃改为**涂鸦彩绘风**：浅色纸底 `#F6FAFB`、白色扁平卡片 + 2.5px 深蓝描边 + 硬阴影（贴纸感）、手绘不规则圆角、卡片轻微歪斜、顶部封口胶带、背景手绘 doodle（星星/波浪/箭头/爱心/感叹号）
- 配色保持不变（海洋渐变 5 色）
- 移除 ColorHarbor 项目及其展示

### 2026-08-01 · v1 — 首版发布
- 「Bering DIY Tools」门户首版（海洋渐变主题，暗色画廊衍生）
- 可用项目 / 待办项目两栏：可用含 ColorHarbor + Algora（可跳转链接）；待办 10 项（本地 5 + 远程 5）索引到本地路径并带描述
- 本地 / 网页模式自动检测 + 「复制路径」按钮（Finder `Cmd+Shift+G` 直达）
- 部署 GitHub Pages：`https://beringz.github.io/diy-tools/`
- 创建仓库 `BeringZ/diy-tools`
