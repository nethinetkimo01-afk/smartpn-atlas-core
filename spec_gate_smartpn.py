# -*- coding: utf-8 -*-
"""
spec_gate_smartpn.py — SmartPN demo 對「16_S02_TO_S17_COMPLETE_SPECS.md」逐場景對帳。
頁面級（jsdom 真渲染真點擊，非字串比對）：每個 S02–S17 場景須有可點畫面 + 場景關鍵資料，缺一即 FAIL。
用法：python spec_gate_smartpn.py           → 驗兩個 v3 檔（品牌+供應商）
      python spec_gate_smartpn.py <file>    → 驗指定檔
"""
import os, sys, io, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = sys.argv[1:] or [
    os.path.join(ROOT, 'docs', 'preview', 'SMARTPN_DEMO_V3.html'),
    os.path.join(ROOT, 'docs', 'preview', 'SMARTPN_DEMO_SUPPLIER_V3.html'),
    os.path.join(ROOT, 'docs', 'preview', 'SMARTPN_DEMO_FACTORY_V3.html'),
]

# 16 場景關鍵 token（依 16 號檔 Demo interactions/表格）——缺一即 FAIL
SCN_TOKENS = {
 'S02':['SPA-COMP-0101','SPA-MAT-0001','SPA-MAT-0002'],
 'S03':['SPA-MAT-0001','SHOE-MAT-118','APP-MAT-552','BAG-MAT-907'],
 'S04':['Group A','SPA-MAT-0001','A-SHOE-MAT-118','B-SHOE-MAT-778'],
 'S05':['SPA-COMP-0101-B','SPA-MAT-0048','Factory A','Factory B'],
 'S06':['SPA-GRP-0001','120,000','180,000'],
 'S07':['SPA-MAT-0001','SPA-COMP-0101','BR-MAT-7781','FAC-M-2039'],
 'S08':['Supplier Vietnam','240,000','Net 60','2.00','SUP-A-991'],
 'S09':['Draft','Pending review','Approved','Published','editor-01','reviewer-01','publisher-01'],
 'S10':['identical','alternative','spu-01','sku-01','sku-02','20 days'],
 'S11':['sell back to supplier-01','transfer to factory-02','sell to factory-03','factory-01'],
 'S12':['qr-01','Batch A','Batch B','60% recycled','55% recycled','supplier-02'],
 'S13':['composition','recycled content','evidence-file','ready'],
 'S14':['authorized to partner-01','evidence-file','NOT authorized'],
 'S15':['supplier-code-new-01','unified-new-01','Published','brand-01','Save','Submit','Approve','Publish'],
 'S16':['brand-01','new material','not visible'],
 'S17':['5 stars','1 star','supplier-01','supplier-02','private'],
}

NODE = r"""
const fs=require('fs'), {JSDOM}=require('jsdom');
const file=process.argv[2]; const TOK=JSON.parse(process.argv[3]);
const html=fs.readFileSync(file,'utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,beforeParse(w){
  w.alert=()=>{};w.confirm=()=>true;w.prompt=()=>'';w.scrollTo=()=>{};w.open=()=>({focus(){}});
  w.matchMedia=w.matchMedia||(()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}}));
  if(w.Element){w.Element.prototype.scrollIntoView=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};}
}});
const {window}=dom, {document}=window;
setTimeout(()=>{
 const out={};
 try{
  if(typeof window.openScenarios!=='function'){ console.log(JSON.stringify({error:'no openScenarios'})); process.exit(0); }
  window.openScenarios();
  const vtext=()=>{ const v=document.getElementById('scnView'); return v?v.textContent:''; };
  for(const [id,tokens] of Object.entries(TOK)){
    const r={present:false,tokens_ok:true,missing:[],interactive:false};
    const btn=document.getElementById('scn-btn-'+id);
    r.present=!!btn;
    if(btn) btn.click(); else if(window.showScn) window.showScn(id);
    // 執行該場景所有可點互動（Select/Toggle/Step…），累積各狀態渲染文字（＝跑完 Demo interactions）
    let accum=vtext();
    for(let k=0;k<10;k++){
      const ctrls=[...document.querySelectorAll('#scnView .scn-ctrl')];
      if(!ctrls.length) break;
      const c=ctrls[k % ctrls.length];
      const b4=vtext(); c.click(); const af=vtext();
      accum += ' \n ' + af;
      if(af!==b4) r.interactive=true;
    }
    for(const t of tokens){ if(accum.indexOf(t)<0){ r.tokens_ok=false; r.missing.push(t); } }
    out[id]=r;
  }
 }catch(e){ out.__exc=e.message; }
 console.log(JSON.stringify(out));
 process.exit(0);
},400);
"""

def run(file):
    import tempfile
    js = os.path.join(ROOT, '_scn_probe.js')
    open(js, 'w', encoding='utf-8').write(NODE)
    try:
        p = subprocess.run(['node', js, file, json.dumps(SCN_TOKENS)], capture_output=True, text=True, timeout=60, cwd=ROOT)
        line = [l for l in p.stdout.strip().splitlines() if l.startswith('{')]
        return json.loads(line[-1]) if line else {'error': p.stderr[-300:] or 'no output'}
    finally:
        try: os.remove(js)
        except Exception: pass

def main():
    allok = True
    for f in FILES:
        name = os.path.basename(f)
        print(f"\n===== spec_gate_smartpn · {name} =====")
        res = run(f)
        if res.get('error') or res.get('__exc'):
            print(f"  ❌ harness: {res.get('error') or res.get('__exc')}"); allok = False; continue
        npass = 0
        for id in SCN_TOKENS:
            r = res.get(id, {})
            ok = r.get('present') and r.get('tokens_ok') and r.get('interactive')
            if ok: npass += 1
            else:
                det = []
                if not r.get('present'): det.append('無入口')
                if not r.get('tokens_ok'): det.append('缺token:'+','.join(r.get('missing',[])[:6]))
                if not r.get('interactive'): det.append('不可互動')
                print(f"  ❌ {id} — {'; '.join(det)}")
        for id in SCN_TOKENS:
            r = res.get(id, {})
            if r.get('present') and r.get('tokens_ok') and r.get('interactive'):
                print(f"  ✅ {id} 可點+資料齊+可互動")
        g = (npass == len(SCN_TOKENS))
        allok = allok and g
        print(f"  → {npass}/{len(SCN_TOKENS)} {'✅ ALL GREEN' if g else '❌ FAIL'}")
    print('\n'+'='*56)
    print(f"  spec_gate_smartpn: {'✅ ALL GREEN（%d 檔各 16/16）' % len(FILES) if allok else '❌ FAIL'}")
    print('='*56)
    sys.exit(0 if allok else 1)

if __name__ == '__main__':
    main()
