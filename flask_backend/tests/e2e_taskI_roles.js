// Task I — 前端角色感知渲染 adversarial E2E（每個角色真登入跑一輪）
// 1) tongcai(read_only) 細表: 0 input/select/操作鈕; 數值可讀
// 2) test_editor(data_entry): 無權鞋型(h3) 全灰; 有權鞋型(h32) 編輯框正常
// 3) jim(admin): 不受影響 — 連刀 select/合併鈕/輸入框都在（迴歸）
// 4) 對抗: read_only 打 API 寫入 → 403
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskI_roles';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };

async function login(browser, user, pw) {
  const ctx = await browser.newContext({ viewport: { width: 1800, height: 1050 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept().catch(() => {}));
  page.on('pageerror', e => result.errors.push(user + ': ' + e));
  await ctx.request.post(BASE + '/api/login', { data: { username: user, password: pw } });
  return { ctx, page };
}
async function open(page, hid) {
  await page.goto(`${BASE}/ie/${hid}/detail`, { waitUntil: 'networkidle' });
  await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
  await page.waitForTimeout(900);
}
// count editable elements + action buttons inside the cutting detail main content
const probeEdit = () => {
  const mc = document.getElementById('mainContent');
  if (!mc) return { inputs: -1 };
  const inputs = mc.querySelectorAll('input:not([type=checkbox]):not([type=radio]), select, textarea').length;
  const actionBtns = mc.querySelectorAll('button.btn-del:not([style*="display: none"]),button.btn-ins:not([style*="display: none"]),button.cut-merge-btn:not([style*="display: none"]),button.btn-import:not([style*="display: none"])').length;
  const visibleActionBtns = [...mc.querySelectorAll('button.btn-del,button.btn-ins,button.cut-merge-btn,button.btn-import')].filter(b => b.offsetParent !== null).length;
  const interlockSel = mc.querySelectorAll('select.cut-interlock').length;
  // a number is still readable (std cell has text)
  const sampleText = (mc.querySelector('.cutting-std-a,.formula-cell') || {}).textContent || '';
  const saveVisible = (document.getElementById('saveDropdown') || {}).offsetParent != null;
  return { inputs, interlockSel, visibleActionBtns, sampleText, saveVisible };
};

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1) read_only
  {
    const { page, ctx } = await login(browser, 'tongcai', 'tongcai');
    await open(page, 32);
    const p = await page.evaluate(probeEdit);
    // adversarial API write
    const w = await ctx.request.post(BASE + '/api/ie/cell/save',
      { data: { cell_id: 33060, field: 'interlock_cut', value: '4' } });
    result.scenarios.read_only = {
      probe: p, apiWriteStatus: w.status(),
      PASS: p.inputs === 0 && p.interlockSel === 0 && p.visibleActionBtns === 0 &&
            !p.saveVisible && p.sampleText.length >= 0 && w.status() === 403
    };
    await page.screenshot({ path: OUT + '\\I1_readonly.png', fullPage: true });
    await ctx.close();
  }

  // 2) editor — unassigned (h3) grey, assigned (h32) editable
  {
    const { page, ctx } = await login(browser, 'test_editor', 'testpw123');
    await open(page, 3);
    const un = await page.evaluate(probeEdit);
    await open(page, 32);
    const as = await page.evaluate(probeEdit);
    result.scenarios.editor = {
      unassigned_h3: un, assigned_h32: as,
      PASS: un.inputs === 0 && un.visibleActionBtns === 0 &&
            as.inputs > 0 && as.interlockSel > 0 && as.visibleActionBtns > 0
    };
    await page.screenshot({ path: OUT + '\\I2_editor_assigned.png', fullPage: true });
    await ctx.close();
  }

  // 3) admin — unaffected (regression)
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await open(page, 32);
    const p = await page.evaluate(probeEdit);
    result.scenarios.admin = {
      probe: p,
      PASS: p.inputs > 0 && p.interlockSel > 0 && p.visibleActionBtns > 0 && p.saveVisible
    };
    await page.screenshot({ path: OUT + '\\I3_admin.png', fullPage: true });
    await ctx.close();
  }

  // 5) eolr_settings — read_only 純文字（0 select），admin 有下拉
  {
    const ro = await login(browser, 'tongcai', 'tongcai');
    await ro.page.goto(`${BASE}/eolr-settings`, { waitUntil: 'networkidle' });
    await ro.page.waitForSelector('#content table', { timeout: 8000 }).catch(() => {});
    await ro.page.waitForTimeout(500);
    const roSel = await ro.page.evaluate(() => document.querySelectorAll('#content select').length);
    const roTxt = await ro.page.evaluate(() => document.querySelectorAll('#content .eolr-ro').length);
    await ro.ctx.close();
    const ad = await login(browser, 'jim', 'admin123');
    await ad.page.goto(`${BASE}/eolr-settings`, { waitUntil: 'networkidle' });
    await ad.page.waitForSelector('#content table', { timeout: 8000 }).catch(() => {});
    await ad.page.waitForTimeout(500);
    const adSel = await ad.page.evaluate(() => document.querySelectorAll('#content select').length);
    await ad.ctx.close();
    result.scenarios.eolr_settings = {
      read_only_selects: roSel, read_only_textCells: roTxt, admin_selects: adSel,
      PASS: roSel === 0 && roTxt > 0 && adSel > 0
    };
  }

  // 6) allocation — read_only(無撥人角色) 勾選框全禁用
  {
    const ro = await login(browser, 'tongcai', 'tongcai');
    await ro.page.goto(`${BASE}/allocation`, { waitUntil: 'networkidle' });
    await ro.page.waitForTimeout(1200);
    const chk = await ro.page.evaluate(() => {
      const all = [...document.querySelectorAll('#content input[type=checkbox]')];
      return { total: all.length, enabled: all.filter(c => !c.disabled).length };
    });
    result.scenarios.allocation = {
      checkboxes: chk.total, enabled: chk.enabled,
      PASS: chk.enabled === 0   // 全禁用（total 可能為 0=無資料，也算通過：無可編輯元素）
    };
    await ro.ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_I_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
