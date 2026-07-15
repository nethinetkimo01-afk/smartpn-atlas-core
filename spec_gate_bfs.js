#!/usr/bin/env node
/**
 * spec_gate_bfs.js — Task F：真實點擊 BFS 走遍主 UI（補齊 fresh 判定的覆蓋盲區）。
 *
 * 為什麼需要這支（fresh_click_test 的結構性盲區）：
 *   死按鈕唯一判定＝「全新頁面 + 零預備動作 + 零排除文字快照」。該判定強制 App 走 lazy render，
 *   而 lazy render 又讓「全新頁面」上本來就只有落地頁的控制項 → fresh 判定只驗得到落地頁按鈕
 *   （供應商 205→16、品牌 62→47）。深層按鈕從未被走到＝「沒驗」，不是「驗過」。
 *   本閘門用**真實點擊**走進每個畫面，在該路徑狀態下逐顆判定，把「沒驗」補成「驗過」。
 *
 * 判定鐵則（與 fresh_click_test 同源，不得放寬）：
 *   1. 只用**真實點擊**前進——絕不呼叫 showView/showPage/switchTab 等任何頁面 API 直達。
 *   2. 每顆按鈕都在**全新頁面重播該路徑**後才點（一顆一個 JSDOM 實例，狀態互不污染）。
 *   3. 判定＝按下後「可見文字快照」有變化＝活；無變化＝死。
 *      快照＝當前**實際可見**的文字（getComputedStyle 解析 class 型 display:none，
 *      排除隱藏頁）——BFS 已把畫面真的導覽過去，看得見的才算數。
 *   4. 只判定「當前畫面實際可見且點得到」的按鈕：
 *      - 看不見的（祖先 display:none）→ 使用者點不到，留給它自己的畫面去判；
 *      - modal 開著時，被 modal 遮住的頁面按鈕點不到 → 只判 modal 內的控制項
 *        （modal 是阻斷式覆蓋層；computed style 仍算它「可見」，但使用者點不到它）。
 *
 * 用法：node spec_gate_bfs.js <demo.html>
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const file = process.argv[2];
if (!file) { console.error('用法: node spec_gate_bfs.js <demo.html>'); process.exit(2); }
const html = fs.readFileSync(file, 'utf8');
const label = path.basename(file);

const SEL = '[onclick], button, .tab, .nav-item, [role="tab"], .nav-btn, .cat-btn, .fc, .main-tab, .nav-sub, .tab-btn, .level-btn';
const MAX_SCREENS = 60;
const MAX_EVALS = 4000;

// ── 自我防作弊：判定程式不得呼叫頁面 API（直達＝繞過真實點擊路徑） ──
(function selfCheck() {
  const code = fs.readFileSync(__filename, 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/\/\/[^\n]*/g, ' ')
    .replace(/`(?:\\[\s\S]|[^\\`])*`/g, '``')
    .replace(/'(?:\\[\s\S]|[^\\'])*'/g, "''")
    .replace(/"(?:\\[\s\S]|[^\\"])*"/g, '""');
  if (/\b(showView|showPage|switchTab|goToView|openTab)\s*\(/.test(code)) {
    console.error('❌ 自我防作弊失敗：BFS 呼叫了頁面 API（直達）＝繞過真實點擊路徑。');
    process.exit(3);
  }
})();

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
const settle = () => new Promise(r => setTimeout(r, 45));

// 元素是否「實際看得見」：祖先鏈沒有 display:none / visibility:hidden（jsdom 會解析 class 型 CSS）
function isVisible(win, el) {
  let n = el;
  while (n && n.nodeType === 1) {
    let s;
    try { s = win.getComputedStyle(n); } catch (e) { return true; }
    if (s && (s.display === 'none' || s.visibility === 'hidden')) return false;
    n = n.parentElement;
  }
  return true;
}
// 可見文字快照（BFS 已真的導覽過去 → 以「使用者當下看得到的文字」為準）
function snap(win, doc) {
  if (!doc.body) return '';
  let out = '';
  (function walk(node) {
    if (node.nodeType === 3) { out += node.textContent; return; }
    if (node.nodeType !== 1) return;
    let s;
    try { s = win.getComputedStyle(node); } catch (e) { s = null; }
    if (s && (s.display === 'none' || s.visibility === 'hidden')) return;
    for (const c of node.childNodes) walk(c);
  })(doc.body);
  return out.replace(/\s+/g, ' ').trim();
}
/** 目前是否有「阻斷式 modal」開著；有的話回傳該 modal 元素（只有它裡面的控制項點得到）。 */
function openModal(win, doc) {
  const cands = [...doc.querySelectorAll('[class*="modal" i],[class*="overlay" i],[role="dialog"]')];
  for (const m of cands) {
    if (m.closest('[class*="modal" i]') !== m && m.parentElement && m.parentElement.closest('[class*="modal" i]')) continue;
    let s; try { s = win.getComputedStyle(m); } catch (e) { continue; }
    if (!s || s.display === 'none' || s.visibility === 'hidden') continue;
    if (s.position !== 'fixed' && s.position !== 'absolute') continue;   // 阻斷式覆蓋層才算
    if (!(m.textContent || '').trim()) continue;
    return m;
  }
  return null;
}
// 畫面識別＝導覽結構（哪些頁/視圖/分頁在啟用 + 哪些 modal 開著）。
// 不用全文當識別，否則像「改一個欄位權限」這種同畫面內的狀態變化會被當成新畫面 → BFS 爆炸。
function screenSig(win, doc) {
  const act = (sel) => [...doc.querySelectorAll(sel)].filter(e => e.classList.contains('active')).map(e => e.id || e.className).sort();
  const modals = [...doc.querySelectorAll('[class*="modal" i]')]
    .filter(e => isVisible(win, e)).map(e => e.id || e.className).sort();
  const sig = { p: act('.page'), v: act('.view'), t: act('.tab-panel'), m: modals };
  if (!sig.p.length && !sig.v.length && !sig.t.length && !sig.m.length) {
    // 沒有頁/視圖結構的檔：退回用「可見按鈕標籤集合」當畫面識別
    const win2 = win;
    sig.b = [...doc.querySelectorAll(SEL)].filter(e => isVisible(win2, e))
      .map(e => (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 18)).sort();
  }
  return JSON.stringify(sig);
}
function tagOf(el) {
  return (el.textContent || el.getAttribute('title') || el.getAttribute('onclick') || el.id || el.className || '?')
    .toString().replace(/\s+/g, ' ').trim().slice(0, 34) || '(空白鈕)';
}

// 在全新頁面重播 path（只用真實點擊），回傳 dom
async function replay(pathIdx) {
  const d = mk(); await settle();
  const doc = d.window.document;
  for (const i of pathIdx) {
    const el = doc.querySelectorAll(SEL)[i];
    if (!el) break;
    try { el.click(); } catch (e) {}
    await settle();
  }
  return d;
}

async function main() {
  const t0 = Date.now();
  const visited = new Set();
  const queue = [[]];                 // 從落地頁開始（空路徑）
  const dead = [];
  let evals = 0, screens = 0, capped = null;
  const judged = [];                  // {sig, idx, label, alive}

  while (queue.length) {
    if (screens >= MAX_SCREENS) { capped = `畫面數達上限 ${MAX_SCREENS}`; break; }
    if (evals >= MAX_EVALS) { capped = `判定次數達上限 ${MAX_EVALS}`; break; }
    const p = queue.shift();

    const d0 = await replay(p);
    const w0 = d0.window, doc0 = w0.document;
    const sig = screenSig(w0, doc0);
    if (visited.has(sig)) { d0.window.close(); continue; }
    visited.add(sig); screens++;

    // 該畫面「當前實際可見且點得到」的按鈕
    const all = [...doc0.querySelectorAll(SEL)];
    const blocker = openModal(w0, doc0);      // modal 開著 → 只有 modal 內的控制項點得到
    const vis = [];
    all.forEach((el, i) => {
      if (!isVisible(w0, el)) return;
      if (blocker && !blocker.contains(el)) return;
      vis.push({ i, label: tagOf(el) });
    });
    d0.window.close();

    for (const { i, label: lb } of vis) {
      if (evals >= MAX_EVALS) { capped = `判定次數達上限 ${MAX_EVALS}`; break; }
      const d = await replay(p);                 // 全新頁面 + 重播路徑 → 狀態乾淨
      const win = d.window, doc = d.window.document;
      const el = doc.querySelectorAll(SEL)[i];
      if (!el) { d.window.close(); continue; }
      const before = snap(win, doc);
      let changed = false;
      for (let k = 0; k < 2 && !changed; k++) {
        try { el.click(); } catch (e) {}
        await settle();
        if (snap(win, doc) !== before) changed = true;
      }
      evals++;
      judged.push({ sig, idx: i, label: lb, alive: changed });
      if (!changed) dead.push(`${lb}  ← 路徑[${p.join('→') || '落地頁'}] #${i}`);
      else {
        const ns = screenSig(win, doc);
        if (!visited.has(ns) && queue.length + screens < MAX_SCREENS * 3) queue.push(p.concat([i]));
      }
      d.window.close();
    }
  }

  const secs = ((Date.now() - t0) / 1000).toFixed(0);
  console.log(`\n===== spec_gate_bfs · ${label} =====`);
  console.log(`  走訪畫面數 = ${screens}`);
  console.log(`  可達按鈕數（各畫面當前可見，去重 screen×button）= ${judged.length}`);
  console.log(`  已判定數 = ${evals}`);
  console.log(`  死按鈕數 = ${dead.length}`);
  if (dead.length) { console.log('  死按鈕清單：'); dead.forEach(x => console.log('   ❌ ' + x)); }
  if (capped) console.log(`  ⚠ 截斷：${capped}（未走完；不得視為覆蓋完整）`);

  const noGap = (evals === judged.length) && !capped;
  const green = dead.length === 0 && noGap && screens > 0;
  console.log(`\n  覆蓋率：已判定 ${evals} / 可達 ${judged.length} → ${noGap ? '✅ 無漏驗' : '❌ 有漏驗/被截斷'}`);
  console.log(`  死按鈕 = ${dead.length} → ${dead.length === 0 ? '✅' : '❌'}`);
  console.log(`  ${green ? '✅ ALL GREEN' : '❌ FAIL'}  （耗時 ${secs}s）`);
  process.exit(green ? 0 : 1);
}
main();
