// Task B — reproduce 裁斷合併 render bug (層數/數量/刀數 disappear on merge).
// Captures console + network + DOM (before/after) for contiguous and non-contiguous merges.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = 'http://localhost:5057';
const OUT = 'C:\\smartpn-atlas-core\\test_screenshots\\cutting_merge_diag';
const HID = 1, ZONE = '裁斷機';

// serialize the 裁斷機 tbody: for each data row, list cells (class + value/text)
function rowProbe() {
  const tb = document.getElementById('tbody-cut-' + '裁斷機');
  if (!tb) return { error: 'no tbody' };
  const out = [];
  for (const tr of tb.querySelectorAll('tr')) {
    if (tr.classList.contains('add-trigger-row') || tr.classList.contains('add-row-inline')) continue;
    if (!tr.querySelector('.del-cell') && !tr.querySelector('.group-cell')) {
      // total row etc.
      out.push({ kind: 'other', text: tr.textContent.trim().slice(0, 40), tdCount: tr.children.length });
      continue;
    }
    const cells = [];
    for (const td of tr.children) {
      const inp = td.querySelector('input');
      cells.push({
        cls: td.className,
        rowspan: td.getAttribute('rowspan') || '',
        val: inp ? inp.value : td.textContent.trim().slice(0, 12)
      });
    }
    // pick out the 3 cutting input fields by data-cfield
    const cfields = {};
    tr.querySelectorAll('input[data-cfield]').forEach(i => { cfields[i.getAttribute('data-cfield')] = i.value; });
    out.push({ kind: 'data', tdCount: tr.children.length, cfields, cells });
  }
  return { rowCount: out.length, rows: out };
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1700, height: 1000 } });
  const page = await ctx.newPage();

  const logs = [];
  page.on('console', m => logs.push({ t: 'console', type: m.type(), text: m.text() }));
  page.on('pageerror', e => logs.push({ t: 'pageerror', text: String(e && e.stack || e) }));
  const net = [];
  page.on('request', r => { if (r.url().includes('/api/ie/')) net.push({ t: 'req', method: r.method(), url: r.url() }); });
  page.on('response', r => { if (r.url().includes('/api/ie/')) net.push({ t: 'res', status: r.status(), url: r.url() }); });

  await ctx.request.post(BASE + '/api/login', { data: { username: 'jim', password: 'admin123' } });

  const report = { steps: [] };
  const snap = async (label) => {
    await page.waitForTimeout(600);
    const probe = await page.evaluate(rowProbe);
    await page.screenshot({ path: path.join(OUT, label + '.png'), fullPage: true });
    report.steps.push({ label, probe });
    return probe;
  };

  // load detail page (cutting is default segment)
  await page.goto(BASE + `/ie/${HID}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1200);

  const STAGE = 1;
  // get pids from the API (module-scoped DATA/STAGE are not on window)
  const cellR = await ctx.request.get(BASE + `/api/ie/cell/${HID}?segment=cutting&eolr=120&stage_id=${STAGE}`);
  const cell = await cellR.json();
  const czone = (cell.zones || []).find(z => z.zone === ZONE) || { rows: [] };
  const bySeq = {}; czone.rows.forEach(r => { bySeq[r.seq] = r.id; });
  report.pids = czone.rows.map(r => ({ id: r.id, seq: r.seq, name: r.process_name }));
  report.stage = STAGE;

  const saveGroup = async (pids, hc) => {
    const r = await ctx.request.post(BASE + '/api/ie/cell/save_group', {
      data: { header_id: HID, segment: 'cutting', zone: ZONE, stage_id: STAGE, process_ids: pids, headcount: hc, note: '' } });
    return { status: r.status(), body: await r.json().catch(() => null) };
  };
  const reload = () => page.evaluate(() => loadSegment('cutting'));  // real re-render (合併瞬間)

  await snap('01_before_merge');

  // ── Merge CONTIGUOUS: seq 1,2,3 ──
  report.contiguousMerge = await saveGroup([bySeq[1], bySeq[2], bySeq[3]], 9);
  await reload();
  await snap('02_after_contiguous_merge');

  // unmerge to reset
  const cell2 = await (await ctx.request.get(BASE + `/api/ie/cell/${HID}?segment=cutting&eolr=120&stage_id=${STAGE}`)).json();
  const gz = (cell2.zones || []).find(z => z.zone === ZONE) || { rows: [] };
  const grp = gz.rows.find(r => r.group_info);
  if (grp) {
    await ctx.request.post(BASE + '/api/ie/cell/delete_group', { data: { group_id: grp.group_info.group_id } });
    await reload();
  }
  await snap('03_after_unmerge_reset');

  // ── Merge NON-CONTIGUOUS: seq 1 and 3 (skip 2) ──
  report.nonContiguousMerge = await saveGroup([bySeq[1], bySeq[3]], 7);
  await reload();
  await snap('04_after_noncontiguous_merge');

  report.logs = logs;
  report.net = net;
  fs.writeFileSync(path.join(OUT, 'diag_data.json'), JSON.stringify(report, null, 2));
  await browser.close();
  console.log('TASKB DIAG DONE — rows before/after captured');
}
main().catch(e => { console.error('FATAL', e); process.exit(1); });
