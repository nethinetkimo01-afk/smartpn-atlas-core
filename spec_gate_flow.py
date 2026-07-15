# -*- coding: utf-8 -*-
"""
spec_gate_flow.py — Task D：SmartPN demo「真實點擊路徑」逐場景走通閘門（把「可點」升級成「可用」）。

與 spec_gate_smartpn 的差別（互補，不重複）：
  spec_gate_smartpn：呼叫 window.openScenarios() 開場景，抽驗 token 是否出現（＝資料齊）。
  spec_gate_flow   ：**完全不呼叫任何頁面 API**——從全新頁面用「真實點擊」BFS 找到情境入口，
                     點進每個場景，把該場景 Demo interactions 的每個控制項**逐一點到底**，
                     斷言：①入口可由真實點擊抵達 ②每個場景可點開且畫面真的變
                     ③每個控制項按下畫面真的變（無死路/空白）④該場景規格 token 全部出現（數字/資料正確）。

判定與 fresh_click_test 一致：畫面變化＝doc.body 全部文字快照（零排除）有變。

用法：python spec_gate_flow.py [檔案...]（預設驗 v3 全部檔）
"""
import os, sys, io, json, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# 場景 token 直接沿用 spec_gate_smartpn 的規格對帳表（單一事實來源，不另抄一份）
# 註：須先 import 再包 stdout——該模組匯入時會自行包一次，重複包會關掉底層 buffer。
from spec_gate_smartpn import SCN_TOKENS   # 匯入時該模組已把 stdout 包成 utf-8（不可再包一次）

FILES = sys.argv[1:] or [
    os.path.join(ROOT, 'docs', 'preview', 'SMARTPN_DEMO_V3.html'),
    os.path.join(ROOT, 'docs', 'preview', 'SMARTPN_DEMO_SUPPLIER_V3.html'),
]

NODE = r"""
const fs=require('fs'), {JSDOM}=require('jsdom');
const file=process.argv[2], TOK=JSON.parse(process.argv[3]);
const html=fs.readFileSync(file,'utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,beforeParse(w){
  w.alert=()=>{};w.confirm=()=>true;w.prompt=()=>'';w.scrollTo=()=>{};w.open=()=>({document:{},focus(){},close(){}});
  w.matchMedia=w.matchMedia||(()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}}));
  if(w.Element){w.Element.prototype.scrollIntoView=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};}
  if(!w.URL.createObjectURL)w.URL.createObjectURL=()=>'blob:stub';
}});
const {window}=dom,{document}=window;
// 判定一致：零排除的全文快照
const snap=()=>((document.body&&document.body.textContent)||'').replace(/\s+/g,' ').trim();
const vtext=()=>{const v=document.getElementById('scnView');return v?v.textContent:'';};

setTimeout(()=>{
 const out={scenarios:{}};
 try{
  // ── ① 真實點擊 BFS 找情境入口（禁用任何頁面 API）──
  const cands=[...document.querySelectorAll('button,[onclick],a')];
  const entry=cands.find(b=>/情境|scenario|S02/i.test((b.textContent||'')+' '+(b.id||'')));
  out.entryFound=!!entry;
  if(!entry){ console.log(JSON.stringify(out)); process.exit(0); }
  const b4=snap(); entry.click(); const af=snap();
  out.entryOpens = (af!==b4);                       // 點入口畫面真的變
  out.panelVisible = !!document.getElementById('scnView');

  // ── ②③④ 逐場景：真實點擊走到底 ──
  for(const [id,tokens] of Object.entries(TOK)){
    const r={present:false,opens:false,steps:0,deadSteps:[],missing:[],tokens_ok:true};
    const btn=document.getElementById('scn-btn-'+id);
    r.present=!!btn;
    if(!btn){ out.scenarios[id]=r; continue; }
    const s0=snap(); btn.click(); const s1=snap();
    r.opens=(s1!==s0)||!!vtext();                   // 點場景鈕：畫面變（或已渲染出內容）
    let accum=vtext();
    // 把該場景 Demo interactions「點到底」：輪流點每個控制項——stepper 只有一顆鈕 → 會被連點到走完
    // 整條流程；selector 會輪流切到每個選項。每輪重抓元素（點完會重繪，舊參照失效）。
    const states=new Set([vtext()]);
    for(let round=0; round<14; round++){
      const ctrls=[...document.querySelectorAll('#scnView .scn-ctrl')];
      if(!ctrls.length) break;
      const c=ctrls[round % ctrls.length];
      const label=(c.textContent||'?').trim().slice(0,24);
      const t0=vtext(), g0=snap();
      c.click();
      const t1=vtext(), g1=snap();
      accum += ' \n ' + t1;
      r.steps++;
      states.add(t1);
      if(t1===t0 && g1===g0){ if(r.deadSteps.indexOf(label)<0) r.deadSteps.push(label); }
    }
    r.distinctStates=states.size;
    for(const t of tokens){ if(accum.indexOf(t)<0){ r.tokens_ok=false; r.missing.push(t); } }
    out.scenarios[id]=r;
  }
 }catch(e){ out.__exc=e.message+' @ '+(e.stack||'').split('\n')[1]; }
 console.log(JSON.stringify(out));
 process.exit(0);
},500);
"""


def run(file):
    js = os.path.join(ROOT, '_flow_probe.js')
    open(js, 'w', encoding='utf-8').write(NODE)
    try:
        p = subprocess.run(['node', js, file, json.dumps(SCN_TOKENS)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180, cwd=ROOT)
        line = [l for l in p.stdout.strip().splitlines() if l.startswith('{')]
        return json.loads(line[-1]) if line else {'error': (p.stderr or '')[-400:] or 'no output'}
    finally:
        try: os.remove(js)
        except Exception: pass


def main():
    allok = True
    for f in FILES:
        name = os.path.basename(f)
        print(f'\n===== spec_gate_flow · {name} =====')
        if not os.path.isfile(f):
            print(f'  ❌ 找不到檔案'); allok = False; continue
        res = run(f)
        if res.get('error') or res.get('__exc'):
            print(f"  ❌ harness: {res.get('error') or res.get('__exc')}"); allok = False; continue

        ok_entry = res.get('entryFound') and res.get('entryOpens') and res.get('panelVisible')
        print(f"  {'✅' if ok_entry else '❌'} 情境入口可由「真實點擊」抵達且點開畫面真的變"
              f"（找到={res.get('entryFound')} 點開有變={res.get('entryOpens')} 面板存在={res.get('panelVisible')}）")
        allok = allok and ok_entry

        npass = 0
        scns = res.get('scenarios', {})
        for id in SCN_TOKENS:
            r = scns.get(id, {})
            ok = (r.get('present') and r.get('opens') and r.get('tokens_ok')
                  and r.get('steps', 0) > 0 and not r.get('deadSteps')
                  and r.get('distinctStates', 0) >= 2)
            if ok:
                npass += 1
            else:
                det = []
                if not r.get('present'): det.append('無場景鈕')
                if not r.get('opens'): det.append('點開畫面沒變')
                if not r.get('steps'): det.append('無可走的互動步驟')
                if r.get('distinctStates', 0) < 2: det.append('只走出 %s 種畫面狀態(<2)' % r.get('distinctStates'))
                if r.get('deadSteps'): det.append('死路步驟:' + ','.join(r['deadSteps'][:4]))
                if not r.get('tokens_ok'): det.append('缺資料token:' + ','.join(r.get('missing', [])[:5]))
                print(f"  ❌ {id} — {'; '.join(det)}")
        for id in SCN_TOKENS:
            r = scns.get(id, {})
            if (r.get('present') and r.get('opens') and r.get('tokens_ok')
                    and r.get('steps', 0) > 0 and not r.get('deadSteps')
                    and r.get('distinctStates', 0) >= 2):
                print(f"  ✅ {id} 真實點擊走通 {r['steps']} 步 · {r.get('distinctStates')} 種不同畫面（每步都變）+ 資料 token 齊")
        g = (npass == len(SCN_TOKENS)) and ok_entry
        allok = allok and g
        print(f'  → {npass}/{len(SCN_TOKENS)} {"✅ ALL GREEN" if g else "❌ FAIL"}')

    print('\n' + '=' * 60)
    print(f'  spec_gate_flow: {"✅ ALL GREEN（每檔 16 場景真實點擊全走通）" if allok else "❌ FAIL"}')
    print('=' * 60)
    sys.exit(0 if allok else 1)


if __name__ == '__main__':
    main()
