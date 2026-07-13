// Task J — STF 段所有區塊「實際人數」→「EOLR=190 實際人數」(三語)
// 逐一列出 STF 每個區塊表頭結果；三語切換；其他段未波及；填值迴歸；read_only 同步
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskJ_stf';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
const HID = 32;
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };

async function login(browser, u, pw) {
  const ctx = await browser.newContext({ viewport: { width: 1800, height: 1050 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept().catch(() => {}));
  page.on('pageerror', e => result.errors.push(u + ': ' + e));
  await ctx.request.post(BASE + '/api/login', { data: { username: u, password: pw } });
  return { ctx, page };
}
async function openSeg(page, hid, seg) {
  await page.goto(`${BASE}/ie/${hid}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(500);
  await page.evaluate(s => loadSegment(s), seg);
  await page.waitForTimeout(1400);
}
// map every zone card in current view → its actual-operators (th.th-actual) text
// NOTE: inline the arrow into page.evaluate (named-const refs don't serialize reliably)
async function grab(page) {
  // NOTE: renderZoneCard 的 <table> 是 .zone-card 的「兄弟」而非子節點，
  // 故用 index 對齊 zone-name 與 th.th-actual（渲染順序一致：card,table,card,table…）
  return page.evaluate(() => {
    const names = [...document.querySelectorAll('.zone-card .zone-name')].map(e => e.textContent.trim());
    const ths = [...document.querySelectorAll('#mainContent th.th-actual')].map(e => e.textContent.trim());
    return ths.map((h, i) => ({ zone: names[i] || '?', actualHeader: h }));
  });
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1) STF headers renamed (all zones) + 3-lang switch
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openSeg(page, HID, 'stf');
    const zh = await grab(page);
    await page.evaluate(() => setLang('vi'));
    await page.waitForTimeout(300);
    const vi = await grab(page);
    await page.evaluate(() => setLang('zh'));
    await page.waitForTimeout(300);
    const back = await grab(page);
    const allZH = zh.every(z => z.actualHeader === 'EOLR=190 實際人數');
    const allVI = vi.every(z => z.actualHeader === 'EOLR=190 Số người thực tế');
    const allBack = back.every(z => z.actualHeader === 'EOLR=190 實際人數');
    result.scenarios.stf_headers = {
      zones_checked: zh.map(z => z.zone), count: zh.length,
      zh_headers: zh, vi_sample: vi[0], back_ok: allBack,
      PASS: zh.length >= 4 && allZH && allVI && allBack
    };
    await page.screenshot({ path: OUT + '\\J1_stf_headers.png', fullPage: true });
    await ctx.close();
  }

  // 2) other segments NOT affected (cutting/stitching/assembly actual header unchanged)
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openSeg(page, HID, 'stitching');
    const stitch = await grab(page);
    await openSeg(page, HID, 'assembly');
    const asm = await grab(page);
    // cutting uses its own header; check no "EOLR=190" leaked into cutting/stitching/assembly
    await page.evaluate(() => loadSegment('cutting'));
    await page.waitForTimeout(700);
    const cuttingHasEolr190 = await page.evaluate(() =>
      /EOLR=190/.test(document.getElementById('mainContent').textContent));
    const otherHasEolr190 = stitch.concat(asm).some(z => /EOLR=190/.test(z.actualHeader));
    result.scenarios.other_segments = {
      stitching: stitch.map(z => z.actualHeader), assembly: asm.map(z => z.actualHeader),
      cutting_has_eolr190: cuttingHasEolr190, other_has_eolr190: otherHasEolr190,
      PASS: !cuttingHasEolr190 && !otherHasEolr190
    };
    await ctx.close();
  }

  // 3) fill + merge regression on an STF zone with data
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await openSeg(page, HID, 'stf');
    // find an STF zone tbody with an actual input, fill it
    const filled = await page.evaluate(() => {
      const inp = document.querySelector('.zone-card table tbody input[class*="act"], .zone-card table tbody input.cut-act-inp, .zone-card table tbody .actual-cell input');
      if (!inp) return { found: false };
      inp.value = '3'; inp.dispatchEvent(new Event('blur'));
      return { found: true };
    });
    await page.waitForTimeout(1000);
    // header still renamed after interaction
    const stillRenamed = await page.evaluate(() => {
      const ths = [...document.querySelectorAll('#mainContent th.th-actual')];
      return ths.length > 0 && ths.every(t => t.textContent.trim() === 'EOLR=190 實際人數');
    });
    // merge button exists on STF? (generic actual cell may have merge)
    const hasMerge = await page.evaluate(() => !!document.querySelector('.zone-card .cut-merge-btn, .zone-card .merge-btn'));
    result.scenarios.fill_regression = {
      fillFound: filled.found, headerStillRenamed: stillRenamed, hasMergeBtn: hasMerge,
      PASS: stillRenamed === true
    };
    await ctx.close();
  }

  // 4) read_only view — STF header renamed too
  {
    const { page, ctx } = await login(browser, 'tongcai', 'tongcai');
    // lock stage so read_only sees table
    await openSeg(page, HID, 'stf');
    const ro = await grab(page);
    const inputs = await page.evaluate(() => document.querySelectorAll('#mainContent input,#mainContent select').length);
    result.scenarios.read_only = {
      zones: ro.map(z => z.zone), headers: ro.map(z => z.actualHeader), inputs,
      PASS: ro.length >= 1 && ro.every(z => z.actualHeader === 'EOLR=190 實際人數') && inputs === 0
    };
    await page.screenshot({ path: OUT + '\\J4_readonly.png', fullPage: true });
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_J_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
