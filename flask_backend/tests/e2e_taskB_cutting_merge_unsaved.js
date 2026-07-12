// Task B — test the hypothesis: merge's loadSegment() full-reload DISCARDS uncommitted
// 層數/數量/刀數 edits (they only persist on blur via commitEditStatic). Merge before blur => values vanish.
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://localhost:5057';
const OUT = 'C:\\smartpn-atlas-core\\test_screenshots\\cutting_merge_diag';

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1700, height: 1000 } });
  const page = await ctx.newPage();
  const logs = [];
  page.on('console', m => logs.push(m.type() + ': ' + m.text()));
  await ctx.request.post(BASE + '/api/login', { data: { username: 'jim', password: 'admin123' } });
  await page.goto(BASE + '/ie/1/detail', { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(1000);

  const result = {};

  // read the current layers value of the FIRST 裁斷機 row
  const readFirst = () => page.evaluate(() => {
    const tb = document.getElementById('tbody-cut-裁斷機');
    const inp = tb.querySelector('input[data-cfield="layers_per_cut"]');
    return inp ? inp.value : null;
  });
  result.beforeType = await readFirst();

  // Type a NEW value into 層數 of row1 WITHOUT committing (no blur), then immediately trigger
  // a merge (submitMerge -> loadSegment). Simulates "user edits then merges before blur".
  result.typedValue = '99';
  await page.evaluate((typed) => {
    const tb = document.getElementById('tbody-cut-裁斷機');
    const inp = tb.querySelector('input[data-cfield="layers_per_cut"]');
    inp.focus();
    inp.value = typed;
    inp.dispatchEvent(new Event('input', { bubbles: true }));  // recalc, but NOT blur/save
  }, result.typedValue);
  result.domValueAfterType = await readFirst();

  // Now merge two OTHER rows (seq 4,5) so the merge succeeds and the page reloads.
  const cell = await (await ctx.request.get(BASE + '/api/ie/cell/1?segment=cutting&eolr=120&stage_id=1')).json();
  const z = (cell.zones || []).find(z => z.zone === '裁斷機');
  const bySeq = {}; z.rows.forEach(r => bySeq[r.seq] = r.id);
  // Fire submitMerge via the real UI functions WITHOUT blurring the edited input first:
  await page.evaluate(({ ids }) => {
    // mimic what submitMerge does after modal (multi-select) — the exact reload path
    return fetch('/api/ie/cell/save_group', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ header_id: 1, segment: 'cutting', zone: '裁斷機', stage_id: 1, process_ids: ids, headcount: 4, note: '' }) })
      .then(() => loadSegment('cutting'));   // <-- merge-moment re-render
  }, { ids: [bySeq[4], bySeq[5]] });
  await page.waitForTimeout(800);

  result.valueAfterMergeReload = await readFirst();
  result.lost = (result.domValueAfterType === result.typedValue && result.valueAfterMergeReload !== result.typedValue);
  result.logs = logs;

  await page.screenshot({ path: OUT + '\\05_unsaved_edit_after_merge.png', fullPage: true });
  fs.writeFileSync(OUT + '\\unsaved_edit_test.json', JSON.stringify(result, null, 2));
  console.log('UNSAVED TEST: typed=' + result.typedValue + ' domAfterType=' + result.domValueAfterType +
              ' afterMergeReload=' + result.valueAfterMergeReload + ' LOST=' + result.lost);
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
