// Render a briefing page and report what only a browser can tell you.
//
//   node check_page.cjs <file-or-url> [--shots <dir>] [--width 1360]
//
// Needs playwright resolvable (NODE_PATH, or a local node_modules):
//   npm i playwright && npx playwright install chromium
//
// The checks here are the ones that caught real defects rather than the ones
// that were easy to write: a page can be valid HTML, pass every unit test, and
// still ship with a tab that shows nothing, a heading hidden under the sticky
// header, or white-on-white text in dark mode. None of that is visible from
// the generator's side.
function loadPlaywright() {
  try { return require('playwright'); }
  catch (e) {
    throw new Error('playwright not resolvable - `npm i playwright`, '
      + 'or set NODE_PATH to a node_modules that has it');
  }
}
const {chromium} = loadPlaywright();
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const flags = Object.fromEntries(args.filter(a => a.startsWith('--'))
  .map(a => { const [k, v] = a.replace(/^--/, '').split('='); return [k, v ?? true]; }));
for (let i = 0; i < args.length - 1; i++) {
  if (args[i] === '--shots') flags.shots = args[i + 1];
  if (args[i] === '--width') flags.width = args[i + 1];
}
const target = args.find(a => !a.startsWith('--')
  && a !== flags.shots && String(a) !== String(flags.width));
if (!target) { console.error('usage: check_page.cjs <file-or-url> [--shots <dir>]'); process.exit(2); }
const url = /^https?:\/\//.test(target) ? target : 'file://' + path.resolve(target);
const width = Number(flags.width || 1360);
const shots = flags.shots ? String(flags.shots) : null;
if (shots) fs.mkdirSync(shots, {recursive: true});

function luminance(css) {
  const m = (css.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
  if (m.length < 3) return null;
  const lin = m.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}
function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)];
  if (x === null || y === null) return null;
  const [hi, lo] = x > y ? [x, y] : [y, x];
  return (hi + 0.05) / (lo + 0.05);
}

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  const problems = [];
  const note = (msg) => problems.push(msg);

  // --- desktop, light -------------------------------------------------------
  const page = await browser.newPage({viewport: {width, height: 1000}});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(url, {waitUntil: 'load'});

  const info = await page.evaluate(() => ({
    title: document.title,
    headings: [...document.querySelectorAll('main > section h2')].map(e => e.textContent.trim()),
    duplicateIds: [...document.querySelectorAll('[id]')].map(e => e.id)
      .filter((x, i, a) => a.indexOf(x) !== i),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    images: document.querySelectorAll('img').length,
    externalImages: [...document.querySelectorAll('img')]
      .filter(i => i.src && !i.src.startsWith('data:')).map(i => i.src).slice(0, 5),
    brokenImages: [...document.querySelectorAll('img')]
      .filter(i => i.complete && i.naturalWidth === 0).length,
    externalRefs: [...document.querySelectorAll('link[href],script[src]')]
      .map(e => e.href || e.src).filter(u => /^https?:/.test(u)).slice(0, 5),
    emptyText: document.body.innerText.trim().length < 200,
  }));
  if (info.duplicateIds.length) note(`重复 id: ${info.duplicateIds.join(', ')}`);
  if (info.overflow > 1) note(`桌面横向溢出 ${info.overflow}px`);
  if (info.brokenImages) note(`${info.brokenImages} 张图未加载`);
  if (info.externalImages.length) note(`外链图片（页面不自包含）: ${info.externalImages.join(', ')}`);
  if (info.externalRefs.length) note(`外部 CSS/JS（离线会坏）: ${info.externalRefs.join(', ')}`);
  if (info.emptyText) note('页面几乎没有文字');

  // Headings hidden behind a sticky header read as missing sections.
  const headerHeight = await page.evaluate(() => {
    const h = document.querySelector('header');
    if (!h || getComputedStyle(h).position !== 'sticky') return 0;
    return Math.round(h.getBoundingClientRect().height);
  });
  if (headerHeight) {
    const pad = await page.evaluate(() => parseInt(getComputedStyle(
      document.documentElement).scrollPaddingTop) || 0);
    if (pad < headerHeight) note(`sticky header ${headerHeight}px 高于 scroll-padding-top ${pad}px，锚点跳转会被遮住`);
  }

  // --- tabs: every panel group must be able to show something ---------------
  const tabGroups = await page.$$eval('[data-tabs]', gs => gs.map(g => ({
    key: g.dataset.tabs, tabs: g.querySelectorAll('.tab').length})));
  for (const group of tabGroups) {
    const before = await page.$$eval(`[data-panel-${group.key}]`, ps => ps.map(p => p.hidden));
    if (!before.length) { note(`tab 组 "${group.key}" 没有对应面板`); continue; }
    if (!before.some(h => h === false)) note(`tab 组 "${group.key}" 初始全部隐藏`);
    if (group.tabs > 1) {
      await page.click(`[data-tabs=${group.key}] .tab:nth-of-type(2)`).catch(() => {});
      const after = await page.$$eval(`[data-panel-${group.key}]`, ps => ps.map(p => p.hidden));
      if (JSON.stringify(before) === JSON.stringify(after)) note(`tab 组 "${group.key}" 切换无效果`);
      if (!after.some(h => h === false)) note(`tab 组 "${group.key}" 切换后全部隐藏`);
    }
  }
  if (shots) await page.screenshot({path: path.join(shots, 'desktop.png'), fullPage: false});
  await page.close();

  // --- mobile ---------------------------------------------------------------
  const mobile = await browser.newPage({viewport: {width: 390, height: 844}});
  await mobile.goto(url, {waitUntil: 'load'});
  const overflow = await mobile.evaluate(() => {
    const w = document.documentElement.clientWidth;
    const wide = [...document.querySelectorAll('*')]
      .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.right > w + 1; })
      .slice(0, 5)
      .map(el => el.tagName.toLowerCase()
        + (el.className && el.className.baseVal === undefined && el.className
           ? '.' + String(el.className).split(/\s+/)[0] : ''));
    return {amount: document.documentElement.scrollWidth - w, culprits: [...new Set(wide)]};
  });
  if (overflow.amount > 1) note(`窄屏(390px)溢出 ${overflow.amount}px，来自: ${overflow.culprits.join(', ')}`);
  if (shots) await mobile.screenshot({path: path.join(shots, 'mobile.png')});
  await mobile.close();

  // --- forced themes --------------------------------------------------------
  // Dark declared only inside `@media (prefers-color-scheme: dark)` looks fine
  // until someone on a light machine tries to force dark and nothing happens.
  // Both directions have to work, whichever the OS says.
  const forced = await browser.newPage({viewport: {width, height: 800}, colorScheme: 'light'});
  await forced.goto(url, {waitUntil: 'load'});
  const themes = await forced.evaluate(() => {
    const bg = () => getComputedStyle(document.body).backgroundColor;
    const out = {light: bg()};
    document.documentElement.dataset.theme = 'dark';
    out.forcedDark = bg();
    document.documentElement.dataset.theme = 'light';
    out.forcedLight = bg();
    delete document.documentElement.dataset.theme;
    return out;
  });
  if (themes.forcedDark === themes.light) {
    note('亮色系统下强制 data-theme=dark 无效（暗色规则可能只写在 media query 里）');
  }
  const toggle = await forced.$('[data-theme-toggle]');
  if (!toggle) note('没有主题切换按钮（读者的机器和会议室的光线不是一回事）');
  await forced.close();

  // --- dark mode ------------------------------------------------------------
  const dark = await browser.newPage({viewport: {width, height: 1000}, colorScheme: 'dark'});
  await dark.goto(url, {waitUntil: 'load'});
  const pairs = await dark.evaluate(() => {
    const out = [];
    const seen = new Set();
    const wanted = ['body', '.tab[aria-pressed=true]', '.tab', '.card', '.kpi strong',
                    'table.data td', '.notice', 'footer'];
    for (const sel of wanted) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const s = getComputedStyle(el);
      let bg = s.backgroundColor, node = el;
      while (bg === 'rgba(0, 0, 0, 0)' && node.parentElement) {
        node = node.parentElement; bg = getComputedStyle(node).backgroundColor;
      }
      const key = sel + s.color + bg;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({sel, fg: s.color, bg});
    }
    return out;
  });
  for (const p of pairs) {
    const r = contrast(p.fg, p.bg);
    if (r !== null && r < 4.5) note(`暗色模式 ${p.sel} 对比度 ${r.toFixed(2)}:1 (底 ${p.bg} 字 ${p.fg})`);
  }
  if (shots) await dark.screenshot({path: path.join(shots, 'dark.png')});
  await dark.close();
  await browser.close();

  const size = /^file:/.test(url) ? fs.statSync(url.replace('file://', '')).size : null;
  console.log(JSON.stringify({
    title: info.title,
    sections: info.headings,
    images: info.images,
    sizeMB: size ? +(size / 1e6).toFixed(2) : null,
    jsErrors: errors,
    problems,
  }, null, 1));
  if (errors.length) console.error('\nJS 报错:\n  ' + errors.join('\n  '));
  if (problems.length) { console.error('\n问题:\n  ' + problems.join('\n  ')); process.exit(1); }
  console.error('\n体检通过');
})().catch(e => { console.error(e); process.exit(1); });
