// Task R — SmartPN Demo v3 acceptance (v1 全功能 + 議會定案 + Boss + 引導腳本)
// v2 acceptance + 功能迴歸(V1_PARITY 全存在) + 引導5步 + Boss(無錯/無毛利率) + 3違規=0 + MOCK_WORLD一致
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:8099';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskR_demo_v3';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
fs.mkdirSync(OUT, { recursive: true });
const result = { brand: {}, supplier: {}, boss: {}, errors: [] };

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
  const page = await ctx.newPage();
  const perr = []; page.on('pageerror', e => perr.push(String(e)));

  // ── Brand v3 ──
  await page.goto(`${BASE}/SMARTPN_DEMO_V3.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);
  result.brand = await page.evaluate(() => {
    const o = {};
    o.v1_total = window.V1_PARITY.length;
    o.v1_missing = window.V1_PARITY.filter(fn => typeof window[fn] !== 'function');
    o.hooks = ['MOCK_WORLD','setAccount','getVisibleMaterials','setLang'].every(h=>typeof window[h]!=='undefined');
    window.setAccount('A'); o.A = window.getVisibleMaterials().length;
    window.setAccount('B'); o.B = window.getVisibleMaterials().length;
    o.privateNotInB = !window.getVisibleMaterials().some(m=>m.id==='SPA-FV-1003'); window.setAccount('A');
    // guided 5 steps → end
    startGuide(); const step1 = !!document.getElementById('guideOv');
    for (let i=0;i<5;i++) nextGuide();
    o.guided = { step1, endedAfter5: !document.getElementById('guideOv') };
    const b=document.body.innerText; o.viol={verified:/SmartPN Verified/.test(b),margin:/毛利率/.test(b),who:/誰看過/.test(b)};
    showPage('search'); applyFilters(); o.grid = document.querySelectorAll('.mat-card').length;
    return o;
  });
  await page.screenshot({ path: OUT + '\\R1_brand_v3_search_acct.png', fullPage: true });
  await page.evaluate(() => { openSpu(MATERIALS[0].id); });
  await page.screenshot({ path: OUT + '\\R2_brand_v3_spu_fields.png', fullPage: true });
  await page.evaluate(() => startGuide());
  await page.screenshot({ path: OUT + '\\R3_brand_v3_guided.png', fullPage: true });

  // ── Supplier v3 ──
  await page.goto(`${BASE}/SMARTPN_DEMO_SUPPLIER_V3.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);
  result.supplier = await page.evaluate(() => {
    const o = {};
    o.v1_total = window.V1_PARITY.length;
    o.v1_missing = window.V1_PARITY.filter(fn => typeof window[fn] !== 'function');
    o.mw_total = MOCK_WORLD.materials.length;
    o.sample3 = ['SPA-FV-1000','SPA-AP-1010','SPA-SS-1020'].map(id=>MOCK_WORLD.materials.find(m=>m.id===id).name);
    window.setAccount('A'); o.A = window.getVisibleMaterials().length; window.setAccount('B'); o.B = window.getVisibleMaterials().length;
    o.permTriState = typeof renderPermFields==='function' && typeof setPF==='function';
    const b=document.body.innerText; o.viol={verified:/SmartPN Verified/.test(b),margin:/毛利率/.test(b),who:/誰看過/.test(b)};
    return o;
  });
  await page.evaluate(() => { const n=[...document.querySelectorAll('.nav-sub')].find(b=>/欄位權限/.test(b.textContent)); n&&n.click(); });
  await page.screenshot({ path: OUT + '\\R4_supplier_v3_permtristate.png', fullPage: true });
  await page.evaluate(() => { const n=[...document.querySelectorAll('.nav-sub')].find(b=>/Mapping/.test(b.textContent)); n&&n.click(); });
  await page.screenshot({ path: OUT + '\\R5_supplier_v3_mapping.png', fullPage: true });

  // ── Boss view ──
  await page.goto(`${BASE}/SMARTPN_DEMO_SUPPLIER_V3.html#boss`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(900);
  result.boss = await page.evaluate(() => ({
    banner: !!document.getElementById('bossBanner'),
    biVisible: getComputedStyle(document.getElementById('view-bi')).display!=='none',
    noMargin: !/毛利率/.test(document.getElementById('view-bi').innerText),
    kpis: /營業額|Revenue/.test(document.getElementById('view-bi').innerText),
    readonly: [...document.querySelectorAll('.nav-item,.nav-sub')].some(x=>x.style.opacity==='0.4'),
  }));
  await page.screenshot({ path: OUT + '\\R6_boss_view.png', fullPage: true });

  result.errors = perr;
  result.consistency = { same_total: result.brand.hooks && result.supplier.mw_total===24 };
  result.ALL_PASS = perr.length===0 &&
    result.brand.v1_missing.length===0 && result.supplier.v1_missing.length===0 &&
    result.brand.A===5 && result.brand.B===3 && result.brand.privateNotInB &&
    result.supplier.A===5 && result.supplier.B===3 && result.supplier.permTriState &&
    result.brand.guided.endedAfter5 &&
    !result.brand.viol.verified && !result.brand.viol.margin && !result.brand.viol.who &&
    !result.supplier.viol.verified && !result.supplier.viol.margin && !result.supplier.viol.who &&
    result.boss.banner && result.boss.noMargin && result.boss.kpis && result.boss.readonly &&
    result.supplier.mw_total===24;

  fs.writeFileSync(OUT + '\\task_R_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
