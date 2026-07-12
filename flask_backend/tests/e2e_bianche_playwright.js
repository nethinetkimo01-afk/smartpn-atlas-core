// Task A — 編制表 E2E via Playwright (Chromium).
// Phases: phaseA (Step1 /ds04 original + Steps 4-7 read-only screenshots),
//         phaseB (Step2 after-reimport + Step3 lock).
// Usage: node e2e_run.js <phase>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = 'http://localhost:5057';
const SHOTS = 'C:\\smartpn-atlas-core\\test_screenshots\\bianche_e2e';
const RESULTS = path.join(SHOTS, 'e2e_results.json');
const MONTH = '2026-06';

function loadResults() { try { return JSON.parse(fs.readFileSync(RESULTS, 'utf8')); } catch { return {}; } }
function saveResults(r) { fs.writeFileSync(RESULTS, JSON.stringify(r, null, 2)); }

async function main() {
  const phase = process.argv[2] || 'phaseA';
  const results = loadResults();
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await ctx.newPage();

  // login (cookie shared with ctx.request) — sys_users session
  const lr = await ctx.request.post(BASE + '/api/login', { data: { username: 'jim', password: 'admin123' } });
  // allocation uses a SEPARATE identity (session.alloc_user); log in there too
  const ar = await ctx.request.post(BASE + '/api/allocation/login', { data: { username: 'jim' } });
  results._login = { status: lr.status(), body: await lr.json().catch(() => null),
    allocStatus: ar.status(), allocBody: await ar.json().catch(() => null) };

  const rec = (k, v) => { results[k] = Object.assign({}, results[k], v, { ts: new Date().toISOString() }); saveResults(results); };
  const shot = async (name) => { const p = path.join(SHOTS, name); await page.screenshot({ path: p, fullPage: true }); return p; };
  const getJSON = async (url) => { const r = await ctx.request.get(BASE + url); return { status: r.status(), body: await r.json().catch(() => null) }; };

  async function step(id, fn) {
    try { await fn(); }
    catch (e) { rec(id, { ok: false, error: String(e && e.stack || e) }); console.log(id, 'FAIL', e && e.message); }
  }

  if (phase === 'phaseA') {
    // ── Step 1: /ds04 upload/parse result (original import) ──
    await step('step1_ds04', async () => {
      const orders = await getJSON(`/api/ds04/orders?month=${MONTH}`);
      const filters = await getJSON(`/api/ds04/filters`);
      await page.goto(BASE + '/ds04', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
      const shotp = await shot('step1_ds04.png');
      const rows = (orders.body && (orders.body.rows || orders.body.orders)) || [];
      rec('step1_ds04', { ok: orders.status === 200, ordersStatus: orders.status,
        orderCount: Array.isArray(rows) ? rows.length : null,
        filters: filters.body, shot: shotp });
    });

    // ── Step 4: /eolr-settings ──
    await step('step4_eolr', async () => {
      const before = await getJSON(`/api/eolr-settings?month=${MONTH}`);
      await page.goto(BASE + '/eolr-settings', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1200);
      const shotp = await shot('step4_eolr.png');
      // modify one LEAN eolr to 60, then read back
      const setr = await ctx.request.post(BASE + '/api/eolr-settings',
        { data: { lean: '1A', month: MONTH, eolr: 60 } });
      const after = await getJSON(`/api/eolr-settings?month=${MONTH}`);
      rec('step4_eolr', { ok: before.status === 200, before: before.body,
        setStatus: setr.status(), after: after.body, shot: shotp });
    });

    // ── Step 5: /allocation checkboxes ──
    await step('step5_alloc', async () => {
      const pre = await ctx.request.post(BASE + '/api/allocation/prefill', { data: { month: MONTH } });
      const preBody = await pre.json().catch(() => null);
      const items = await getJSON(`/api/allocation/items?month=${MONTH}`);
      await page.goto(BASE + '/allocation', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
      const shotp = await shot('step5_allocation.png');
      rec('step5_alloc', { ok: pre.status() === 200, prefillStatus: pre.status(),
        prefill: preBody, itemsStatus: items.status,
        itemCount: items.body && (items.body.items ? items.body.items.length : null), shot: shotp });
    });

    // ── Step 6: /bianche computation ──
    await step('step6_bianche', async () => {
      const bianche = await getJSON(`/api/bianche?month=${MONTH}`);
      const bianzhi = await getJSON(`/api/bianzhi/detail?month=${MONTH}`);
      await page.goto(BASE + '/bianche', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
      const shotp = await shot('step6_bianche.png');
      // 決策③ evidence: with no IE locked version every model should still be
      // listed (no block) but flagged has_locked=false / MP null (red).
      let dRows = [];
      const bb = bianzhi.body;
      if (bb) dRows = bb.rows || bb.models || bb.detail || bb.data || (Array.isArray(bb) ? bb : []);
      const flat = Array.isArray(dRows) ? dRows : [];
      const noLock = flat.filter(r => r && (r.has_locked === false || r.has_locked === 0)).length;
      const withLock = flat.filter(r => r && (r.has_locked === true || r.has_locked === 1)).length;
      rec('step6_bianche', { ok: bianche.status === 200 && bianzhi.status === 200,
        biancheStatus: bianche.status, bianzhiStatus: bianzhi.status,
        detailRowCount: flat.length, noLockedCount: noLock, withLockedCount: withLock,
        note: 'no IE locked data locally -> expect all has_locked=false (紅底不擋單=決策③); MP hand-check BLOCKED',
        bianzhiSample: JSON.stringify(bb).slice(0, 1500), shot: shotp });
    });

    // ── Step 7: export ──
    await step('step7_export', async () => {
      const r = await ctx.request.get(BASE + `/api/bianche/export?month=${MONTH}`);
      const buf = await r.body();
      const outp = path.join(SHOTS, 'step7_bianche_export.xlsx');
      fs.writeFileSync(outp, buf);
      rec('step7_export', { ok: r.status() === 200, status: r.status(),
        bytes: buf.length, file: outp,
        contentType: r.headers()['content-type'] });
    });
  }

  if (phase === 'phaseB') {
    // ── Step 2: after reimport (modified qty) ──
    await step('step2_reimport', async () => {
      const orders = await getJSON(`/api/ds04/orders?month=${MONTH}`);
      await page.goto(BASE + '/ds04', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
      const shotp = await shot('step2_ds04_after.png');
      const rows = (orders.body && (orders.body.rows || orders.body.orders)) || [];
      rec('step2_reimport', { ok: orders.status === 200,
        orderCountAfter: Array.isArray(rows) ? rows.length : null, shot: shotp });
    });

    // ── Step 3: lock then verify edit blocked ──
    await step('step3_lock', async () => {
      const lock = await ctx.request.post(BASE + '/api/ds04/lock', { data: { action: 'lock', month: MONTH } });
      const lockBody = await lock.json().catch(() => null);
      // try to edit an order while locked -> expect blocked
      const ordersR = await getJSON(`/api/ds04/orders?month=${MONTH}`);
      const rows = (ordersR.body && (ordersR.body.rows || ordersR.body.orders)) || [];
      let editAttempt = null;
      if (rows.length) {
        const oid = rows[0].id;
        const put = await ctx.request.put(BASE + `/api/ds04/order/${oid}`,
          { data: { qty: 99999, month: MONTH } });
        editAttempt = { status: put.status(), body: await put.json().catch(() => null) };
      }
      await page.goto(BASE + '/ds04', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1200);
      const shotp = await shot('step3_lock.png');
      const lockStatus = await getJSON(`/api/ds04/lock?month=${MONTH}`);
      rec('step3_lock', { ok: lock.status() === 200, lockResp: lockBody,
        editBlockedResp: editAttempt, lockStatus: lockStatus.body, shot: shotp });
      // unlock to leave DB clean for any re-runs
      await ctx.request.post(BASE + '/api/ds04/lock', { data: { action: 'unlock', month: MONTH } });
    });
  }

  await browser.close();
  console.log('PHASE', phase, 'DONE');
}
main().catch(e => { console.error('FATAL', e); process.exit(1); });
