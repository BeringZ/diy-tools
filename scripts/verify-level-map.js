/**
 * verify-level-map.js — 真实运行时验证 level-map 副本渲染
 * 用 playwright-core + 本地 chromium headless shell 截图并断言关键元素
 */
const path = require('path');
const pw = require('playwright-core');

(async () => {
  const exe = '/Users/bering/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell';
  const browser = await pw.chromium.launch({ executablePath: exe, headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto('http://127.0.0.1:8901/level-map.html', { waitUntil: 'networkidle' });

  const checks = {
    banner: await page.locator('#br-banner').count(),
    bannerText: await page.locator('#br-banner').textContent().catch(() => ''),
    backLink: await page.locator('a.br-back').getAttribute('href').catch(() => null),
    courseCards: await page.locator('.card').count(),
    navItems: await page.locator('.course-nav-item').count(),
    monitorHidden: await page.locator('#monitor').isHidden().catch(() => 'n/a'),
    localhostLinks: await page.locator('a[href^="http://localhost:3000/classroom/"]').count(),
    title: await page.title(),
  };
  console.log(JSON.stringify(checks, null, 2));

  await page.screenshot({ path: path.join(__dirname, '.verify-level-map.png') });

  // 滚动到课程区截图
  await page.locator('.course-block').first().scrollIntoViewIfNeeded().catch(() => {});
  await page.screenshot({ path: path.join(__dirname, '.verify-level-map-2.png') });

  // 首页卡片验证
  await page.goto('http://127.0.0.1:8901/index.html', { waitUntil: 'networkidle' });
  const idx = {
    maicCard: await page.locator('.tool-card', { hasText: 'MAIC 课程地图' }).count(),
    statReady: await page.locator('#statReady').textContent(),
    useHref: await page.locator('.tool-card', { hasText: 'MAIC 课程地图' }).locator('a.btn-primary').getAttribute('href').catch(() => null),
  };
  console.log(JSON.stringify(idx, null, 2));
  await page.screenshot({ path: path.join(__dirname, '.verify-index.png') });

  await browser.close();

  // 断言
  const fail = [];
  if (!checks.banner) fail.push('横幅未渲染');
  if (checks.backLink !== 'https://beringz.github.io/diy-tools/') fail.push('返回链接错误: ' + checks.backLink);
  if (checks.courseCards < 200) fail.push('课程卡数量异常: ' + checks.courseCards);
  if (checks.localhostLinks < 200) fail.push('localhost 课程链接数量异常: ' + checks.localhostLinks);
  if (checks.monitorHidden !== true) fail.push('monitor 未隐藏');
  if (!idx.maicCard) fail.push('主页 MAIC 卡片缺失');
  if (!idx.useHref || !idx.useHref.includes('level-map.html')) fail.push('主页卡片链接错误: ' + idx.useHref);

  if (fail.length) { console.error('FAIL:\n  ' + fail.join('\n  ')); process.exit(1); }
  console.log('\n✅ 全部渲染验证通过');
})();
