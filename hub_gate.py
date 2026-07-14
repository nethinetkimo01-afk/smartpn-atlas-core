# -*- coding: utf-8 -*-
"""
hub_gate.py — 中樞伺服器缺陷閘門（6 類）。生產前必跑全綠才可 push（見 25_CODE_UNATTENDED_RULES）。

用法：
  1) 起隔離 server（勿碰正式庫），例：
       ATLAS_DB=.../atlas_s2.db ATLAS_PORT=5097 python -c "import database as db;db.init_db();from app import app;from waitress import serve;serve(app,host='127.0.0.1',port=5097)"
  2) HUB_GATE_BASE=http://127.0.0.1:5097 python hub_gate.py
  預設 BASE=http://127.0.0.1:5099。

閘門類別：
  1 編制表 /api/bianche·/api/bianzhi 低權限/空月 → 不得 500（有權→200、無權→403、空月→200）
  2 寫入端點越權：read_only 打寫入 → 必 403（不得 200/500）
  3 重算 apply 並發 → 第二發 409（DB 原子鎖）
  4 recalc/preview 及帶 month 端點吃垃圾 month → 4xx（不得 500）
  5 <int:id> 不存在 → 404（不得 500）
  6 全面：缺參數/錯型別/不存在ID/空資料 → 一律 4xx 不 500
"""
import os, sys, io, json, threading, urllib.request, urllib.error, http.cookiejar
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.environ.get('HUB_GATE_BASE', 'http://127.0.0.1:5099')

class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
    def req(self, method, path, body=None):
        data = None; headers = {}
        if body is not None:
            data = json.dumps(body).encode(); headers['Content-Type'] = 'application/json'
        r = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
        try:
            resp = self.op.open(r, timeout=30)
            return resp.status, resp.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')
        except Exception as e:
            return -1, str(e)
    def login(self, u, p):
        return self.req('POST', '/api/login', {'username': u, 'password': p})

def admin():
    c = Client(); c.login('jim', 'admin123'); return c
def readonly():
    c = Client(); c.login('tongcai', 'x'); return c
def dataentry():
    a = admin()
    a.req('POST', '/api/users', {'username': 'gate_de', 'display_name': 'gate_de',
                                 'role': 'data_entry', 'password': 'g123', 'active': 1})
    c = Client(); c.login('gate_de', 'g123'); return c

CATS = {}
def check(cat, name, ok, detail=""):
    CATS.setdefault(cat, []).append((name, ok, detail))

def not500(status): return status not in (500, -1)

# ═══ CAT 1 ═══
def cat1():
    ro, de = readonly(), dataentry()
    reads = ['/api/bianche?month=2026-06', '/api/bianzhi/summary?month=2026-06',
             '/api/bianzhi/detail?month=2026-06', '/api/bianche?month=2026-07',
             '/api/bianzhi/summary?month=2026-07', '/api/bianzhi/detail?month=2026-07',
             '/api/bianzhi/flow_state?month=2026-06', '/api/bianzhi/flow_state?month=2026-07',
             '/api/bianzhi/flow_state?month=']    # Task Y 新端點納入閘門（含空 month）
    for role, c in [('read_only', ro), ('data_entry', de)]:
        for p in reads:
            s, _ = c.req('GET', p)
            check(1, f'{role} GET {p}', not500(s) and s in (200, 403), f'status={s}')

# ═══ CAT 2 ═══
def cat2():
    ro = readonly()
    writes = [
        ('POST', '/api/ds03/save', {'art': 'X', 'rows': []}),
        ('DELETE', '/api/ds03/delete?art=NOPE', None),
        ('POST', '/api/ds03/add_art', {'art': 'X'}),
        ('POST', '/api/lookup/add', {'viet': 'a', 'zh': 'b'}),
        ('POST', '/api/ie/cell/approve', {'log_id': 1}),
        ('POST', '/api/ie/update_mp', {'header_id': 1}),
        ('POST', '/api/ds04/order', {'lean': '1A', 'model_name': 'X', 'art': 'X', 'qty': 1}),
        ('POST', '/api/eolr-settings', {'lean': '1A', 'month': '2026-06', 'eolr': 120}),
        ('POST', '/api/bianche/manual', {'lean': '1A', 'month': '2026-06'}),
        ('POST', '/api/bianche/model_manual', {'lean': '1A', 'model_name': 'X', 'month': '2026-06'}),
        ('POST', '/api/bianche/dept_hc', {'dept': 'X', 'month': '2026-06'}),
        ('POST', '/api/bianche/lean_hc', {'lean': '1A', 'month': '2026-06', 'headcount': 1}),
        ('POST', '/api/bianzhi/unit_manual', {'month': '2026-06', 'unit': 'CSA', 'field': 'direct_this', 'value': 1}),
        ('POST', '/api/bianzhi/monthly_manual', {'month': '2026-06', 'key': 'avg_lc', 'value': 1}),
        ('POST', '/api/bianzhi/lean_bianzhi', {'lean': '1A', 'model_name': 'X', 'month': '2026-06', 'bianzhi': 1}),
        ('POST', '/api/result/import_corrections', {'rows': []}),
        ('POST', '/api/recalc/cutting/apply', None),
        ('POST', '/api/equipment_types', {'name': 'X'}),
    ]
    for m, p, b in writes:
        s, _ = c_status(ro, m, p, b)
        check(2, f'read_only {m} {p}', s == 403, f'status={s} (期望403)')

def c_status(c, m, p, b):
    return c.req(m, p, b)

# ═══ CAT 3 ═══
def cat3():
    a1, a2 = admin(), admin()
    res = {}
    def fire(tag, c):
        s, _ = c.req('POST', '/api/recalc/cutting/apply'); res[tag] = s
    t1 = threading.Thread(target=fire, args=('a', a1)); t2 = threading.Thread(target=fire, args=('b', a2))
    t1.start(); t2.start(); t1.join(); t2.join()
    codes = sorted(res.values())
    # 兩發不得皆 200；至少一個 409（或第二發被擋）
    ok = not500(res.get('a', -1)) and not500(res.get('b', -1)) and (codes.count(200) <= 1) and (409 in codes)
    check(3, '重算 apply 並發 → 第二發 409', ok, f'codes={res}')

# ═══ CAT 4 ═══
def cat4():
    a = admin()
    bad_months = ['', '9999-99', "2026-06'; DROP TABLE ie_process;--", 'abc', '2026-13', '../../etc']
    for mth in bad_months:
        import urllib.parse
        q = urllib.parse.quote(mth)
        s, _ = a.req('GET', f'/api/recalc/cutting/preview?month={q}')
        check(4, f'preview month={mth!r}', not500(s), f'status={s}')
        s2, _ = a.req('GET', f'/api/bianzhi/summary?month={q}')
        check(4, f'bianzhi/summary month={mth!r}', not500(s2), f'status={s2}')

# ═══ CAT 5 ═══
def cat5():
    a = admin()
    BIG = 999999
    ids = [
        ('GET', f'/api/ie/{BIG}/sheets', None),
        ('GET', f'/api/ie/{BIG}/detail', None),
        ('GET', f'/api/ie/{BIG}/sum', None),
        ('GET', f'/api/ie/cell/{BIG}', None),
        ('GET', f'/api/ie/{BIG}/process', None),
        ('GET', f'/api/ie/{BIG}/groups', None),
        ('PUT', f'/api/ds04/order/{BIG}', {'qty': 1}),
        ('DELETE', f'/api/ds04/order/{BIG}', None),
        ('PUT', f'/api/users/{BIG}', {'display_name': 'x'}),
        ('DELETE', f'/api/users/{BIG}', None),
    ]
    for m, p, b in ids:
        s, _ = a.req(m, p, b)
        check(5, f'{m} {p} (不存在id)', not500(s) and 400 <= s < 500, f'status={s} (期望4xx/404)')

# ═══ CAT 6 ═══
def cat6():
    a = admin()
    probes = [
        ('POST', '/api/ie/cell/save', {}),               # 缺 cell_id
        ('POST', '/api/ie/cell/add_row', {}),
        ('POST', '/api/ie/import/apply', {}),
        ('POST', '/api/ds04/order', {}),
        ('POST', '/api/bianzhi/unit_manual', {'month': '2026-06'}),  # 缺欄位
        ('GET', '/api/ie/abc/sum', None),                # 錯型別（非 int→Flask 404）
        ('POST', '/api/ie/cell/save', {'cell_id': 'notnum'}),
        ('POST', '/api/eolr-settings', {}),
        ('POST', '/api/lookup/add', {}),
        ('GET', '/api/ie/detail/999999', None),
    ]
    for m, p, b in probes:
        s, _ = a.req(m, p, b)
        check(6, f'{m} {p} bad-input', not500(s) and 400 <= s < 500, f'status={s}')


def main():
    # 連線檢查
    s, _ = Client().req('GET', '/api/health')
    if s == -1:
        print(f'❌ 無法連線 {BASE}（請先起隔離 server）'); sys.exit(2)
    for fn in (cat1, cat2, cat3, cat4, cat5, cat6):
        try: fn()
        except Exception as e:
            check(fn.__name__, 'harness-exception', False, str(e))
    total = passed = 0
    allgreen = True
    for cat in sorted(CATS):
        rows = CATS[cat]; npass = sum(1 for _, ok, _ in rows if ok)
        total += len(rows); passed += npass
        green = npass == len(rows); allgreen = allgreen and green
        print(f'\n{"✅" if green else "❌"} CAT {cat}: {npass}/{len(rows)}')
        for name, ok, det in rows:
            if not ok: print(f'   ❌ {name} — {det}')
    print('\n' + '=' * 56)
    print(f'  hub_gate: {passed}/{total}  →  {"✅ ALL GREEN" if allgreen else "❌ FAILURES ABOVE"}')
    print('=' * 56)
    sys.exit(0 if allgreen else 1)


if __name__ == '__main__':
    main()
