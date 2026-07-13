// Task L — STF 段欄位標準化（向 Assembly 看齊）
// 1) STF 每區塊 8 欄（=assembly）；標準時間/生產目標/理論=公式格(灰)
// 2) 打粗 nt100/ap10 → 標時 110、target/theory 連動
// 3) 照射 舊列(只 std88) → 顯示 88(fallback)、值不變
// 4) 貼底 nt50+存std88 → 公式勝出 55(補正常時間後轉公式)
// 5) Task J 迴歸：STF 實際人數表頭仍「EOLR=190 實際人數」
// 6) read_only 全灰迴歸
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskL_stf';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };
const num = s => (s == null ? NaN : parseFloat(String(s).replace(/,/g, '')));

async function login(browser, u, pw) {
  const ctx = await browser.newContext({ viewport: { width: 1800, height: 1050 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept().catch(() => {}));
  page.on('pageerror', e => result.errors.push(u + ': ' + e));
  await ctx.request.post(BASE + '/api/login', { data: { username: u, password: pw } });
  return { ctx, page };
}
async function openSeg(page, seg, hid = 32) {
  await page.goto(`${BASE}/ie/${hid}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(500);
  await page.evaluate(s => loadSegment(s), seg);
  await page.waitForTimeout(1400);
}
function grabStf() {
  return this.evaluate(() => {
    const zones = {};
    ['打粗', '照射', '水洗', '貼底'].forEach(z => {
      const tb = document.getElementById('tbody-gen-' + z);
      if (!tb) { zones[z] = null; return; }
      const table = tb.closest('table');
      const headerCols = table.querySelectorAll('thead th').length; // 含最左空th
      const actualHdr = (table.querySelector('th.th-actual') || {}).textContent || null;
      const rows = [];
      tb.querySelectorAll('tr').forEach(tr => {
        if (!tr.querySelector('.del-cell')) return;
        const fcs = [...tr.querySelectorAll('td.formula-cell')].map(c => c.textContent.trim());
        rows.push({ cellCount: tr.children.length, formulaCells: fcs });
      });
      zones[z] = { headerCols, actualHdr, rows };
    });
    return zones;
  });
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // admin: columns + formulas + Task J header
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openSeg(page, 'stf');
    const stf = await grabStf.call(page);
    // assembly cellCount for 看齊比對
    await openSeg(page, 'assembly');
    const asmCell = await page.evaluate(() => {
      const tb = document.querySelector('[id^="tbody-gen-"]');
      const row = tb ? [...tb.querySelectorAll('tr')].find(r => r.querySelector('.del-cell')) : null;
      const table = tb ? tb.closest('table') : null;
      return { headerCols: table ? table.querySelectorAll('thead th').length : null, rowCells: row ? row.children.length : null };
    });
    const zoneList = ['打粗', '照射', '水洗', '貼底'];
    const all8 = zoneList.every(z => stf[z] && stf[z].headerCols === asmCell.headerCols);
    const actualAllRenamed = zoneList.every(z => stf[z] && stf[z].actualHdr === 'EOLR=190 實際人數');
    // 打粗 first row std=110
    const cu = stf['打粗'].rows[0];      // nt100/ap10 → 110
    const zh = stf['照射'].rows[0];      // std88 only → 88
    const td = stf['貼底'].rows[0];      // nt50/std88 → 55
    result.scenarios.columns_formula = {
      assemblyHeaderCols: asmCell.headerCols, stfHeaderCols: zoneList.map(z => stf[z] && stf[z].headerCols),
      all_STF_match_assembly: all8, taskJ_header_kept: actualAllRenamed,
      cuploc_std: cu.formulaCells[0], zhaoshe_std: zh.formulaCells[0], tiedi_std: td.formulaCells[0],
      cuploc_target: cu.formulaCells[1], cuploc_theory: cu.formulaCells[2],
      PASS: all8 && actualAllRenamed &&
            num(cu.formulaCells[0]) === 110 && num(zh.formulaCells[0]) === 88 && num(td.formulaCells[0]) === 55 &&
            num(cu.formulaCells[1]) > 0 && num(cu.formulaCells[2]) > 0
    };
    await page.screenshot({ path: OUT + '\\L1_stf_cols.png', fullPage: true });
    await ctx.close();
  }

  // 真實資料端到端：header 160(未鎖) 的 STF 列已有 normal_time → 標時應=normal×(1+寬放/100)
  // 證明「有正常時間即轉公式值」在真實 DB 資料上成立（不只 seeded）
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openSeg(page, 'stf', 160);
    const checks = await page.evaluate(() => {
      const out = [];
      ['打粗', '照射', '水洗', '貼底'].forEach(z => {
        const tb = document.getElementById('tbody-gen-' + z);
        if (!tb) return;
        const row = [...tb.querySelectorAll('tr')].find(r => r.querySelector('.del-cell'));
        if (!row) return;
        const inputs = [...row.querySelectorAll('td input.cell-inp')];
        const normal = inputs.length ? parseFloat(inputs[0].value) : NaN;
        const allowInp = inputs[1] ? parseFloat(inputs[1].value) : NaN;
        const allow = isNaN(allowInp) ? 10 : allowInp;
        const std = parseFloat((row.querySelector('td.formula-cell') || {}).textContent);
        out.push({ zone: z, normal, allow, std, expect: isNaN(normal) ? null : Math.round(normal * (1 + allow / 100) * 10000) / 10000 });
      });
      return out;
    });
    // 每個有 normal_time 的列：std 應等於 normal×(1+allow/100)
    const verified = checks.filter(c => !isNaN(c.normal));
    const allOk = verified.length > 0 && verified.every(c => Math.abs(c.std - c.expect) < 0.05);
    result.scenarios.formula_realdata = {
      checks, verifiedRows: verified.length, allMatch: allOk,
      PASS: allOk
    };
    await page.screenshot({ path: OUT + '\\L2_realdata.png', fullPage: true });
    await ctx.close();
  }

  // read_only 全灰 regression + Task J header
  {
    const { page, ctx } = await login(browser, 'tongcai', 'tongcai');
    await openSeg(page, 'stf');
    const ro = await page.evaluate(() => ({
      inputs: document.querySelectorAll('#mainContent input,#mainContent select').length,
      headers: [...document.querySelectorAll('#mainContent th.th-actual')].map(t => t.textContent.trim()),
    }));
    result.scenarios.read_only = {
      inputs: ro.inputs, headersAllRenamed: ro.headers.length > 0 && ro.headers.every(h => h === 'EOLR=190 實際人數'),
      PASS: ro.inputs === 0 && ro.headers.length > 0 && ro.headers.every(h => h === 'EOLR=190 實際人數')
    };
    await page.screenshot({ path: OUT + '\\L3_readonly.png', fullPage: true });
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_L_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
