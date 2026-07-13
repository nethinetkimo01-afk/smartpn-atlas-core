// Task H-2 — 連刀下拉新增 6
// 1) 下拉出現 6（順序 1/2/4/6/8/16）；2) 選 6 → 標時 39600/6=6600、理論連動；
// 3) 連刀切換不丟未存值（flush 迴歸）；4) read_only 顯示文字（迴歸）
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskH2_interlock6';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
const HID = 32;
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
async function open(page) {
  await page.goto(`${BASE}/ie/${HID}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(700);
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // admin: option 6 present + formula + flush
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await open(page);
    const opts = await page.$$eval('#tbody-cut-裁斷機 tr:first-child select.cut-interlock option', els => els.map(o => o.value));
    // set 層1件11刀1, 連刀=1 → 39600
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '1');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '1');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="qty_per_pair"]', '11');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="cut_per_hour"]', '1');
    await page.waitForTimeout(250);
    const std1 = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    // select 6 → 39600/6 = 6600
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '6');
    await page.waitForTimeout(350);
    const std6 = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    const th6 = await page.$eval('#tbody-cut-裁斷機 .cutting-th-a', el => el.textContent);
    // flush: type layers=7 unsaved, change 連刀, layers persists
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '7');
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '2');
    await page.waitForTimeout(300);
    const layAfter = await page.$eval('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', el => el.value);
    result.scenarios.admin = {
      options: opts, has6: opts.includes('6'), orderOk: JSON.stringify(opts) === JSON.stringify(['1','2','4','6','8','16']),
      std_il1: std1, std_il6: std6, theory_il6: th6, layers_after_flush: layAfter,
      PASS: opts.includes('6') && JSON.stringify(opts) === JSON.stringify(['1','2','4','6','8','16']) &&
            num(std1) === 39600 && num(std6) === 6600 && num(th6) === 220 && layAfter === '7'
    };
    await page.screenshot({ path: OUT + '\\H2b_option6.png', fullPage: true });
    await ctx.close();
  }

  // read_only: 連刀 rendered as text (no select), value readable
  {
    const { page, ctx } = await login(browser, 'tongcai', 'tongcai');
    await open(page);
    const ro = await page.evaluate(() => ({
      selects: document.querySelectorAll('#tbody-cut-裁斷機 select').length,
      inputs: document.querySelectorAll('#mainContent input,#mainContent select').length,
    }));
    result.scenarios.read_only = { ...ro, PASS: ro.selects === 0 && ro.inputs === 0 };
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_H2_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
