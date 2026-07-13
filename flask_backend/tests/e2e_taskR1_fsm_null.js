// Task R-1 — FSM 空脈絡例外修復
// 1) 空脈絡直接呼叫依賴脈絡的函式 → 不噴例外(安靜return)
// 2) 全頁亂點兩遍(空脈絡) → 0 pageerror
// 3) 正常 FSM 動線(開材料→FSM→比對→新視窗) 迴歸
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:8099';
const OUT = 'D:\\smartpn-atlas-core\\test_screenshots\\taskR1_fsm';
const EXE = process.env.PW_CHROME || 'C:\\Users\\user\\AppData\\Local\\ms-playwright\\chromium-1228\\chrome-win64\\chrome.exe';
fs.mkdirSync(OUT, { recursive: true });
const result = { scenarios: {}, errors: [] };

(async () => {
  const browser = await chromium.launch({ executablePath: EXE });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
  const page = await ctx.newPage();
  const perr = []; page.on('pageerror', e => perr.push(String(e)));
  page.on('dialog', d => d.accept().catch(()=>{}));
  // block popups (openFsmInNewWindow opens a window in normal flow)
  ctx.on('page', p => { if (p !== page) p.close().catch(()=>{}); });

  await page.goto(`${BASE}/SMARTPN_DEMO_V3.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(400);

  // 1) direct calls with empty context — must not throw
  result.scenarios.direct_null_calls = await page.evaluate(() => {
    const out = { thrown: [] };
    // ensure empty context
    fsmContext = null; currentMat = null; currentSku = null; activeThread = null;
    const tryFn = (name, fn) => { try { fn(); } catch(e){ out.thrown.push(name + ': ' + e.message); } };
    tryFn('openFsmInNewWindow', () => openFsmInNewWindow());
    tryFn('renderFsmBody', () => renderFsmBody());
    tryFn('selectOpt', () => selectOpt('BLK'));
    tryFn('sendMsg', () => sendMsg());
    tryFn('showFieldHistory', () => showFieldHistory('NO_SUCH_ID'));
    tryFn('renderSpuPage', () => renderSpuPage(null));
    tryFn('openThread', () => openThread('no_such_thread'));
    return { thrown: out.thrown, PASS: out.thrown.length === 0 };
  });

  // 2) fuzz — click every visible button twice, empty context, capture pageerrors
  const beforeFuzz = perr.length;
  for (let pass = 0; pass < 2; pass++) {
    const n = await page.evaluate(() => document.querySelectorAll('button').length);
    for (let i = 0; i < n; i++) {
      await page.evaluate((idx) => {
        const btns = [...document.querySelectorAll('button')];
        const b = btns[idx];
        if (b && b.offsetParent !== null) { try { b.click(); } catch(e){} }
      }, i).catch(()=>{});
    }
    // close any modals that opened, reset to home/empty context
    await page.evaluate(() => { document.getElementById('fsm-modal')&&(document.getElementById('fsm-modal').style.display='none'); document.getElementById('fieldHistModal')?.remove(); if(typeof applyFilters==='function'){fsmContext=null;} });
    await page.waitForTimeout(150);
  }
  result.scenarios.fuzz = { pageErrorsDuringFuzz: perr.length - beforeFuzz, PASS: (perr.length - beforeFuzz) === 0 };
  await page.screenshot({ path: OUT + '\\R1_fuzz.png', fullPage: true });

  // 3) normal FSM flow regression
  const flow = await page.evaluate(() => {
    const out = {};
    try {
      const m = MATERIALS[0];
      openSpu(m.id); out.spu = currentPage === 'spu';
      const sku = currentSku;
      findSameMaterial(m.id, m.spuCode, sku.key);
      out.fsmModalShown = document.getElementById('fsm-modal').style.display === 'flex';
      out.fsmBodyRendered = document.getElementById('fsm-modal-body').innerHTML.length > 0;
      out.fsmContextSet = !!fsmContext;
      // new window (guarded — with context should proceed; we don't assert window, just no throw)
      openFsmInNewWindow(); out.newWindowNoThrow = true;
      // compare
      showPage('compare'); renderCompare(); out.compareRendered = document.getElementById('compare-body').innerHTML.length > 0;
      closeFsmModal();
    } catch(e){ out.error = e.message; }
    return out;
  });
  result.scenarios.normal_flow = {
    ...flow,
    PASS: flow.spu && flow.fsmModalShown && flow.fsmBodyRendered && flow.fsmContextSet && flow.newWindowNoThrow && flow.compareRendered && !flow.error
  };

  result.errors = perr;
  result.ALL_PASS = perr.length === 0 && Object.values(result.scenarios).every(s => s.PASS);
  fs.writeFileSync(OUT + '\\task_R1_result.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
