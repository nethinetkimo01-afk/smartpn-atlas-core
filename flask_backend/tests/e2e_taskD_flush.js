// Task D — verify flushPendingEdits() prevents loss of unsaved 層/件/刀 on
// merge / tab-switch / delete / insert, keeps regression correct, and on backend-500 does NOT lose data + alerts.
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://localhost:5057';
const OUT = 'C:\\smartpn-atlas-core\\test_screenshots\\cutting_merge_diag';
// HIDs seeded fresh: 3=merge 4=tab 5=delete 6=insert 7=fail500 8=regression
const H = { merge: 3, tab: 4, del: 5, ins: 6, fail: 7, regr: 8 };

const firstLayersJS = () => {
  const tb = document.getElementById('tbody-cut-裁斷機');
  const inp = tb && tb.querySelector('input[data-cfield="layers_per_cut"]');
  return inp ? inp.value : null;
};

async function newPage(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1700, height: 1000 } });
  const page = await ctx.newPage();
  const dialogs = [];
  page.on('dialog', d => { dialogs.push(d.message()); d.accept().catch(() => {}); });
  await ctx.request.post(BASE + '/api/login', { data: { username: 'jim', password: 'admin123' } });
  return { ctx, page, dialogs };
}
async function openDetail(page, hid) {
  await page.goto(`${BASE}/ie/${hid}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(800);
}
const result = { scenarios: {} };

(async () => {
  const browser = await chromium.launch();

  // ── Scenario 1: merge preserves unsaved layers ──
  {
    const { page } = await newPage(browser);
    await openDetail(page, H.merge);
    const before = await page.evaluate(firstLayersJS);
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '8');   // typed, NOT saved
    await page.click('#tbody-cut-裁斷機 .cut-merge-btn');                             // blurs input -> EDITS, opens modal
    await page.waitForSelector('#mergeModal', { state: 'visible' });
    const boxes = page.locator('#mergeProcList input[type=checkbox]');
    await boxes.nth(1).check();                                                       // add a 2nd process
    await page.fill('#mergeHeadcount', '9');
    await page.click('.btn-mok');                                                     // submitMerge -> flush -> save_group -> reload
    await page.waitForTimeout(1500);
    const after = await page.evaluate(firstLayersJS);
    const hasGroup = await page.evaluate(() => !!document.querySelector('#tbody-cut-裁斷機 .group-cell'));
    result.scenarios.merge = { before, typed: '8', after, hasGroup, PASS: after === '8' };
    await page.screenshot({ path: OUT + '\\D1_merge.png', fullPage: true });
    await page.context().close();
  }

  // ── Scenario 2a: tab-switch preserves unsaved layers ──
  {
    const { page } = await newPage(browser);
    await openDetail(page, H.tab);
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '6');
    await page.click('.tab-btn[data-seg="stitching"]');
    await page.waitForTimeout(900);
    await page.click('.tab-btn[data-seg="cutting"]');
    await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 6000 });
    await page.waitForTimeout(700);
    const after = await page.evaluate(firstLayersJS);
    result.scenarios.tabSwitch = { typed: '6', after, PASS: after === '6' };
    await page.context().close();
  }

  // ── Scenario 2b: delete (another row) preserves unsaved layers ──
  {
    const { page } = await newPage(browser);
    await openDetail(page, H.del);
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '5');
    const delBtns = page.locator('#tbody-cut-裁斷機 .btn-del');
    await delBtns.last().click();                                                     // delete last row (confirm auto-accepted)
    await page.waitForTimeout(1400);
    const after = await page.evaluate(firstLayersJS);
    result.scenarios.delete = { typed: '5', after, PASS: after === '5' };
    await page.context().close();
  }

  // ── Scenario 2c: insert (inline add) preserves unsaved layers ──
  {
    const { page } = await newPage(browser);
    await openDetail(page, H.ins);
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '4');
    await page.click('#tbody-cut-裁斷機 .add-trigger-row .btn-add, #tbody-cut-裁斷機 .add-trigger-row button');
    await page.waitForTimeout(300);
    await page.fill('#add-name-裁斷機', 'INSERT TEST');
    await page.click('.btn-inline-ok');                                              // confirmAddCuttingRow -> flush -> reload
    await page.waitForTimeout(1400);
    const after = await page.evaluate(firstLayersJS);
    result.scenarios.insert = { typed: '4', after, PASS: after === '4' };
    await page.context().close();
  }

  // ── Scenario 4: backend 500 on save -> NO data loss + alert, merge NOT executed ──
  {
    const { page, dialogs } = await newPage(browser);
    await page.route('**/api/ie/cell/save', route =>
      route.fulfill({ status: 500, contentType: 'application/json', body: '{"ok":false,"error":"simulated 500"}' }));
    await openDetail(page, H.fail);
    await page.fill('#tbody-cut-裁斷機 input[data-cfield="layers_per_cut"]', '3');
    await page.click('#tbody-cut-裁斷機 .cut-merge-btn');
    await page.waitForSelector('#mergeModal', { state: 'visible' });
    await page.locator('#mergeProcList input[type=checkbox]').nth(1).check();
    await page.fill('#mergeHeadcount', '9');
    await page.click('.btn-mok');
    await page.waitForTimeout(1200);
    const domVal = await page.evaluate(firstLayersJS);
    const hasGroup = await page.evaluate(() => !!document.querySelector('#tbody-cut-裁斷機 .group-cell'));
    result.scenarios.fail500 = {
      typed: '3', domValueAfter: domVal, hasGroup,
      alerted: dialogs.some(m => m.includes('儲存失敗') || m.includes('失敗')),
      dialogs,
      PASS: domVal === '3' && !hasGroup && dialogs.some(m => m.includes('失敗'))
    };
    await page.screenshot({ path: OUT + '\\D4_fail500.png', fullPage: true });
    await page.context().close();
  }

  // ── Scenario 3: regression — saved-data merge keeps rowspan/group/columns correct ──
  {
    const { page, ctx } = await newPage(browser);
    await openDetail(page, H.regr);
    const cell = await (await ctx.request.get(`${BASE}/api/ie/cell/${H.regr}?segment=cutting&eolr=120`)).json();
    const z = (cell.zones || []).find(z => z.zone === '裁斷機');
    const bySeq = {}; z.rows.forEach(r => bySeq[r.seq] = r.id);
    await ctx.request.post(`${BASE}/api/ie/cell/save_group`, { data: { header_id: H.regr, segment: 'cutting', zone: '裁斷機', stage_id: null, process_ids: [bySeq[1], bySeq[2], bySeq[3]], headcount: 9, note: '' } });
    await page.evaluate(() => loadSegment('cutting'));
    await page.waitForTimeout(900);
    const probe = await page.evaluate(() => {
      const tb = document.getElementById('tbody-cut-裁斷機');
      const rows = [];
      for (const tr of tb.querySelectorAll('tr')) {
        if (!tr.querySelector('.del-cell')) continue;
        const cf = {}; tr.querySelectorAll('input[data-cfield]').forEach(i => cf[i.getAttribute('data-cfield')] = i.value);
        const g = tr.querySelector('.group-cell');
        rows.push({ tdCount: tr.children.length, cfields: cf, group: g ? g.getAttribute('rowspan') : null });
      }
      return rows;
    });
    const grouped = probe.slice(0, 3);
    const allHaveCfields = grouped.every(r => r.cfields.layers_per_cut && r.cfields.qty_per_pair && r.cfields.cut_per_hour);
    result.scenarios.regression = {
      rows: probe, groupRowspan: probe[0] && probe[0].group,
      allGroupedRowsKeepLayersQtyCut: allHaveCfields,
      PASS: probe[0] && probe[0].group === '3' && allHaveCfields
    };
    await page.screenshot({ path: OUT + '\\D3_regression.png', fullPage: true });
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS);
  fs.writeFileSync(OUT + '\\task_D_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
