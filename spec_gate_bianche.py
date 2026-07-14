# -*- coding: utf-8 -*-
"""
spec_gate_bianche.py — 廠務編制表對「28_BIANCHE_SPEC.md」逐欄對帳閘門。
規格是唯一基準；驗收＝python spec_gate_bianche.py 全綠（+ hub_gate.py 全綠）。

用法：起一台有編制資料的隔離 server，例 atlas_v_e2e(合成鎖定版) @ 5098：
  SPEC_GATE_BASE=http://127.0.0.1:5098 python spec_gate_bianche.py
預設 BASE=http://127.0.0.1:5098。

對帳項（依 28 §一 區塊B/C）：
  B1 區塊B 12 欄齊全（鞋型/ART|訂單|裁斷|針車|成型|协理给|合計|編制|外移P|外移Q|外移R|C2B）
  B2 合計 L = SUM(H:K) = 裁斷+針車+成型+协理给
  B3 C2B  T = L + 外移P + 外移Q + 外移R
  B4 每 LEAN 有 直工小計 N(=SUM 編制) 與 人力小計 P(=SUM C2B)
  C1 區塊C 月度 11 項齊全（N2–N12）
  C2 月度公式：预计总工时 N6 = N4*N5（预计直工数×平均上班时数）
  D1 DS-04 匯入端點存在且不 500（缺檔→4xx）
"""
import os, sys, io, json, urllib.request, urllib.error, http.cookiejar
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.environ.get('SPEC_GATE_BASE', 'http://127.0.0.1:5098')
MONTH = os.environ.get('SPEC_GATE_MONTH', '2026-06')

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def req(method, path, body=None, form=None):
    data=None; headers={}
    if body is not None: data=json.dumps(body).encode(); headers['Content-Type']='application/json'
    if form is not None: data=form
    r=urllib.request.Request(BASE+path, data=data, method=method, headers=headers)
    try:
        resp=op.open(r, timeout=30); return resp.status, resp.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e: return e.code, e.read().decode('utf-8','replace')
    except Exception as e: return -1, str(e)

R=[]
def rec(n, ok, d=''):
    R.append((n,ok)); print(f"  {'✅' if ok else '❌'} {n}"+(f" — {d}" if d and not ok else (f" — {d}" if d else '')))

def approxeq(a,b,tol=0.11): return abs((a or 0)-(b or 0))<=tol

def main():
    s,_=req('POST','/api/login',{'username':'jim','password':'admin123'})
    if s!=200: print(f'❌ 登入失敗 {s}（BASE={BASE}）'); sys.exit(2)

    s,body=req('GET',f'/api/bianzhi/detail?month={MONTH}')
    det=json.loads(body) if s==200 else {}
    leans=det.get('leans',[])
    models=[m for lg in leans for m in lg.get('models',[])]

    # B1 十二欄齊全
    NEED=['model_name','arts','qty','cutting','stitching','assembly','xieligei','total_k','bianzhi','p_ext','q_ext','r_ext','c2b']
    miss=set()
    for m in models[:200]:
        for k in NEED:
            if k not in m: miss.add(k)
    rec('B1 區塊B 12 欄齊全（含 协理给 xieligei）', not miss and len(models)>0, f'缺欄={sorted(miss)} models={len(models)}')

    # B2/B3 公式
    b2=b3=True; b2d=b3d=''
    dm=[m for m in models if m.get('has_locked') and m.get('total_k') is not None]
    for m in dm:
        L=round((m['cutting'] or 0)+(m['stitching'] or 0)+(m['assembly'] or 0)+(m.get('xieligei') or 0),1)
        if not approxeq(L, m['total_k']): b2=False; b2d=f"{m['model_name']}: 合計{m['total_k']}≠{L}"; break
    for m in dm:
        T=round((m['total_k'] or 0)+(m['p_ext'] or 0)+(m['q_ext'] or 0)+(m['r_ext'] or 0),1)
        if not approxeq(T, m['c2b']): b3=False; b3d=f"{m['model_name']}: C2B{m['c2b']}≠{T}"; break
    rec('B2 合計 L = 裁斷+針車+成型+协理给', b2, b2d or f'驗 {len(dm)} 型體')
    rec('B3 C2B T = 合計+外移P+外移Q+外移R', b3, b3d or f'驗 {len(dm)} 型體')

    # B4 LEAN 小計
    b4=True; b4d=''
    for lg in leans:
        if 'total_bianzhi' not in lg or 'labor_subtotal' not in lg: b4=False; b4d=f"{lg['lean']}: 缺小計欄"; break
        n=round(sum((x['bianzhi'] or 0) for x in lg['models'] if x['bianzhi'] is not None),1)
        p=round(sum((x['c2b'] or 0) for x in lg['models'] if x['c2b'] is not None),1)
        if not approxeq(n, lg['total_bianzhi']) or not approxeq(p, lg['labor_subtotal']):
            b4=False; b4d=f"{lg['lean']}: N {lg['total_bianzhi']}/{n} P {lg['labor_subtotal']}/{p}"; break
    rec('B4 每 LEAN 直工小計 N(=SUM編制) + 人力小計 P(=SUM C2B)', b4 and len(leans)>0, b4d or f'{len(leans)} LEAN 組')

    # C1/C2 月度
    s,body=req('GET',f'/api/bianzhi/summary?month={MONTH}')
    summ=json.loads(body) if s==200 else {}
    mon=summ.get('monthly',{})
    NEED_M=['total_qty','avg_lc','direct_planned','working_hours','total_manhours','external_hours','deduct_hours','planned_eff','target80_direct','actual_direct','actual_eff']
    missm=[k for k in NEED_M if k not in mon]
    rec('C1 區塊C 月度 11 項齊全（N2–N12）', not missm and len(mon)>=11, f'缺={missm}')
    tm=mon.get('total_manhours'); dp=mon.get('direct_planned'); wh=mon.get('working_hours')
    c2ok = (tm is None) or approxeq(tm, round((dp or 0)*(wh or 0),1), tol=1.0)
    rec('C2 预计总工时 N6 = 预计直工数 × 平均上班时数', c2ok, f'N6={tm} vs N4×N5={round((dp or 0)*(wh or 0),1)}')

    # D1 DS-04 匯入端點（缺檔不 500）
    s,_=req('POST','/api/bianche/import_manual', body={})
    rec('D1 DS-04 匯入端點存在且不 500（缺檔→4xx）', s not in (500,-1) and 400<=s<500, f'status={s}')

    npass=sum(1 for _,ok in R if ok)
    print('\n'+'='*56)
    print(f'  spec_gate_bianche: {npass}/{len(R)} → {"✅ ALL GREEN" if npass==len(R) else "❌ FAIL"}')
    print('='*56)
    sys.exit(0 if npass==len(R) else 1)

if __name__=='__main__':
    print(f'===== spec_gate_bianche · BASE={BASE} month={MONTH} =====')
    main()
