// Task 1 — verify cutting std formula is now ×1.0 (層1件11刀1 -> 39600, theory eolr120 -> 1320).
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://localhost:5057';
const OUT = 'C:\\smartpn-atlas-core\\test_screenshots\\bianche_e2e';
const HID = process.argv[2] || '2';

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1700, height: 1000 } });
  const page = await ctx.newPage();
  await ctx.request.post(BASE + '/api/login', { data: { username: 'jim', password: 'admin123' } });
  await page.goto(BASE + `/ie/${HID}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(1000);

  // fill the FIRST 裁斷機 data row: layers=1, qty=11, cut/H=1
  const r = await page.evaluate(() => {
    const tb = document.getElementById('tbody-cut-裁斷機');
    const tr = [...tb.querySelectorAll('tr')].find(t => t.querySelector('input[data-cfield="layers_per_cut"]'));
    if (!tr) return { error: 'no cutting input row' };
    const set = (f, v) => { const i = tr.querySelector(`input[data-cfield="${f}"]`); i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); };
    set('layers_per_cut', '1'); set('qty_per_pair', '11'); set('cut_per_hour', '1');
    const stdCell = tr.querySelector('.cutting-std-a');
    const thCell = tr.querySelector('.cutting-th-a');
    return { std: stdCell ? stdCell.textContent.trim() : null, theory: thCell ? thCell.textContent.trim() : null };
  });

  await page.waitForTimeout(300);
  await page.screenshot({ path: OUT + '\\task1_formula_x1.0.png', fullPage: true });

  const stdNum = parseFloat(String(r.std).replace(/,/g, ''));
  const thNum = parseFloat(String(r.theory).replace(/,/g, ''));
  const result = {
    input: '層1 件11 刀1', eolr: 120,
    std_displayed: r.std, theory_displayed: r.theory,
    expect_std: 39600, expect_theory: 1320,
    std_PASS: stdNum === 39600, theory_PASS: thNum === 1320,
    note: 'x1.1 would give std=43560/theory=1452; 39600/1320 confirms x1.0'
  };
  fs.writeFileSync(OUT + '\\task1_formula_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
