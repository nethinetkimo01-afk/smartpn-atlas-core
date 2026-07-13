// Task O-1 — 移除 ART 選單缺漏修復（群組聯集）
// 1) 選單列出群組聯集全部 ART（含掛在另一 header 的 ARTX-60ONLY）
// 2) 移除掛 h201 的 ARTX-60ONLY → h201 級聯刪、h202(eolr120) 仍在、徽章即時消失
// 3) 單 header 單 ART → 最後一個警告迴歸
// 4) Task O 寬鬆比對/rowcount 迴歸
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskO1_group';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
const H60 = 201, H120 = 202;
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };

async function login(browser, u, pw) {
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 1000 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept().catch(() => {}));
  page.on('pageerror', e => result.errors.push(u + ': ' + e));
  await ctx.request.post(BASE + '/api/login', { data: { username: u, password: pw } });
  return { ctx, page };
}
async function openIE(page) {
  await page.goto(`${BASE}/ie`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody tr', { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(800);
}
async function headerExists(ctx, hid) {
  const d = await (await ctx.request.get(`${BASE}/api/ie/list`)).json();
  return (d.records || []).some(r => r.id === hid);
}
async function artsOf(ctx, hid) {
  const d = await (await ctx.request.get(`${BASE}/api/ie/list`)).json();
  const r = (d.records || []).find(x => x.id === hid);
  return r ? r.arts : null;
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1) union listing (entry via id120=202, but ARTX-60ONLY lives on h201)
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openIE(page);
    const modal = await page.evaluate((h120) => {
      removeArtFromModel(h120);
      const m = document.getElementById('artRemoveModal');
      if (!m) return null;
      const btns = [...m.querySelectorAll('.art-pick-btn')];
      return { count: btns.length, arts: btns.map(b => b.getAttribute('data-art')),
               hids: Object.fromEntries(btns.map(b => [b.getAttribute('data-art'), b.getAttribute('data-hids')])) };
    }, H120);
    result.scenarios.union_listing = {
      modal, includesCrossHeaderArt: !!modal && modal.arts.includes('ARTX-60ONLY'),
      crossHeaderHid: modal && modal.hids['ARTX-60ONLY'],
      PASS: !!modal && modal.count === 3 && modal.arts.includes('ARTX-60ONLY') && modal.hids['ARTX-60ONLY'] === String(H60)
    };
    await page.evaluate(() => document.getElementById('artRemoveModal')?.remove());
    await page.screenshot({ path: OUT + '\\O1_union_modal.png', fullPage: true });
    await ctx.close();
  }

  // 2) remove cross-header ART (ARTX-60ONLY on h201) via entry 202 → h201 cascades, h202 stays
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openIE(page);
    const h60Before = await headerExists(ctx, H60), h120Before = await headerExists(ctx, H120);
    await page.evaluate((h120) => removeArtFromModel(h120), H120);
    await page.waitForTimeout(200);
    await page.evaluate(() => {
      const b = [...document.querySelectorAll('#artRemoveModal .art-pick-btn')].find(x => x.getAttribute('data-art') === 'ARTX-60ONLY');
      if (b) b.click();
    });
    await page.waitForTimeout(1500);
    const h60After = await headerExists(ctx, H60), h120After = await headerExists(ctx, H120);
    const h120Arts = await artsOf(ctx, H120);
    result.scenarios.remove_cross_header = {
      before: { h60: h60Before, h120: h120Before }, after: { h60: h60After, h120: h120After }, h120Arts,
      PASS: h60Before && h120Before && h60After === false && h120After === true &&
            Array.isArray(h120Arts) && h120Arts.length === 2 && !h120Arts.includes('ARTX-60ONLY')
    };
    await ctx.close();
  }

  // 3) after h201 gone, group = single header (h202) with 2 arts; remove down to last → warning
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openIE(page);
    // remove one of the two → 1 left (not last warning yet)
    await page.evaluate((h120) => removeArtFromModel(h120), H120);
    await page.waitForTimeout(150);
    await page.evaluate(() => document.querySelector('#artRemoveModal .art-pick-btn')?.click());
    await page.waitForTimeout(1400);
    // now 1 art left → open again → should show last-ART warning
    await page.evaluate((h120) => removeArtFromModel(h120), H120);
    await page.waitForTimeout(150);
    const warn = await page.evaluate(() => {
      const m = document.getElementById('artRemoveModal');
      return { btns: m ? m.querySelectorAll('.art-pick-btn').length : 0, lastWarn: /刪除整個鞋型/.test(m ? m.textContent : '') };
    });
    await page.evaluate(() => document.getElementById('artRemoveModal')?.remove());
    result.scenarios.last_art_warning = { ...warn, PASS: warn.btns === 1 && warn.lastWarn };
    await ctx.close();
  }

  // 4) Task O regression: nonexistent ART → ok:false (not silent)
  {
    const { ctx } = await login(browser, 'jim', 'admin123');
    const r = await ctx.request.post(`${BASE}/api/ie/remove_art`, { data: { header_id: H120, art: 'NO_SUCH_ZZZ' } });
    const j = await r.json();
    result.scenarios.taskO_regression = { ok: j.ok, error: j.error, PASS: j.ok === false && !!j.error };
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_O1_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
