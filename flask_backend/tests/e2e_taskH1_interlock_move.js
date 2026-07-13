// Task H-1 — 連刀移到「層數」左邊
// 1) 欄序：連刀 在 層數 左邊（表頭+資料列）
// 2) 迴歸：連刀切4→標時÷4；切換不丟未存值
// 3) read_only：連刀顯示為文字，且在新位置（層數左邊）
// 4) 匯入：source header 裁斷機 → target，走通且 interlock_cut 帶過去
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5059';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskH1_interlock';
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
async function open(page, hid) {
  await page.goto(`${BASE}/ie/${hid}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(800);
}
// order probe: within first 裁斷機 data row, cell index of 連刀 vs 層數(first cell-inp)
const orderProbe = () => {
  const tb = document.getElementById('tbody-cut-裁斷機');
  const row = [...tb.querySelectorAll('tr')].find(tr => tr.querySelector('.del-cell'));
  if (!row) return { ok: false };
  const cells = [...row.children];
  const ilIdx = cells.findIndex(td => td.querySelector('select.cut-interlock') || td.classList.contains('ro-il'));
  const layIdx = cells.findIndex(td => td.querySelector('input[data-cfield="layers_per_cut"]'));
  // header order (r6 zh row): text sequence
  const thead = tb.closest('table').querySelector('thead');
  const zhRow = thead.querySelectorAll('tr')[3];
  const zhTxt = [...zhRow.querySelectorAll('th')].map(th => th.textContent.replace(/\s/g, ''));
  return { ilIdx, layIdx, zhTxt };
};

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1+2) admin: order + formula regression + flush
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await open(page, 32);
    const order = await page.evaluate(orderProbe);
    // formula regression on first row — 連刀 先設 1 再驗
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '1');
    await page.waitForTimeout(150);
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '1');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="qty_per_pair"]', '11');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="cut_per_hour"]', '1');
    await page.waitForTimeout(250);
    const stdBefore = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '4');
    await page.waitForTimeout(350);
    const std4 = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    // flush: type layers=7 unsaved then change 連刀, layers must persist
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '7');
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '2');
    await page.waitForTimeout(300);
    const layAfter = await page.$eval('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', el => el.value);
    result.scenarios.admin_order_formula = {
      ilIdx: order.ilIdx, layIdx: order.layIdx, zhHeader: order.zhTxt,
      interlock_left_of_layers: order.ilIdx >= 0 && order.layIdx >= 0 && order.ilIdx < order.layIdx,
      std_il1: stdBefore, std_il4: std4, layers_after_flush: layAfter,
      PASS: order.ilIdx < order.layIdx && num(stdBefore) === 39600 && num(std4) === 9900 && layAfter === '7'
    };
    await page.screenshot({ path: OUT + '\\H1m_order.png', fullPage: true });
    await ctx.close();
  }

  // 3) read_only: 連刀 as text, in new position (before 層數)
  {
    const { page, ctx } = await login(browser, 'tongcai', 'tongcai');
    await open(page, 32);
    const p = await page.evaluate(() => {
      const tb = document.getElementById('tbody-cut-裁斷機');
      const row = [...tb.querySelectorAll('tr')].find(tr => tr.querySelector('.del-cell'));
      const cells = [...row.children];
      // no selects at all (read_only)
      const selects = tb.querySelectorAll('select').length;
      // header zh order still 連刀 before 層數
      const zhRow = tb.closest('table').querySelector('thead').querySelectorAll('tr')[3];
      const zhTxt = [...zhRow.querySelectorAll('th')].map(th => th.textContent.replace(/\s/g, ''));
      const ilPos = zhTxt.indexOf('連刀'), layPos = zhTxt.indexOf('層數');
      return { selects, ilPos, layPos, zhTxt };
    });
    result.scenarios.read_only_pos = {
      selects: p.selects, ilPos: p.ilPos, layPos: p.layPos,
      PASS: p.selects === 0 && p.ilPos >= 0 && p.layPos >= 0 && p.ilPos < p.layPos
    };
    await page.screenshot({ path: OUT + '\\H1m_readonly.png', fullPage: true });
    await ctx.close();
  }

  // 4) import: source h32 裁斷機 → target h3, interlock carried (row set to 2 in DB)
  {
    const { ctx } = await login(browser, 'jim', 'admin123');
    const imp = await ctx.request.post(BASE + '/api/ie/import/apply', {
      data: { target_header_id: 3, source_header_id: 32, segment: 'cutting', zone: '裁斷機', overwrite: true }
    });
    const impJson = await imp.json();
    // interlock 帶入驗證改由 DB 直查（見 bash 步驟）；此處驗證匯入走通
    result.scenarios.import = {
      ok: impJson.ok, imported: impJson.imported_count,
      PASS: impJson.ok === true && impJson.imported_count > 0
    };
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_H1_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
