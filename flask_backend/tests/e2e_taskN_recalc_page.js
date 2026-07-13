// Task N — 裁斷重算管理頁 /admin/recalc-cutting adversarial E2E
// 1) admin: 預覽筆數=實改筆數; 執行後 39600-config 列 std=39600; 還原後復原
// 2) 執行中鎖: 並發 apply → 不雙重執行(一個 changed>0, 另一個 busy 或 changed=0)
// 3) manager/editor/read_only: 頁面 403 + 入口不顯示 + 寫入 API 403
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskN_recalc';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
const SEED_PID = 33060;
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };
const num = s => (s == null ? NaN : parseFloat(String(s).replace(/,/g, '')));

async function login(browser, u, pw) {
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 1000 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept().catch(() => {}));
  page.on('pageerror', e => result.errors.push(u + ': ' + e));
  await ctx.request.post(BASE + '/api/login', { data: { username: u, password: pw } });
  return { ctx, page };
}
const stdOf = async (ctx, pid) => {
  const d = await (await ctx.request.get(`${BASE}/api/ie/cell/32?segment=cutting&eolr=120`)).json();
  const z = (d.zones || []).find(z => z.zone === '裁斷機');
  const r = (z ? z.rows : []).find(r => r.id === pid);
  return r ? r.standard_time : null;
};

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1) admin UI: preview → apply → 39600 → rollback
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await page.goto(`${BASE}/admin/recalc-cutting`, { waitUntil: 'networkidle' });
    await page.waitForSelector('#btnPreview', { timeout: 8000 });
    const denied = await page.evaluate(() => document.getElementById('denied').offsetParent !== null);
    // preview
    await page.click('#btnPreview');
    await page.waitForTimeout(900);
    const pv = await page.evaluate(() => ({
      inScope: document.getElementById('pIn').textContent,
      wouldChange: document.getElementById('pChange').textContent,
      excl: document.getElementById('pExcl').textContent,
      sampleRows: document.querySelectorAll('#pRows tr').length,
    }));
    const stdBefore = await stdOf(ctx, SEED_PID);
    // apply (dialog auto-accepted)
    await page.click('#btnApply');
    await page.waitForTimeout(2500);
    const applyText = await page.evaluate(() => document.getElementById('applyResult').textContent);
    const changed = (applyText.match(/實改\s*(\d+)/) || [])[1];
    const stdAfter = await stdOf(ctx, SEED_PID);
    // rollback newest backup
    await page.click('#bkRows button');   // first 還原 button
    await page.waitForTimeout(2500);
    const stdRollback = await stdOf(ctx, SEED_PID);
    result.scenarios.admin_flow = {
      denied, preview: pv, stdBefore, changed, stdAfter, stdRollback,
      PASS: !denied && num(pv.wouldChange) > 0 && num(pv.excl) > 0 &&
            String(num(pv.wouldChange)) === String(changed) &&
            num(stdBefore) === 43560 && num(stdAfter) === 39600 && num(stdRollback) === 43560
    };
    await page.screenshot({ path: OUT + '\\N1_admin.png', fullPage: true });
    await ctx.close();
  }

  // 2) lock: parallel apply — no double execution
  {
    const { ctx } = await login(browser, 'jim', 'admin123');
    // ensure x1.1 state (rollback in scenario 1 restored it)
    const [r1, r2] = await Promise.all([
      ctx.request.post(`${BASE}/api/recalc/cutting/apply`),
      ctx.request.post(`${BASE}/api/recalc/cutting/apply`),
    ]);
    const j1 = await r1.json().catch(() => ({})); const j2 = await r2.json().catch(() => ({}));
    const outcomes = [{ s: r1.status(), j: j1 }, { s: r2.status(), j: j2 }];
    const changedGt0 = outcomes.filter(o => o.j.changed > 0).length;
    const busyOr0 = outcomes.filter(o => o.j.busy === true || o.j.changed === 0).length;
    result.scenarios.lock = {
      statuses: outcomes.map(o => o.s), changedVals: outcomes.map(o => o.j.changed), busy: outcomes.map(o => o.j.busy),
      // 鎖保證：不會兩個都 changed>0（雙重執行）
      PASS: changedGt0 <= 1 && busyOr0 >= 1 && result.errors.length === 0
    };
    // rollback back to x1.1 for cleanliness
    const bks = await (await ctx.request.get(`${BASE}/api/recalc/cutting/backups`)).json();
    if (bks.backups && bks.backups.length) await ctx.request.post(`${BASE}/api/recalc/cutting/rollback`, { data: { backup_file: bks.backups[0].file } });
    await ctx.close();
  }

  // 3) permissions: manager/editor/read_only → page 403 + entry hidden + API 403
  {
    for (const [u, pw] of [['test_mgr', 'testpw123'], ['test_editor', 'testpw123'], ['tongcai', 'tongcai']]) {
      const { page, ctx } = await login(browser, u, pw);
      await page.goto(`${BASE}/ie`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1000);
      const entryHidden = await page.evaluate(() => {
        const b = document.getElementById('btn-recalc-cutting');
        return !b || b.offsetParent === null;
      });
      const pageResp = await ctx.request.get(`${BASE}/admin/recalc-cutting`);
      const apiResp = await ctx.request.post(`${BASE}/api/recalc/cutting/apply`);
      result.scenarios['noaccess_' + u] = {
        entryHidden, pageStatus: pageResp.status(), apiStatus: apiResp.status(),
        PASS: entryHidden && pageResp.status() === 403 && apiResp.status() === 403
      };
      await ctx.close();
    }
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_N_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
