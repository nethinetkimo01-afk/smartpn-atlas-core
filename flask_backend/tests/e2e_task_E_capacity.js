// Task E — Playwright: login, GET the IE capacity export, save it.
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://localhost:5057';
const OUT = 'C:\\smartpn-atlas-core\\flask_backend\\test_output\\ie_capacity_export.xlsx';

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  await ctx.request.post(BASE + '/api/login', { data: { username: 'jim', password: 'admin123' } });
  const r = await ctx.request.get(BASE + '/api/ie/export/capacity');
  const buf = await r.body();
  fs.writeFileSync(OUT, buf);
  console.log(JSON.stringify({ status: r.status(), bytes: buf.length, contentType: r.headers()['content-type'], saved: OUT }));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
