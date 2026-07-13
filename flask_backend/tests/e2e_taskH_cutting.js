// Task H — 裁斷段界面改版 adversarial E2E
// 1) 裁斷機 連刀: default 1; 層1件11刀1→39600; 連刀4→9900(理論/4); 回1→還原; 連刀切換不丟未存值(Task D flush)
// 2) ATOM/EMMA: 只剩 5 欄+名稱, 無後製欄; 舊資料載入不報錯; 總計不含被移除欄
// 3) 裁斷手工: 新增行→名稱+標時→理論自動; 插/刪/切tab不丟; 總計正確
// 4) 亂點: 連刀快速連切; 空行插/刪 不噴錯
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskH_cutting';
const HID = 32;
fs.mkdirSync(OUT, { recursive: true });

const Z = { machine: '裁斷機', hand: '裁斷手工', atom: 'ATOM', emma: 'EMMA' };
const result = { scenarios: {}, errors: [] };

async function newPage(browser, user = 'jim', pw = 'admin123') {
  const ctx = await browser.newContext({ viewport: { width: 1800, height: 1050 } });
  const page = await ctx.newPage();
  const dialogs = [];
  page.on('dialog', d => { dialogs.push(d.message()); d.accept().catch(() => {}); });
  page.on('pageerror', e => result.errors.push(String(e)));
  await ctx.request.post(BASE + '/api/login', { data: { username: user, password: pw } });
  return { ctx, page, dialogs };
}
async function open(page) {
  await page.goto(`${BASE}/ie/${HID}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(700);
}
const num = s => (s == null ? NaN : parseFloat(String(s).replace(/,/g, '')));

const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // ── Scenario 1: 連刀 formula + default + flush ──
  {
    const { page } = await newPage(browser);
    await open(page);
    const sel = '#tbody-cut-裁斷機 tr:first-child';
    const defIl = await page.$eval('#tbody-cut-裁斷機 select.cut-interlock', el => el.value);
    // set 層1 件11 刀1 on first row
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '1');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="qty_per_pair"]', '11');
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="cut_per_hour"]', '1');
    await page.waitForTimeout(300);
    const std1 = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    const th1  = await page.$eval('#tbody-cut-裁斷機 .cutting-th-a', el => el.textContent);
    // change 連刀 -> 4
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '4');
    await page.waitForTimeout(400);
    const std4 = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    const th4  = await page.$eval('#tbody-cut-裁斷機 .cutting-th-a', el => el.textContent);
    // flush check: layers input still shows 1 (連刀 change did NOT reload)
    const layAfter = await page.$eval('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', el => el.value);
    // back to 1
    await page.selectOption('#tbody-cut-裁斷機 select.cut-interlock', '1');
    await page.waitForTimeout(400);
    const stdBack = await page.$eval('#tbody-cut-裁斷機 .cutting-std-a', el => el.textContent);
    result.scenarios.interlock = {
      default: defIl, std_il1: std1, theory_il1: th1, std_il4: std4, theory_il4: th4,
      layers_after_il_change: layAfter, std_back_to_il1: stdBack,
      PASS: defIl === '1' && num(std1) === 39600 && num(th1) === 1320 &&
            num(std4) === 9900 && num(th4) === 330 && layAfter === '1' && num(stdBack) === 39600
    };
    await page.screenshot({ path: OUT + '\\H1_interlock.png', fullPage: true });
    await page.context().close();
  }

  // ── Scenario 2: ATOM/EMMA simplified (no post cols), loads OK ──
  {
    const { page } = await newPage(browser);
    await open(page);
    const probe = await page.evaluate((Z) => {
      const out = {};
      for (const zone of [Z.atom, Z.emma]) {
        const tb = document.getElementById('tbody-cut-' + zone);
        if (!tb) { out[zone] = { present: false }; continue; }
        const dataRow = [...tb.querySelectorAll('tr')].find(tr => tr.querySelector('.del-cell'));
        const cellCount = dataRow ? dataRow.children.length : null;
        // header th text — should NOT contain 削皮/热压/贴补强
        const table = tb.closest('table');
        const headTxt = table.querySelector('thead').textContent;
        out[zone] = {
          present: true, dataRowCells: cellCount,
          hasPostHeaders: /削皮|热压|贴补强|涂边|印线/.test(headTxt),
          hasPostInputs: !!dataRow && !!dataRow.querySelector('input[value][class*="cell-inp"]') // sanity
        };
      }
      return out;
    }, Z);
    // ATOM/EMMA type C → data row cells = del + mat + name + layers + qty + std + theory + act = 8
    const ok = [Z.atom, Z.emma].every(z => probe[z].present && !probe[z].hasPostHeaders &&
                (probe[z].dataRowCells === 8 || probe[z].dataRowCells === null));
    result.scenarios.atomEmma = { probe, PASS: ok };
    await page.screenshot({ path: OUT + '\\H2_atom_emma.png', fullPage: true });
    await page.context().close();
  }

  // ── Scenario 3: 裁斷手工 add + theory auto + total ──
  {
    const { page } = await newPage(browser);
    await open(page);
    const handExists = await page.$('#tbody-cut-裁斷手工');
    // add a row
    await page.click('#tbody-cut-裁斷手工 .add-trigger-row button');
    await page.waitForTimeout(300);
    await page.fill('#add-name-裁斷手工', '手工裁斷測試');
    await page.fill('#add-std-裁斷手工', '60');
    await page.fill('#add-act-裁斷手工', '2');
    await page.click('#tbody-cut-裁斷手工 .btn-inline-ok');
    await page.waitForTimeout(1400);
    // after reload, find the new row: std=60 → theory=60/30=2
    const rowInfo = await page.evaluate(() => {
      const tb = document.getElementById('tbody-cut-裁斷手工');
      const dataRow = [...tb.querySelectorAll('tr')].find(tr => tr.querySelector('.del-cell'));
      if (!dataRow) return null;
      const th = dataRow.querySelector('.theory-cell');
      const nm = dataRow.querySelector('.name');
      const cells = dataRow.children.length;
      const totalRow = tb.querySelector('.zone-total-row');
      return { cells, name: nm ? nm.textContent.trim() : '', theory: th ? th.textContent.trim() : '',
               totalStd: totalRow ? (totalRow.querySelector('.zt-std')||{}).textContent : null,
               totalTheory: totalRow ? (totalRow.querySelector('.zt-theory')||{}).textContent : null };
    });
    result.scenarios.hand = {
      zoneExists: !!handExists, row: rowInfo,
      PASS: !!handExists && rowInfo && rowInfo.cells === 5 && num(rowInfo.theory) === 2 &&
            num(rowInfo.totalStd) === 60 && num(rowInfo.totalTheory) === 2
    };
    await page.screenshot({ path: OUT + '\\H3_hand.png', fullPage: true });
    await page.context().close();
  }

  // ── Scenario 4: fuzz — rapid 連刀 toggle + empty-row insert/cancel, no crash ──
  {
    const { page, dialogs } = await newPage(browser);
    await open(page);
    const selEl = '#tbody-cut-裁斷機 select.cut-interlock';
    for (const v of ['2','8','16','1','4','1']) { await page.selectOption(selEl, v); await page.waitForTimeout(80); }
    // open add row then cancel (empty)
    await page.click('#tbody-cut-裁斷手工 .add-trigger-row button');
    await page.waitForTimeout(150);
    await page.click('#tbody-cut-裁斷手工 .add-row-inline .btn-del'); // cancel
    await page.waitForTimeout(150);
    // confirm empty add -> should alert, not crash
    await page.click('#tbody-cut-裁斷手工 .add-trigger-row button');
    await page.waitForTimeout(150);
    await page.click('#tbody-cut-裁斷手工 .btn-inline-ok'); // empty name -> alert
    await page.waitForTimeout(300);
    result.scenarios.fuzz = {
      pageErrors: result.errors.length,
      emptyAddAlerted: dialogs.some(m => /流程名稱|部件名稱/.test(m)),
      PASS: result.errors.length === 0 && dialogs.some(m => /流程名稱|部件名稱/.test(m))
    };
    await page.context().close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS);
  fs.writeFileSync(OUT + '\\task_H_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
