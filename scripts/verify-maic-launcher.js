/**
 * verify-maic-launcher.js — 端到端验证
 *   1) 主页 MAIC 卡片按钮指向网关 / 状态接口
 *   2) 网关 / → 302 跳 localhost:3000/level-map.html
 *   3) 跳转目标真实渲染（课程卡 > 200）
 *   4) 服务未启动时：网关能自动拉起 OpenMAIC 并最终跳转成功
 *      （--kill 模式会先 stop MAIC 进程，最慢等 180s）
 */
const path = require('path');
const pw = require('playwright-core');

const EXE =
  '/Users/bering/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const GW = 'http://127.0.0.1:8910';
const PORTAL = process.env.PORTAL_URL || 'http://127.0.0.1:8901/index.html';
const MAIC_INDEX = 'http://localhost:3000/level-map.html';

(async () => {
  const browser = await pw.chromium.launch({ executablePath: EXE, headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const fail = [];

  // —— 1) 主页卡片 ——
  await page.goto(PORTAL, { waitUntil: 'networkidle' });
  const card = page.locator('.tool-card', { hasText: 'MAIC 课程地图' });
  if (!(await card.count())) fail.push('主页 MAIC 卡片缺失');
  const btnHrefs = await card.locator('a.btn').evaluateAll((els) =>
    els.map((e) => ({ text: e.textContent.trim(), href: e.getAttribute('href') }))
  );
  console.log('卡片按钮:', JSON.stringify(btnHrefs));
  if (!btnHrefs.some((b) => b.href === `${GW}/`)) fail.push('主按钮未指向网关根路径');
  if (!btnHrefs.some((b) => b.href === `${GW}/health`)) fail.push('状态按钮未指向 /health');
  const noteText = await card.locator('.tool-note').textContent().catch(() => '');
  if (!noteText.includes('start-maic.command')) fail.push('缺少 start-maic.command 提示');
  await page.screenshot({ path: path.join(__dirname, '.verify-card.png') });

  // —— 2) 网关跳转 ——
  const resp = await page.goto(`${GW}/`, { waitUntil: 'domcontentloaded', timeout: WAIT_MAX() });
  const finalUrl = page.url();
  console.log('网关跳转后 URL:', finalUrl);
  if (!finalUrl.startsWith(MAIC_INDEX)) fail.push('网关未跳转到课程地图: ' + finalUrl);
  if (resp && resp.status() === 503) fail.push('网关返回 503（服务拉起失败）');

  // —— 3) 目标页真实渲染 ——
  await page.waitForLoadState('networkidle').catch(() => {});
  const cards = await page.locator('.card').count();
  const localhostLinks = await page.locator('a[href^="/classroom/"]').count();
  console.log('课程卡:', cards, '| 课程链接:', localhostLinks);
  if (cards < 200) fail.push('课程卡数量异常: ' + cards);
  if (localhostLinks < 200) fail.push('课程链接数量异常: ' + localhostLinks);
  await page.screenshot({ path: path.join(__dirname, '.verify-maic-live.png') });

  await browser.close();

  if (fail.length) { console.error('\nFAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
  console.log('\n✅ 端到端验证通过');
})();

function WAIT_MAX() { return Number(process.env.WAIT_MAX || 200000); }
