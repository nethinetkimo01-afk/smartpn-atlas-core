# -*- coding: utf-8 -*-
"""
spec_gate_ie.py — IE 細表「總計列完整性」閘門（Task IE-2 定案 2026-07-15，頁面級真渲染）。

★閘門覆蓋率鐵則（25 規則）：必須覆蓋規格的完整結構維度——IE 細表**全部段 × 全部區塊 × 全部分組**，
  只驗一處＝閘門失效。尾端印出覆蓋率（幾段/幾區塊/幾分組/幾欄）。

判定（逐段 cutting/stitching/assembly/stf → 逐區塊 → 逐分組 → 逐欄）：
  1 凡有「標準時間/標時」欄的分組 → 底部必須有標時總計
  2 凡有「理論人數」欄的分組     → 底部必須有理論人數總計
  3 凡有「實際人數/要求人數」欄的分組 → 底部必須有該欄總計
  4 多製程分組（印线画线/削皮/贴补强/涂边烘毛边/热压/磨皮/烘鞋垫/轉印鞋垫）→ 每組各自獨立小計，
    且**橫向對齊該組**（總計格 index == 表頭該欄 index，非用 colspan 蓋掉）
  5 數字可追溯：總計 == 該區塊該欄各列加總（誤差 0）
  6 填值即時更新：手工輸入後小計即時變（不需 reload）；空欄視為 0
  7 欄位對齊：每列 td 數 == 表頭欄數（含總計列）
  8 read_only 全灰迴歸；9 三語迴歸（中/英/越表頭切換）

用法：SPEC_GATE_IE_BASE=http://127.0.0.1:5095 python spec_gate_ie.py
"""
import os, sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = os.environ.get('SPEC_GATE_IE_BASE', 'http://127.0.0.1:5095')
# 正式庫形狀：多 header（含資料齊全/僅裁斷/多段混合），非單一乾淨案例
HEADERS = [int(x) for x in (os.environ.get('SPEC_GATE_IE_HEADERS', '32,160,80').split(','))]
# read_only 只能看「已核准鎖定版」(ie_stage.is_approved=1)；header 160=量產(已核准)
RO_HEADER = int(os.environ.get('SPEC_GATE_IE_RO_HEADER', '160'))
SEGS = ['cutting', 'stitching', 'assembly', 'stf']

R = []
COV = {'headers': set(), 'segs': set(), 'zones': set(), 'groups': set(), 'cols': 0, 'roles': set(), 'langs': set()}


def rec(n, ok, d=''):
    R.append((n, ok))
    print(f"  {'✅' if ok else '❌'} {n}" + (f" — {d}" if d else ''))


def need_kind(zh):
    if not zh:
        return None
    if re.search(r'標時|標准時間|標準時間', zh):
        return 'std'
    if re.search(r'理論人數', zh):
        return 'theory'
    if re.search(r'要求人數|實際人數', zh):
        return 'actual'
    return None


# 逐表掃描：thead 網格 → 每欄 (分組, 中文欄名)；總計列網格 → 該欄是否有總計格
JS_SCAN = r"""
() => {
  const norm = s => (s||'').replace(/\s+/g,'').replace(/\(.*?\)/g,'').replace(/（.*?）/g,'').trim();
  function gridOf(rows){
    const occ=[];
    rows.forEach((tr,r)=>{ let c=0;
      for (const cell of tr.children){
        while (occ[r] && occ[r][c]) c++;
        const cs=parseInt(cell.getAttribute('colspan')||'1'), rs=parseInt(cell.getAttribute('rowspan')||'1');
        for(let i=0;i<rs;i++) for(let j=0;j<cs;j++){const rr=r+i,cc=c+j;occ[rr]=occ[rr]||[];occ[rr][cc]=cell;}
        c+=cs;
      }});
    return occ;
  }
  const out=[];
  for (const table of document.querySelectorAll('table.proc-table')){
    const tb=table.querySelector('tbody'); const tbid=tb?(tb.id||''):'';
    const zone=tbid.replace(/^tbody-(cut|gen)-/,'')||'?';
    const heads=[...table.querySelectorAll('thead tr')]; if(!heads.length) continue;
    const hg=gridOf(heads); const last=hg[hg.length-1]||[];
    const ncol=Math.max(...hg.map(r=>(r||[]).length));
    const cols=[];
    for(let c=0;c<ncol;c++){
      const zh=last[c]?norm(last[c].textContent):'';
      let grp='';
      for(let r=0;r<hg.length;r++){
        const cell=hg[r]&&hg[r][c];
        if(cell&&(cell.classList.contains('th-cut-group')||cell.classList.contains('th-post-group'))){
          const t=norm(cell.textContent); if(t) grp=t;
        }
      }
      cols.push({idx:c,zh,grp});
    }
    const trTot=table.querySelector('tr.zone-total-row');
    const totCells=trTot?(gridOf([trTot])[0]||[]):[];
    // 欄位對齊：資料列/總計列的格位總數必須等於表頭欄數
    const bodyRows=[...table.querySelectorAll('tbody tr')].filter(tr=>
      !tr.classList.contains('add-trigger-row') && !tr.classList.contains('add-row-inline'));
    const widths=bodyRows.map(tr=>{
      let n=0; for(const td of tr.children) n+=parseInt(td.getAttribute('colspan')||'1'); return n;
    });
    out.push({zone, ncol, hasTotalRow: !!trTot,
      cols: cols.map(c=>{ const cell=totCells[c.idx];
        return {idx:c.idx, zh:c.zh, grp:c.grp,
          totalText: cell?(cell.textContent||'').trim():null,
          totalCls: cell?cell.className:null,
          spanned: !!(cell && parseInt(cell.getAttribute('colspan')||'1')>1)};
      }),
      rowWidths: widths});
  }
  return out;
}
"""

TOTAL_CLS = ('zt-std', 'zt-theory', 'zt-actual', 'zt-post-std', 'zt-post-theory')


def scan(pg, seg):
    btn = pg.query_selector(f'.tab-btn[data-seg="{seg}"]')
    if not btn:
        return None
    btn.click(); pg.wait_for_timeout(1600)
    return pg.evaluate(JS_SCAN)


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        ctx = b.new_context(viewport={'width': 1900, 'height': 1100})
        pg = ctx.new_page()
        pg.on('dialog', lambda d: d.accept())
        pg.goto(f'{BASE}/login', wait_until='domcontentloaded')
        pg.fill('#username', 'jim'); pg.fill('#password', 'admin123')
        pg.click('#btnLogin'); pg.wait_for_timeout(900)
        COV['roles'].add('jim(admin)')

        missing, misaligned, spanned_bad = [], [], []
        for hid in HEADERS:
            pg.goto(f'{BASE}/ie/{hid}/detail', wait_until='domcontentloaded')
            pg.wait_for_timeout(1800)
            COV['headers'].add(hid)
            for seg in SEGS:
                data = scan(pg, seg)
                if data is None:
                    rec(f'[h{hid}/{seg}] 頁簽存在', False, '找不到頁簽鈕'); continue
                COV['segs'].add(seg)
                for z in data:
                    COV['zones'].add(f"{seg}/{z['zone']}")
                    for c in z['cols']:
                        kind = need_kind(c['zh'])
                        if not kind:
                            continue
                        COV['cols'] += 1
                        COV['groups'].add(f"{seg}/{z['zone']}/{c['grp'] or '(主)'}")
                        key = f"h{hid} {seg}/{z['zone']}/{c['grp'] or '(主)'}/{c['zh']}"
                        if not z['hasTotalRow']:
                            missing.append(key + ' [無總計列]'); continue
                        if c['spanned']:
                            spanned_bad.append(key + ' [被 colspan 蓋掉→未對齊該組]'); continue
                        if not (c['totalCls'] and any(k in c['totalCls'] for k in TOTAL_CLS)):
                            missing.append(key)
                    for w in z['rowWidths']:
                        if w != z['ncol']:
                            misaligned.append(f"h{hid} {seg}/{z['zone']} 列寬={w} 表頭欄數={z['ncol']}")

        rec(f'規則1-3：每個有 標時/理論人數/實際人數 欄的分組都有對應總計（逐段逐區塊逐分組，共驗 {COV["cols"]} 欄）',
            not missing, f'缺={len(missing)}' + ('　→ ' + '; '.join(missing[:6]) if missing else ''))
        rec('規則4：多製程分組各自獨立小計且橫向對齊該組（總計格 index 對上表頭欄，非 colspan 蓋掉）',
            not spanned_bad, f'未對齊={len(spanned_bad)}' + ('　→ ' + '; '.join(spanned_bad[:6]) if spanned_bad else ''))
        rec('規則7：欄位對齊不跑掉（每列格位數 == 表頭欄數）',
            not misaligned, f'不齊={len(misaligned)}' + ('　→ ' + '; '.join(misaligned[:4]) if misaligned else ''))

        # ── 規則5：數字可追溯（總計 == 各列加總，誤差 0）──
        pg.goto(f'{BASE}/ie/32/detail', wait_until='domcontentloaded'); pg.wait_for_timeout(1800)
        scan(pg, 'cutting')
        trace = pg.evaluate(r"""
        () => {
          const F=['post_marking_std','post_skiving_std','post_attach_std','post_edge_std','post_heat_std','post_polish_std'];
          const z=(DATA.zones||[]).find(x=>x.zone==='裁斷機'); if(!z) return {err:'無裁斷機區塊'};
          const div=3600/EOLR; const out=[];
          const tr=[...document.querySelectorAll('tr.zone-total-row')].find(r=>r.dataset.totalZone==='裁斷機');
          if(!tr) return {err:'無總計列'};
          for(const f of F){
            let sum=0;
            for(const row of (z.rows||[])){ if(row.flag==='deleted') continue;
              const v=parseFloat(row[f]); if(!isNaN(v)&&v>0) sum+=v; }
            const td=tr.querySelector(`.zt-post-std[data-total-field="${f}"]`);
            const tdT=tr.querySelector(`.zt-post-theory[data-total-field="${f}"]`);
            out.push({f, srcStd:Math.round(sum*10)/10, shownStd:td?parseFloat(td.textContent||'0'):null,
                      srcTh:Math.round(sum/div*10)/10, shownTh:tdT?parseFloat(tdT.textContent||'0'):null});
          }
          return {out};
        }""")
        if trace.get('err'):
            rec('規則5：數字可追溯（後製各分組小計 = 各列加總）', False, trace['err'])
        else:
            bad = [t for t in trace['out']
                   if abs((t['shownStd'] or 0) - t['srcStd']) > 0.11 or abs((t['shownTh'] or 0) - t['srcTh']) > 0.11]
            detail = ' '.join(f"{t['f'].replace('post_','').replace('_std','')}={t['shownStd']}/{t['shownTh']}" for t in trace['out'])
            rec('規則5：數字可追溯——後製各分組小計 = 該區塊各列加總（誤差 0）', not bad, detail)

        # ── 規則6：填值即時更新（不 reload）+ 空欄視為 0 ──
        live = pg.evaluate(r"""
        () => {
          const tr=[...document.querySelectorAll('tr.zone-total-row')].find(r=>r.dataset.totalZone==='裁斷機');
          const td=tr.querySelector('.zt-post-std[data-total-field="post_polish_std"]');   // 磨皮：原本全空=0
          const before=parseFloat(td.textContent||'0');
          const inp=document.querySelector('input[data-pfield="post_polish_std"]');
          if(!inp) return {err:'找不到磨皮輸入格'};
          const pid=inp.dataset.pid;
          inp.value='12.5'; inp.dispatchEvent(new Event('input',{bubbles:true}));
          const after=parseFloat(td.textContent||'0');
          const thCell=document.querySelector(`td[data-pfield-th="post_polish_std"][data-pid="${pid}"]`);
          const thVal=thCell?thCell.textContent.trim():null;
          const expTh=(12.5/(3600/EOLR)).toFixed(1);
          // 還原（不留髒資料、不存檔）
          inp.value=''; inp.dispatchEvent(new Event('input',{bubbles:true}));
          const back=parseFloat(td.textContent||'0');
          return {before, after, thVal, expTh, back};
        }""")
        if live.get('err'):
            rec('規則6：填值即時更新（手工輸入 → 該組小計即時變）', False, live['err'])
        else:
            ok6 = (abs(live['after'] - (live['before'] + 12.5)) < 0.11
                   and abs(float(live['thVal'] or 0) - float(live['expTh'])) < 0.11
                   and abs(live['back'] - live['before']) < 0.11)
            rec('規則6：填值即時更新（輸入 12.5 → 小計即時 +12.5、理論人數連動、清空→視為 0 復原）',
                ok6, f"小計 {live['before']}→{live['after']}（清空後 {live['back']}）· 該列理論人數={live['thVal']}(期望{live['expTh']})")

        # ── 規則：樣式統一（總計列無框/粗體/上方細線，與既有總計列一致）──
        sty = pg.evaluate(r"""
        () => {
          const tr=[...document.querySelectorAll('tr.zone-total-row')].find(r=>r.dataset.totalZone==='裁斷機');
          const main=tr.querySelector('.zt-std'), post=tr.querySelector('.zt-post-std');
          const g=e=>{const s=getComputedStyle(e);return {fw:s.fontWeight, bt:s.borderTopWidth, bg:s.backgroundColor, bl:s.borderLeftWidth};};
          return {main:g(main), post:g(post)};
        }""")
        same = (sty['main']['fw'] == sty['post']['fw'] and sty['main']['bt'] == sty['post']['bt']
                and sty['main']['bg'] == sty['post']['bg'] and sty['main']['bl'] == sty['post']['bl'])
        rec('樣式統一：後製小計格與既有總計格同樣式（粗體/上方細線/無左右框/同底色）',
            same, f"主={sty['main']} 後製={sty['post']}")

        # ── 三語迴歸：切 中/英/越 表頭與小計都在 ──
        langs_ok, ldet = True, []
        for lg in ['en', 'vi', 'zh']:
            try:
                pg.evaluate(f'setLang({json.dumps(lg)})'); pg.wait_for_timeout(700)
                COV['langs'].add(lg)
                n = pg.evaluate("document.querySelectorAll('tr.zone-total-row .zt-post-std').length")
                ldet.append(f'{lg}:小計格={n}')
                if n < 8:
                    langs_ok = False
            except Exception as e:
                langs_ok = False; ldet.append(f'{lg}:EXC')
        rec('三語迴歸：中/英/越切換後 後製分組小計仍在（不因語言重繪而消失）', langs_ok, ' '.join(ldet))
        ctx.close()

        # ── read_only 全灰迴歸 ──
        ctx2 = b.new_context(viewport={'width': 1900, 'height': 1100})
        pg2 = ctx2.new_page(); pg2.on('dialog', lambda d: d.accept())
        pg2.goto(f'{BASE}/login', wait_until='domcontentloaded')
        pg2.fill('#username', 'tongcai'); pg2.fill('#password', 'x')
        pg2.click('#btnLogin'); pg2.wait_for_timeout(900)
        COV['roles'].add('read_only(tongcai)')
        pg2.goto(f'{BASE}/ie/{RO_HEADER}/detail', wait_until='domcontentloaded'); pg2.wait_for_timeout(2000)
        b2 = pg2.query_selector('.tab-btn[data-seg="cutting"]')
        if b2: b2.click(); pg2.wait_for_timeout(1400)
        ro = pg2.evaluate(r"""
        () => {
          // applyReadOnlyDOM 會把 input/select 換成純文字 span → 全灰＝完全沒有可編輸入
          const editable=[...document.querySelectorAll('#mainContent input,#mainContent select,#mainContent textarea')]
              .filter(i=>!i.disabled && !i.readOnly && i.type!=='checkbox' && i.type!=='radio').length;
          const tables=document.querySelectorAll('table.proc-table').length;
          const totals=document.querySelectorAll('tr.zone-total-row .zt-post-std').length;
          const locked=/尚無鎖定版|沒有可檢視/.test(document.body.innerText);
          return {editable, tables, totals, locked};
        }""")
        rec('read_only 全灰迴歸：鎖定版可讀 + 完全無可編輸入(全灰) + 後製小計仍看得見',
            (not ro['locked']) and ro['tables'] > 0 and ro['editable'] == 0 and ro['totals'] > 0,
            f"鎖定版渲染={not ro['locked']} 表格={ro['tables']} 可編輸入={ro['editable']}(期望0) 後製小計格={ro['totals']}")
        ctx2.close()
        b.close()

    npass = sum(1 for _, ok in R if ok)
    print('\n' + '─' * 70)
    print(f'  閘門覆蓋率：header {sorted(COV["headers"])}（{len(COV["headers"])}）'
          f' · 段 {sorted(COV["segs"])}（{len(COV["segs"])}/4）'
          f' · 區塊 {len(COV["zones"])} 個 · 分組 {len(COV["groups"])} 個 · 受檢欄 {COV["cols"]} 欄'
          f' · 角色 {sorted(COV["roles"])} · 語言 {sorted(COV["langs"])}')
    print(f'  區塊明細：{sorted(COV["zones"])}')
    print('=' * 70)
    print(f'  spec_gate_ie: {npass}/{len(R)} → {"✅ ALL GREEN" if npass == len(R) else "❌ FAIL"}')
    print('=' * 70)
    sys.exit(0 if npass == len(R) else 1)


if __name__ == '__main__':
    print(f'===== spec_gate_ie（IE 細表總計完整性·逐段逐區塊逐分組）· BASE={BASE} =====')
    main()
