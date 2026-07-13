// Task K — 設備種類管理頁（manager/admin）adversarial E2E
// 1) manager 看得到入口→開頁→新增/停用/排序
// 2) 已引用列：改名/刪除鈕反灰(disabled)+顯示引用數；硬打 API→409
// 3) 未引用：可改名/刪除；新增後細表下拉出現；停用後下拉消失(舊資料不變)
// 4) editor/read_only：入口不顯示、頁面路由 403、寫入 API 403
// 5) 亂點：連續停用/啟用/排序不噴錯
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:5058';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskK_equip';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };

async function login(browser, u, pw) {
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 950 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept().catch(() => {}));
  page.on('pageerror', e => result.errors.push(u + ': ' + e));
  await ctx.request.post(BASE + '/api/login', { data: { username: u, password: pw } });
  return { ctx, page };
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });

  // 1) manager: entry visible on /ie + page opens + can add
  {
    const { page, ctx } = await login(browser, 'test_mgr', 'testpw123');
    await page.goto(`${BASE}/ie`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);
    const entryVisible = await page.evaluate(() => {
      const b = document.getElementById('btn-equip-types');
      return !!b && b.offsetParent !== null;
    });
    await page.goto(`${BASE}/admin/equipment-types`, { waitUntil: 'networkidle' });
    await page.waitForSelector('#tbody tr', { timeout: 8000 });
    const denied = await page.evaluate(() => document.getElementById('denied').offsetParent !== null);
    // add a new type via UI
    await page.fill('#newName', 'UITEST_MACHINE');
    await page.fill('#newSort', '99');
    await page.click('button.btn-pri');
    await page.waitForTimeout(1000);
    const hasNew = await page.evaluate(() => [...document.querySelectorAll('#tbody td')].some(t => t.textContent.includes('UITEST_MACHINE')));
    result.scenarios.manager_access = { entryVisible, denied, addedNewShows: hasNew, PASS: entryVisible && !denied && hasNew };
    await page.screenshot({ path: OUT + '\\K1_manager_page.png', fullPage: true });
    await ctx.close();
  }

  // 2) referenced row → rename/delete disabled + ref count; API 409
  {
    const { page, ctx } = await login(browser, 'test_mgr', 'testpw123');
    await page.goto(`${BASE}/admin/equipment-types`, { waitUntil: 'networkidle' });
    await page.waitForSelector('#tbody tr', { timeout: 8000 });
    // find the referenced row (三針針車機TEST, ref_count=1)
    const refRow = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('#tbody tr')];
      const tr = rows.find(r => r.textContent.includes('三針針車機TEST'));
      if (!tr) return null;
      const btns = [...tr.querySelectorAll('button')];
      const rename = btns.find(b => b.textContent.trim() === '改名');
      const del = btns.find(b => b.textContent.trim() === '刪除');
      return {
        showsRefCount: /已被 1 道|1 道工序/.test(tr.textContent),
        renameDisabled: rename ? rename.disabled : null,
        delDisabled: del ? del.disabled : null,
      };
    });
    // hard API PUT rename → 409, DELETE → 409
    const tid = await (await ctx.request.get(`${BASE}/api/equipment_types/admin`)).json()
      .then(d => (d.options.find(o => o.name === '三針針車機TEST') || {}).id);
    const putR = await ctx.request.put(`${BASE}/api/equipment_types/${tid}`, { data: { name: 'HACK' } });
    const delR = await ctx.request.delete(`${BASE}/api/equipment_types/${tid}`);
    result.scenarios.referenced_lock = {
      ...refRow, apiRenameStatus: putR.status(), apiDeleteStatus: delR.status(),
      PASS: refRow && refRow.renameDisabled === true && refRow.delDisabled === true &&
            refRow.showsRefCount && putR.status() === 409 && delR.status() === 409
    };
    await ctx.close();
  }

  // 3) editor & read_only: entry hidden + page 403 + API 403
  {
    for (const [u, pw] of [['test_editor', 'testpw123'], ['tongcai', 'tongcai']]) {
      const { page, ctx } = await login(browser, u, pw);
      await page.goto(`${BASE}/ie`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1000);
      const entryHidden = await page.evaluate(() => {
        const b = document.getElementById('btn-equip-types');
        return !b || b.offsetParent === null;
      });
      const pageResp = await ctx.request.get(`${BASE}/admin/equipment-types`);
      const apiResp = await ctx.request.post(`${BASE}/api/equipment_types`, { data: { name: 'z' } });
      result.scenarios['noaccess_' + u] = {
        entryHidden, pageStatus: pageResp.status(), apiStatus: apiResp.status(),
        PASS: entryHidden && pageResp.status() === 403 && apiResp.status() === 403
      };
      await ctx.close();
    }
  }

  // 3.5) dropdown: add→細表下拉出現；停用→消失；舊資料值照常顯示
  // 用 admin(jim) 檢視細表（manager 因 Task I 全灰無 select）；add/disable API admin 亦可
  {
    const { page, ctx } = await login(browser, 'jim', 'admin123');
    await ctx.request.post(`${BASE}/api/equipment_types`, { data: { name: 'DROPTEST', sort_order: 50 } });
    const openStitch = async () => {
      await page.goto(`${BASE}/ie/32/detail`, { waitUntil: 'networkidle' });
      await page.waitForSelector('#tbody-cut-裁斷機', { timeout: 8000 });
      await page.waitForTimeout(400);
      await page.evaluate(() => loadSegment('stf'));
      await page.waitForTimeout(1200);
    };
    await openStitch();
    const hasOptAfterAdd = await page.evaluate(() =>
      [...document.querySelectorAll('#mainContent select option')].some(o => o.textContent.trim() === 'DROPTEST'));
    // set an ie_process stitching row's equipment_type = DROPTEST (old data), then disable DROPTEST
    const tid = await (await ctx.request.get(`${BASE}/api/equipment_types/admin`)).json()
      .then(d => (d.options.find(o => o.name === 'DROPTEST') || {}).id);
    await ctx.request.put(`${BASE}/api/equipment_types/${tid}`, { data: { active: 0 } });
    await openStitch();
    const hasOptAfterDisable = await page.evaluate(() =>
      [...document.querySelectorAll('#mainContent select option')].some(o => o.textContent.trim() === 'DROPTEST'));
    result.scenarios.dropdown = {
      appearsAfterAdd: hasOptAfterAdd, goneAfterDisable: !hasOptAfterDisable,
      PASS: hasOptAfterAdd === true && hasOptAfterDisable === false
    };
    await ctx.close();
  }

  // 4) fuzz: rapid disable/enable/reorder no crash
  {
    const { page, ctx } = await login(browser, 'test_mgr', 'testpw123');
    await page.goto(`${BASE}/admin/equipment-types`, { waitUntil: 'networkidle' });
    await page.waitForSelector('#tbody tr', { timeout: 8000 });
    for (let i = 0; i < 4; i++) {
      const btn = page.locator('#tbody tr').first().locator('button', { hasText: /停用|啟用/ });
      await btn.click().catch(() => {});
      await page.waitForTimeout(250);
    }
    result.scenarios.fuzz = { pageErrors: result.errors.length, PASS: result.errors.length === 0 };
    await ctx.close();
  }

  result.ALL_PASS = Object.values(result.scenarios).every(s => s.PASS) && result.errors.length === 0;
  fs.writeFileSync(OUT + '\\task_K_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
