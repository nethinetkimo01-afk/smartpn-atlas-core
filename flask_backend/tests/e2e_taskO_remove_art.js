// Task O — 移除 ART 靜默失敗修復 + 選擇視窗 adversarial E2E
// 1) 選擇視窗列出 ART 正確；點選移除 → 列表即時消失
// 2) 大小寫/含空白的髒 ART 也能移除（seed '  DirtyCase_ZZ  '）
// 3) 移除最後一個 ART → 二次警告(isLast) → 整鞋型消失
// 4) API 直打不存在 ART → ok:false 有錯誤(不靜默)
// 5) read_only/editor：無 ··· 選單；API 403
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskO_removeart';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
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
async function artsOf(ctx, hid) {
  const d = await (await ctx.request.get(`${BASE}/api/ie/list`)).json();
  const rec = (d.records || []).find(r => r.id === hid);
  return rec ? (rec.arts || []) : null;   // null = header gone
}
async function openIE(page) {
  await page.goto(`${BASE}/ie`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody tr', { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(800);
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1+2) admin: modal lists arts; remove dirty (case/space) → gone
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openIE(page);
    const before = await artsOf(ctx, 160);
    const modal = await page.evaluate(() => {
      removeArtFromModel(160);
      const m = document.getElementById('artRemoveModal');
      if (!m) return null;
      const btns = [...m.querySelectorAll('.art-pick-btn')];
      return { count: btns.length, arts: btns.map(b => b.getAttribute('data-art')) };
    });
    // click the dirty ART button (data-art contains 'DirtyCase')
    await page.evaluate(() => {
      const b = [...document.querySelectorAll('#artRemoveModal .art-pick-btn')].find(x => /DirtyCase/.test(x.getAttribute('data-art')));
      if (b) b.click();
    });
    await page.waitForTimeout(1500);
    const after = await artsOf(ctx, 160);
    result.scenarios.select_and_remove = {
      beforeCount: before && before.length, modalCount: modal && modal.count,
      hadDirty: !!(modal && modal.arts.some(a => /DirtyCase/.test(a))),
      afterCount: after && after.length,
      PASS: !!modal && modal.count === before.length &&
            modal.arts.some(a => /DirtyCase/.test(a)) &&
            after.length === before.length - 1 &&
            !after.some(a => /DirtyCase/.test(a))
    };
    await page.screenshot({ path: OUT + '\\O1_modal.png', fullPage: true });
    await ctx.close();
  }

  // 3) remove last ART (header 2, single) → warning → header gone
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openIE(page);
    const before = await artsOf(ctx, 69);
    const warn = await page.evaluate(() => {
      removeArtFromModel(69);
      const m = document.getElementById('artRemoveModal');
      return { isLastWarning: /刪除整個鞋型/.test(m ? m.textContent : ''), btns: m ? m.querySelectorAll('.art-pick-btn').length : 0 };
    });
    await page.evaluate(() => document.querySelector('#artRemoveModal .art-pick-btn')?.click());
    await page.waitForTimeout(1500);
    const after = await artsOf(ctx, 69);
    result.scenarios.remove_last = {
      beforeCount: before && before.length, isLastWarning: warn.isLastWarning, headerGone: after === null,
      PASS: before && before.length === 1 && warn.isLastWarning && after === null
    };
    await ctx.close();
  }

  // 4) API nonexistent ART → ok:false (not silent)
  {
    const { ctx } = await login(browser, 'jim', 'admin123');
    const r = await ctx.request.post(`${BASE}/api/ie/remove_art`, { data: { header_id: 3, art: 'NO_SUCH_ART_XYZ' } });
    const j = await r.json();
    result.scenarios.nonexistent = {
      status: r.status(), ok: j.ok, error: j.error,
      PASS: j.ok === false && !!j.error
    };
    await ctx.close();
  }

  // 5) read_only / editor: no ··· menu + API 403
  {
    for (const [u, pw] of [['tongcai', 'tongcai'], ['test_editor', 'testpw123']]) {
      const { page, ctx } = await login(browser, u, pw);
      await openIE(page);
      const noMenu = await page.evaluate(() => document.querySelectorAll('.btn-dot-menu').length === 0);
      const api = await ctx.request.post(`${BASE}/api/ie/remove_art`, { data: { header_id: 3, art: 'x' } });
      result.scenarios['noaccess_' + u] = {
        noDotMenu: noMenu, apiStatus: api.status(),
        PASS: noMenu && api.status() === 403
      };
      await ctx.close();
    }
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_O_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
