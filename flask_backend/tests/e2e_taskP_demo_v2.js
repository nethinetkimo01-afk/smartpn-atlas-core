// Task P — SmartPN Demo v2 acceptance (議會定案版)
// 兩檔載入無錯; MOCK_WORLD 兩視角一致; 8 項需求; 3 違規=0; 帳號A/B 5/3; 私密不在B; mapping鎖; EN/ZH
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:8099';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskP_demo_v2';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
fs.mkdirSync(OUT, { recursive: true });
const result = { brand: {}, supplier: {}, errors: [] };

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
  const page = await ctx.newPage();
  const perr = [];
  page.on('pageerror', e => perr.push(String(e)));

  // ── Brand v2 ──
  await page.goto(`${BASE}/SMARTPN_DEMO_V2.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  result.brand = await page.evaluate(() => {
    const o = {};
    o.hooks = ['MOCK_WORLD','setAccount','getVisibleMaterials','setLang'].every(h => typeof window[h] !== 'undefined');
    o.total = MOCK_WORLD.materials.length;
    window.setAccount('A'); o.A = window.getVisibleMaterials().map(m=>m.id);
    window.setAccount('B'); o.B = window.getVisibleMaterials().map(m=>m.id);
    o.privateNotInB = !o.B.includes('SPA-FV-1003');
    window.setAccount('A');
    return o;
  });
  await page.screenshot({ path: OUT + '\\P1_brand_search.png', fullPage: true });
  await page.evaluate(() => openMat('SPA-FV-1000'));
  await page.evaluate(() => { const b=document.querySelector('#page-detail .src-btn'); b&&b.click(); });
  await page.waitForTimeout(200);
  await page.screenshot({ path: OUT + '\\P2_brand_detail_source_quote_history.png', fullPage: true });
  await page.evaluate(() => nav('account'));
  await page.screenshot({ path: OUT + '\\P3_brand_account_seats.png', fullPage: true });
  const brandBody = await page.evaluate(() => document.body.innerText);
  result.brand.violations = {
    smartpnVerified: /SmartPN Verified/.test(brandBody),
    grossMargin: /毛利率/.test(brandBody),
    whoViewed: /誰看過/.test(brandBody),
  };

  // ── Supplier v2 ──
  await page.goto(`${BASE}/SMARTPN_DEMO_SUPPLIER_V2.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  result.supplier = await page.evaluate(() => {
    const o = {};
    o.hooks = ['MOCK_WORLD','setAccount','getVisibleMaterials','setLang'].every(h => typeof window[h] !== 'undefined');
    o.total = MOCK_WORLD.materials.length;
    o.sample3 = ['SPA-FV-1000','SPA-AP-1010','SPA-SS-1020'].map(id=>MOCK_WORLD.materials.find(m=>m.id===id).name);
    window.setAccount('A'); o.A = window.getVisibleMaterials().length;
    window.setAccount('B'); o.B = window.getVisibleMaterials().length;
    return o;
  });
  await page.screenshot({ path: OUT + '\\P4_supplier_materials_permission.png', fullPage: true });
  await page.evaluate(() => nav('mapping'));
  await page.screenshot({ path: OUT + '\\P5_supplier_mapping_signoff.png', fullPage: true });
  await page.evaluate(() => { nav('evidence'); toggleEvi(); });
  await page.waitForTimeout(150);
  await page.screenshot({ path: OUT + '\\P6_supplier_evidence.png', fullPage: true });
  await page.evaluate(() => nav('contacts'));
  await page.screenshot({ path: OUT + '\\P7_supplier_contacts.png', fullPage: true });
  await page.evaluate(() => nav('bi'));
  await page.screenshot({ path: OUT + '\\P8_supplier_bi_no_margin.png', fullPage: true });
  const supBody = await page.evaluate(() => document.body.innerText);
  result.supplier.violations = {
    smartpnVerified: /SmartPN Verified/.test(supBody),
    grossMargin: /毛利率/.test(supBody),
    whoViewed: /誰看過/.test(supBody),
  };

  result.errors = perr;
  result.consistency = {
    same_total: result.brand.total === result.supplier.total,
    same_AB: result.brand.A.length === result.supplier.A && result.brand.B.length === result.supplier.B,
  };
  result.ALL_PASS = perr.length === 0 && result.brand.hooks && result.supplier.hooks &&
    result.brand.A.length === 5 && result.brand.B.length === 3 && result.brand.privateNotInB &&
    result.supplier.A === 5 && result.supplier.B === 3 &&
    !result.brand.violations.smartpnVerified && !result.brand.violations.grossMargin && !result.brand.violations.whoViewed &&
    !result.supplier.violations.smartpnVerified && !result.supplier.violations.grossMargin && !result.supplier.violations.whoViewed &&
    result.consistency.same_total && result.consistency.same_AB;

  fs.writeFileSync(OUT + '\\task_P_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
