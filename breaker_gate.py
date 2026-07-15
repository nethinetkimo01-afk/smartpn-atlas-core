#!/usr/bin/env python3
# 破壞者閘門 breaker_gate.py — 立場:這系統一定有 bug,我的工作是弄壞它
# 不問「有沒有」,只問「弄不弄得壞」。攻擊:並發/壞資料/邊界/權限繞過/狀態殘留
import sys, json, threading, io, time
import urllib.request as U, http.cookiejar as CJ
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5097'
BUGS = []
def bug(name, evidence):
    print('🔴 BUG |', name, '|', evidence); BUGS.append((name, evidence))
def ok(name):
    print('🟢 擋住 |', name)

def client():
    jar = CJ.CookieJar(); return U.build_opener(U.HTTPCookieProcessor(jar))
def req(op, method, path, body=None, raw=None, ctype='application/json', timeout=20):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r = U.Request(BASE+path, data=data, method=method)
    if data is not None: r.add_header('Content-Type', ctype)
    try:
        with op.open(r, timeout=timeout) as x: return x.getcode(), x.read()[:300]
    except U.HTTPError as e: return e.code, e.read()[:300]
    except Exception as e: return -1, str(e).encode()
def login(u, p):
    op = client(); c, _ = req(op, 'POST', '/api/login', {'username': u, 'password': p})
    return op if c == 200 else None

sys.path.insert(0, 'flask_backend')
import database as db
for u, r in [('brk_admin','admin'),('brk_ro','read_only')]:
    db.create_user(u, 'breaker', r, 'brk-'+u)
admin = login('brk_admin', 'brk-brk_admin')
ro = login('brk_ro', 'brk-brk_ro')
if not admin: print('無法登入'); sys.exit(1)

print('=== 破壞者開始攻擊 ===')

# 攻擊1:並發相同寫入(匯入/重算)——會不會互相蓋、撞檔、雙重執行
def concurrent(path, body, n=5):
    codes = []; lock = threading.Lock()
    def hit():
        c, _ = req(admin, 'POST', path, body)
        with lock: codes.append(c)
    ts = [threading.Thread(target=hit) for _ in range(n)]
    [t.start() for t in ts]; [t.join() for t in ts]
    return codes
codes = concurrent('/api/recalc/cutting/apply', {'confirm': True})
if codes.count(200) > 1: bug('重算並發:多個200(雙重執行)', 'codes=%s' % codes)
else: ok('重算並發鎖')

# 攻擊2:壞資料/邊界參數 → 不得 500
JUNK = ['?month=', '?month=9999-99', "?month='OR'1", '?month=<script>', '?id=-1',
        '?id=99999999999', '?eolr=abc', '?eolr=-60', '?limit=1e9']
apis = ['/api/bianzhi/summary', '/api/bianzhi/detail', '/api/bianche',
        '/api/ds04/lock', '/api/eolr-settings', '/api/bianzhi/flow_state']
boom = []
for a in apis:
    for j in JUNK:
        c, b = req(admin, 'GET', a+j)
        if c >= 500: boom.append('%s%s→%d' % (a, j, c))
if boom: bug('壞參數造成500', '; '.join(boom[:6]))
else: ok('壞參數全部4xx不500')

# 攻擊3:權限繞過 — read_only 硬打寫入端點
leak = []
WRITES = [('POST','/api/ds04/import'),('POST','/api/ds04/order'),
          ('POST','/api/ds04/lock'),('POST','/api/eolr-settings'),
          ('POST','/api/recalc/cutting/apply'),('POST','/api/ie/import/apply')]
if ro:
    for m, p in WRITES:
        c, _ = req(ro, m, p, {})
        if c == 200: leak.append('%s %s' % (m, p))
if leak: bug('read_only 越權寫入成功', '; '.join(leak))
else: ok('read_only 全部寫入被擋')

# 攻擊4:壞xlsx匯入 — 半截檔/空檔/非xlsx 不得500、不得半匯入
def multipart(fields):
    boundary = '----brk'; body = io.BytesIO()
    for name, (fname, content) in fields.items():
        body.write(('--%s\r\n' % boundary).encode())
        body.write(('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (name, fname)).encode())
        body.write(b'Content-Type: application/octet-stream\r\n\r\n')
        body.write(content if isinstance(content, bytes) else content.encode())
        body.write(b'\r\n')
    body.write(('--%s--\r\n' % boundary).encode())
    return body.getvalue(), 'multipart/form-data; boundary=%s' % boundary
for label, content in [('半截檔', b'PK\x03\x04broken'), ('空檔', b''), ('非xlsx', b'hello world')]:
    raw, ct = multipart({'file': ('x.xlsx', content)})
    c, b = req(admin, 'POST', '/api/ds04/import', raw=raw, ctype=ct)
    if c >= 500: bug('壞xlsx匯入造成500(%s)' % label, 'code=%d' % c)
    else: ok('壞xlsx擋下(%s)→%d' % (label, c))

# 攻擊5:狀態殘留 — 連續切月份/版本後,summary 是否串味
c1, b1 = req(admin, 'GET', '/api/bianzhi/summary?month=2026-06')
c2, b2 = req(admin, 'GET', '/api/bianzhi/summary?month=2026-99')  # 不存在月
c3, b3 = req(admin, 'GET', '/api/bianzhi/summary?month=2026-06')
if c1 == 200 and c3 == 200 and b1 != b3:
    bug('狀態殘留:切壞月份後同月結果改變', 'b1!=b3')
else: ok('無狀態殘留(切月份後同月結果一致)')

print('\n=== 破壞者總結:', '攻破 %d 處' % len(BUGS) if BUGS else '全部擋住,攻不破', '===')
for n, e in BUGS: print('  BUG:', n, '—', e)
sys.exit(1 if BUGS else 0)
