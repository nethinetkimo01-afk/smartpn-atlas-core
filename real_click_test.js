#!/usr/bin/env node
/**
 * real_click_test.js — 真點擊測試（jsdom）。中樞新版判定（不得放寬）：
 *   每顆按鈕在「全新載入的頁面」上獨立測試——按下後「可見文字快照」必須有變化＝活；無變化＝死。
 *   可見文字＝排除隱藏頁/視圖/分頁面板(.page/.view/.tab-panel/.pane/.screen/.unit-pane:not(.active))、
 *   inline display:none、未開啟 modal 之後的螢幕文字。禁止任何裝飾層(__fx 等)讓閘門變綠。
 * 用法：node real_click_test.js <demo.html 路徑>
 * 8 項：1 死按鈕=0 · 2 引導入口 · 3 引導≥4步 · 4-8 機制五項(MOCK_WORLD)。
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const file = process.argv[2];
if (!file) { console.error('用法: node real_click_test.js <demo.html>'); process.exit(2); }
const html = fs.readFileSync(file, 'utf8');
const label = path.basename(file);
const SEL = '[onclick], button, .tab, .nav-item, [role="tab"], .nav-btn, .cat-btn, .fc, .main-tab, .nav-sub, .tab-btn, .level-btn';
const SWITCH = ['page', 'view', 'tab-panel', 'pane', 'screen', 'unit-pane'];

function snap(doc) {
  if (!doc.body) return '';
  let out = '';
  (function walk(node) {
    if (node.nodeType === 3) { out += node.textContent; return; }
    if (node.nodeType !== 1) return;
    const el = node;
    const disp = el.style && el.style.display;
    if (disp === 'none') return;
    if (el.classList) {
      if (SWITCH.some(c => el.classList.contains(c)) && !el.classList.contains('active')) return;
      const isModal = el.classList.contains('modal-backdrop') || el.classList.contains('fsm-modal') ||
                      el.classList.contains('modal-overlay') || el.classList.contains('modal');
      if (isModal && !el.classList.contains('open') && disp !== 'flex' && disp !== 'block') return;
    }
    for (const c of el.childNodes) walk(c);
  })(doc.body);
  return out.replace(/\s+/g, ' ').trim();
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

async function main() {
  // 全新頁面取按鈕總數
  const d0 = mk(); await ready(d0);
  const total = d0.window.document.querySelectorAll(SEL).length;
  d0.window.close();

  // ── 1) 死按鈕：每顆在全新頁面獨立測試 ──
  const dead = [];
  for (let i = 0; i < total; i++) {
    const d = mk(); await ready(d);
    const doc = d.window.document;
    const el = doc.querySelectorAll(SEL)[i];
    if (!el) { d.window.close(); continue; }
    const before = snap(doc);
    let changed = false;
    for (let k = 0; k < 2 && !changed; k++) { try { el.click(); } catch (e) {} if (snap(doc) !== before) changed = true; }
    if (!changed) {
      const tag = (el.textContent || el.getAttribute('title') || el.getAttribute('onclick') || el.id || el.className || '?').toString().replace(/\s+/g, ' ').trim().slice(0, 40);
      dead.push(tag);
    }
    d.window.close();
  }
  rec('死按鈕 = 0（每顆在全新頁面按下畫面必變）', dead.length === 0,
    `可點=${total} 死按鈕=${dead.length}${dead.length ? ' → ' + dead.slice(0, 14).join(' | ') : ''}`);

  // ── 2/3) 引導 + 步數 · 4-8) 機制（單一實例）──
  const d = mk(); await ready(d);
  const { window } = d; const doc = window.document;
  const guideRe = /演示|流程|tour|guide|guided/i;
  const guideEntry = Array.from(doc.querySelectorAll('[onclick], button, a'))
    .find(el => guideRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || '') + ' ' + (el.id || '')));
  rec('引導入口存在且可點', !!guideEntry, guideEntry ? `入口='${(guideEntry.textContent || guideEntry.id).trim().slice(0, 24)}'` : '找不到入口');

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

  console.log(`\n===== real_click_test · ${label} =====`);
  let npass = 0;
  for (const r of results) { if (r.ok) npass++; console.log(`  ${r.ok ? '✅' : '❌'} ${r.name}${r.detail ? ' — ' + r.detail : ''}`); }
  const green = npass === results.length && results.length >= 8;
  console.log(`\n  ${npass}/${results.length}  →  ${green ? '✅ ALL GREEN' : '❌ FAIL'}`);
  process.exit(green ? 0 : 1);
}
main();
