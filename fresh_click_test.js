#!/usr/bin/env node
/**
 * fresh_click_test.js — 唯一死按鈕判定（中樞定案 2026-07-15，被驗收方不得修改）。
 *
 * 判定鐵則（不得放寬，任何違反即閘門失效）：
 *   1. 每顆按鈕都在「全新載入的頁面」上獨立測試（一顆一個 JSDOM 實例，互不污染）。
 *   2. 點擊前不做任何預備動作——不先導入視圖、不先開分頁、不先點別的鈕、不注入任何狀態。
 *   3. 閘門本身絕不呼叫 showView / showPage / switchTab 等任何頁面 API（違者＝變相放寬）。
 *      → 教訓：前回報「死按鈕 0」是因為點擊前先導入視圖，中樞實測實為 13/71。
 *   4. 判定＝按下後「文字快照」有變化＝活；無變化＝死。
 *      ★快照＝doc.body 的全部文字，**零排除**：不因 .active class 切換、也不因 inline display
 *        的可見性切換而算「畫面變了」。只有**內容真的重繪**（文字真的不同）才算活。
 *      ★★對「導覽類已 active 元素」放行＝變相放寬（中樞 2026-07-15 SP-fix4 定案）。
 *        教訓：Home/My Account/Settings 只 toggle .active、目標頁內容從頭到尾都在 DOM 裡沒重繪；
 *        舊版排除 .page:not(.active) → 誤判為活 → Code 判 0、中樞判 3。
 *        改為排除 inline display:none 也不行：showPage 會切 filter-bar 的 inline display，
 *        My Account/Settings 會因為「篩選列文字消失」被誤判為活（Code 判 1、中樞仍判 3）。
 *        零排除才與中樞一致：品牌端 62 顆 → 死 3（Home/My Account/Settings），完全重現。
 *        同段其它導覽鈕(Favorites/Library/Requests/Dashboard)在 showPage 內呼叫 render*()
 *        → 內容真的重繪 → 快照變 → 活。正解＝比照本 App 既有 lazy render 模式，導覽時才渲染該頁內容。
 *      禁止任何裝飾層(__fx 等)讓閘門變綠。
 *
 * 用法：node fresh_click_test.js <demo.html 路徑>
 * 9 項：1 反作弊(非 splash) · 2 死按鈕=0 · 3 引導入口 · 4 引導≥5步 · 5-9 機制五項(MOCK_WORLD)。
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const file = process.argv[2];
if (!file) { console.error('用法: node fresh_click_test.js <demo.html>'); process.exit(2); }
const html = fs.readFileSync(file, 'utf8');
const label = path.basename(file);

const SEL = '[onclick], button, .tab, .nav-item, [role="tab"], .nav-btn, .cat-btn, .fc, .main-tab, .nav-sub, .tab-btn, .level-btn';
// SWITCH 已廢除：不得因 .active class 切換就當畫面變（見檔頭鐵則 4）

// ── 自我防作弊：閘門原始碼不得出現對頁面 API 的呼叫（預備動作） ──
(function selfCheck() {
  // 只掃「真正的程式碼」：先剝掉註解與字串/樣板字面值，避免說明文字誤判。
  const code = fs.readFileSync(__filename, 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, ' ')      // 區塊註解
    .replace(/\/\/[^\n]*/g, ' ')            // 行註解
    .replace(/`(?:\\[\s\S]|[^\\`])*`/g, '``')   // 樣板字串
    .replace(/'(?:\\[\s\S]|[^\\'])*'/g, "''")   // 單引號字串
    .replace(/"(?:\\[\s\S]|[^\\"])*"/g, '""');  // 雙引號字串
  const banned = /\b(showView|showPage|switchTab|goToView|openTab)\s*\(/;
  if (banned.test(code)) {
    console.error('❌ 閘門自我防作弊失敗：判定程式呼叫了頁面 API（預備動作）＝變相放寬。');
    process.exit(3);
  }
})();

/**
 * 反作弊：起始啟用頁必須是「App 真實預設狀態」，不得是載入專用 splash。
 * 判定：起始 active 的 .page/.view，若 App 內沒有任何控制項能導回它（全檔查無
 * show(Page|View)('<id>') 之類的導覽引用）＝單向載入態，其唯一作用是讓「第一次點任何鈕」
 * 都因為離開 splash 而畫面必變 → 死按鈕被整批洗白。此為頁面級的變相放寬，閘門直接拒收。
 * （教訓 2026-07-15：page-welcome splash 把 13 顆真死鈕洗成 0。）
 */
function splashCheck(doc) {
  const pages = Array.from(doc.querySelectorAll('.page, .view'));
  if (pages.length < 2) return null;
  const act = pages.find(p => p.classList.contains('active'));
  if (!act || !act.id) return null;
  const id = act.id.replace(/^(page|view)-/, '');
  const navRef = new RegExp(`show(?:Page|View)\\s*\\(\\s*['"\`]${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}['"\`]`);
  if (navRef.test(html)) return null;                       // 有控制項導得回 → 是真實頁
  return `起始啟用頁 #${act.id} 是「載入專用 splash」：App 內無任何控制項可導回它（查無 showPage/showView('${id}')）。` +
         `此頁只讓第一次點擊必然變畫面＝整批洗白死按鈕。請移除 splash，預設啟用 App 真實首頁。`;
}

// 文字快照——零排除（見檔頭鐵則 4）。任何「只切可見性」的動作都不會讓快照變 → 判死。
function snap(doc) {
  if (!doc.body) return '';
  return (doc.body.textContent || '').replace(/\s+/g, ' ').trim();
}

function mk() {
  return new JSDOM(html, {
    runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.alert = () => {}; w.confirm = () => true; w.prompt = () => '';
      w.scrollTo = () => {}; w.open = () => ({ document: {}, focus() {}, close() {} });
      w.matchMedia = w.matchMedia || (() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }));
      if (w.Element && w.Element.prototype) { w.Element.prototype.scrollIntoView = () => {}; w.HTMLElement.prototype.scrollIntoView = () => {}; }
      if (!w.URL.createObjectURL) w.URL.createObjectURL = () => 'blob:stub';
    },
  });
}
const ready = (dom) => new Promise(res => setTimeout(res, 60));

const results = [];
const rec = (name, ok, detail) => results.push({ name, ok, detail: detail || '' });
function keyInfo(MW, ...keys) {
  for (const k of keys) if (MW[k] != null) { const v = MW[k]; const n = Array.isArray(v) ? v.length : (typeof v === 'object' ? Object.keys(v).length : 1); return `${k}(${n})`; }
  return '缺: ' + keys.join('/');
}
function tagOf(el) {
  return (el.textContent || el.getAttribute('title') || el.getAttribute('onclick') || el.id || el.className || '?')
    .toString().replace(/\s+/g, ' ').trim().slice(0, 40) || '(空白鈕)';
}

async function main() {
  // 全新頁面取按鈕總數（此實例不點任何東西，用完即棄）
  const d0 = mk(); await ready(d0);
  const total = d0.window.document.querySelectorAll(SEL).length;
  const splash = splashCheck(d0.window.document);
  d0.window.close();
  rec('反作弊：起始啟用頁＝App 真實預設狀態（非載入專用 splash）', !splash, splash || '起始頁可由 App 內導回 → 真實頁');

  // ── 1) 死按鈕：每顆在全新頁面獨立測試，點擊前零預備動作 ──
  const dead = [];
  for (let i = 0; i < total; i++) {
    const d = mk(); await ready(d);          // 全新頁面
    const doc = d.window.document;
    const el = doc.querySelectorAll(SEL)[i]; // 直接取第 i 顆——不導入視圖、不點別的鈕
    if (!el) { d.window.close(); continue; }
    const before = snap(doc);
    let changed = false;
    for (let k = 0; k < 2 && !changed; k++) { try { el.click(); } catch (e) {} if (snap(doc) !== before) changed = true; }
    if (!changed) dead.push(`#${i} ${tagOf(el)}`);
    d.window.close();
  }
  rec('死按鈕 = 0（每顆在全新頁面、零預備動作按下，畫面必變）', dead.length === 0,
    `可點=${total} 死按鈕=${dead.length}${dead.length ? '\n       → ' + dead.join('\n       → ') : ''}`);

  // ── 2/3) 引導 + 步數 · 4-8) 機制（單一實例）──
  const d = mk(); await ready(d);
  const { window } = d; const doc = window.document;
  const guideRe = /演示|流程|tour|guide|guided/i;
  const guideEntry = Array.from(doc.querySelectorAll('[onclick], button, a'))
    .find(el => guideRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || '') + ' ' + (el.id || '')));
  rec('引導入口 querySelector 找得到且可點', !!guideEntry, guideEntry ? `入口='${(guideEntry.textContent || guideEntry.id).trim().slice(0, 24)}'` : '找不到入口');

  let steps = 0;
  if (guideEntry) {
    const seen = new Set(); const nextRe = /下一步|next|→|繼續|continue|下一/i; const gRe = /nextGuide|guide.*next|next.*guide/i;
    try { guideEntry.click(); } catch (e) {}
    seen.add(snap(doc)); steps = 1;
    for (let i = 0; i < 12; i++) {
      const cands = Array.from(doc.querySelectorAll('[onclick], button, a'));
      let nb = cands.find(el => gRe.test(el.getAttribute('onclick') || ''))
        || cands.find(el => { const g = el.closest && el.closest('[id*="guide" i],[class*="guide" i]'); return g && nextRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || '')); })
        || cands.find(el => nextRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || '')));
      if (!nb) break;
      const b4 = snap(doc); try { nb.click(); } catch (e) {} const af = snap(doc);
      if (af === b4 || seen.has(af)) { if (!seen.has(af)) { seen.add(af); steps++; } break; }
      seen.add(af); steps++;
    }
  }
  rec('引導可連走 ≥5 步（每步畫面不同）', steps >= 5, `走了 ${steps} 步`);

  const MW = window.MOCK_WORLD || {};
  const has = (...keys) => keys.some(k => MW[k] != null && (Array.isArray(MW[k]) ? true : (typeof MW[k] !== 'object' || Object.keys(MW[k]).length > 0)));
  rec('機制① fieldGroups', has('fieldGroups'), keyInfo(MW, 'fieldGroups'));
  rec('機制② accessRequests | grants', has('accessRequests') || has('grants'), keyInfo(MW, 'accessRequests', 'grants'));
  rec('機制③ properties | units', has('properties') || has('units') || has('unitRegistry'), keyInfo(MW, 'properties', 'units', 'unitRegistry'));
  rec('機制④ exchanges | evidence', has('exchanges') || has('evidence') || has('exchangeEvents') || has('evidenceRecords'), keyInfo(MW, 'exchanges', 'evidence', 'exchangeEvents', 'evidenceRecords'));
  rec('機制⑤ apiSpec | mappings', has('apiSpec') || has('mappings'), keyInfo(MW, 'apiSpec', 'mappings'));
  d.window.close();

  console.log(`\n===== fresh_click_test · ${label} =====`);
  let npass = 0;
  for (const r of results) { if (r.ok) npass++; console.log(`  ${r.ok ? '✅' : '❌'} ${r.name}${r.detail ? ' — ' + r.detail : ''}`); }
  const green = npass === results.length && results.length >= 9;
  console.log(`\n  ${npass}/${results.length}  →  ${green ? '✅ ALL GREEN' : '❌ FAIL'}`);
  process.exit(green ? 0 : 1);
}
main();
