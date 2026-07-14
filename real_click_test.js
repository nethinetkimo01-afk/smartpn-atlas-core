#!/usr/bin/env node
/**
 * real_click_test.js — 真點擊測試（jsdom，不看原始碼字串）。
 * 用法：node real_click_test.js <demo.html 路徑>
 *
 * 8 項檢查（全綠才 PASS，任一 FAIL → exit 1）：
 *   1 死按鈕=0（每個可點元素點擊後 body 文字快照必變；無變化=死按鈕）
 *   2 引導入口存在且可點（文字/onclick 含 演示/流程/tour/guide）
 *   3 引導可連走 ≥4 步（找 下一步/next/→/繼續，每步畫面不同）
 *   4 機制 fieldGroups
 *   5 機制 accessRequests | grants
 *   6 機制 properties | units
 *   7 機制 exchanges | evidence
 *   8 機制 apiSpec | mappings
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const file = process.argv[2];
if (!file) { console.error('用法: node real_click_test.js <demo.html>'); process.exit(2); }
const html = fs.readFileSync(file, 'utf8');
const label = path.basename(file);

const results = [];
function rec(name, ok, detail) { results.push({ name, ok, detail: detail || '' }); }

// 「畫面文字快照」＝整體可見文字 + DOM 結構信號（class/開關狀態）。
// 用 body.textContent 捕捉內容變化，附加 active/open 類別數與元素數，讓純切換(class toggle)
// 也算「有變化」——死按鈕＝點了 DOM 完全無反應（文字與結構皆不變）。
function snap(doc) {
  if (!doc.body) return '';
  const text = (doc.body.textContent || '').replace(/\s+/g, ' ').trim();
  let actives = 0, opens = 0;
  try { actives = doc.querySelectorAll('.active').length; opens = doc.querySelectorAll('.open,.on').length; } catch (e) {}
  const nEl = doc.body.getElementsByTagName('*').length;
  // 附上目前 active 元素的「識別特徵」序列（class/id），使切換不同 active 目標被視為畫面變化
  let activeSig = '';
  try {
    activeSig = Array.from(doc.querySelectorAll('.active, .open, .on'))
      .map(e => (e.id || '') + '.' + (e.className || '')).join('|');
  } catch (e) {}
  return `${text}::a${actives}o${opens}n${nEl}::${activeSig}`;
}

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  beforeParse(window) {
    // stub 避免 jsdom 誤報 / not-implemented
    window.alert = () => {};
    window.confirm = () => true;
    window.prompt = () => '';
    window.scrollTo = () => {};
    window.open = () => ({ document: {}, focus() {}, close() {} });
    window.matchMedia = window.matchMedia || (() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }));
    if (window.Element && window.Element.prototype) {
      window.Element.prototype.scrollIntoView = () => {};
      window.HTMLElement.prototype.scrollIntoView = () => {};
    }
    if (!window.URL.createObjectURL) window.URL.createObjectURL = () => 'blob:stub';
  },
});

const { window } = dom;
const { document } = window;

function afterLoad(fn) {
  // 內嵌 script 同步跑完；再等一 tick 讓 load/init 完成
  if (document.readyState === 'complete') return setTimeout(fn, 60);
  window.addEventListener('load', () => setTimeout(fn, 60));
  setTimeout(fn, 400); // 保險
}

let done = false;
function finish() {
  if (done) return; done = true;
  console.log(`\n===== real_click_test · ${label} =====`);
  let npass = 0;
  for (const r of results) {
    if (r.ok) npass++;
    console.log(`  ${r.ok ? '✅' : '❌'} ${r.name}${r.detail ? ' — ' + r.detail : ''}`);
  }
  const green = npass === results.length && results.length >= 8;
  console.log(`\n  ${npass}/${results.length}  →  ${green ? '✅ ALL GREEN' : '❌ FAIL'}`);
  try { dom.window.close(); } catch (e) {}
  process.exit(green ? 0 : 1);
}

afterLoad(() => {
  try {
    // ── 1) 死按鈕偵測 ──
    const sel = '[onclick], button, .tab, .nav-item, [role="tab"], .nav-btn, .cat-btn, .fc, .main-tab';
    const nodes = Array.from(document.querySelectorAll(sel));
    const dead = [];
    let clickable = 0;
    for (const el of nodes) {
      // 跳過 disabled / hidden 隱形結構性元素？ 規格要求「可點的都要有反應」→ 全點
      const before = snap(document);
      let changed = false;
      for (let i = 0; i < 2 && !changed; i++) {
        try { el.click(); } catch (e) { /* 拋錯視為未變化 */ }
        if (snap(document) !== before) changed = true;
      }
      clickable++;
      if (!changed) {
        const tag = (el.textContent || el.getAttribute('title') || el.getAttribute('onclick') || el.id || el.className || '?').toString().replace(/\s+/g, ' ').trim().slice(0, 40);
        dead.push(tag);
      }
    }
    rec('死按鈕 = 0（每顆可點元素點擊畫面必變）', dead.length === 0,
      `可點=${clickable} 死按鈕=${dead.length}${dead.length ? ' → ' + dead.slice(0, 12).join(' | ') : ''}`);

    // ── 2/3) 引導入口 + 連走步數 ──
    const guideRe = /演示|流程|tour|guide|guided/i;
    const guideEntry = Array.from(document.querySelectorAll('[onclick], button, a'))
      .find(el => guideRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || '') + ' ' + (el.id || '')));
    rec('引導入口存在且可點', !!guideEntry, guideEntry ? `入口='${(guideEntry.textContent || guideEntry.id).trim().slice(0, 24)}'` : '找不到引導入口');

    let steps = 0;
    if (guideEntry) {
      const seen = new Set();
      try { guideEntry.click(); } catch (e) {}
      seen.add(snap(document)); steps = 1;
      const nextRe = /下一步|next|→|繼續|continue|下一/i;
      const guideNextRe = /nextGuide|guide.*next|next.*guide/i;
      for (let i = 0; i < 12; i++) {
        const cands = Array.from(document.querySelectorAll('[onclick], button, a'));
        // 優先：引導專屬 next（onclick 含 nextGuide / 在 guide 容器內）；否則泛用 next 文字
        let nextBtn = cands.find(el => guideNextRe.test(el.getAttribute('onclick') || ''))
          || cands.find(el => {
              const inGuide = el.closest && el.closest('[id*="guide" i], [class*="guide" i], [id*="Guide"]');
              return inGuide && nextRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || ''));
            })
          || cands.find(el => nextRe.test((el.textContent || '') + ' ' + (el.getAttribute('onclick') || '')));
        if (!nextBtn) break;
        const before = snap(document);
        try { nextBtn.click(); } catch (e) {}
        const after = snap(document);
        if (after === before || seen.has(after)) { if (!seen.has(after)) { seen.add(after); steps++; } break; }
        seen.add(after); steps++;
      }
    }
    rec('引導可連走 ≥4 步（每步畫面不同）', steps >= 4, `走了 ${steps} 步（不同畫面）`);

    // ── 4-8) 五項機制資料 ──
    const MW = window.MOCK_WORLD || {};
    const has = (...keys) => keys.some(k => MW[k] != null && (Array.isArray(MW[k]) ? MW[k].length >= 0 : true) && MW[k] !== undefined && MW[k] !== null && (typeof MW[k] !== 'object' || Object.keys(MW[k]).length > 0 || Array.isArray(MW[k])));
    rec('機制① fieldGroups', has('fieldGroups'), keyInfo(MW, 'fieldGroups'));
    rec('機制② accessRequests | grants', has('accessRequests') || has('grants'), keyInfo(MW, 'accessRequests', 'grants'));
    rec('機制③ properties | units', has('properties') || has('units') || has('unitRegistry'), keyInfo(MW, 'properties', 'units', 'unitRegistry'));
    rec('機制④ exchanges | evidence', has('exchanges') || has('evidence') || has('exchangeEvents') || has('evidenceRecords'), keyInfo(MW, 'exchanges', 'evidence', 'exchangeEvents', 'evidenceRecords'));
    rec('機制⑤ apiSpec | mappings', has('apiSpec') || has('mappings'), keyInfo(MW, 'apiSpec', 'mappings'));
  } catch (e) {
    rec('harness', false, 'EXC ' + e.message);
  }
  finish();
});

function keyInfo(MW, ...keys) {
  for (const k of keys) {
    if (MW[k] != null) {
      const v = MW[k];
      const n = Array.isArray(v) ? v.length : (typeof v === 'object' ? Object.keys(v).length : 1);
      return `${k}(${n})`;
    }
  }
  return '缺: ' + keys.join('/');
}

// 逾時保護
setTimeout(() => { rec('timeout', false, '腳本逾時'); finish(); }, 15000);
