# -*- coding: utf-8 -*-
"""
spec_gate_import.py — Task IMP-FIX：DS-04 匯入壓力/容錯閘門（隔離副本，絕不碰正式庫）。

抓的是「有時能有時不能、失敗居多」那類間歇性缺陷——單發成功不代表沒事，必須壓並發/重複/變異/壞檔：
  1 併發：同時 5 個匯入 → 全部成功或明確排隊(409 匯入進行中)，不得有人因撞暫存檔而解析失敗
  2 重複：同一檔連續匯入 10 次 → 10 次全成功（舊版固定暫存檔會間歇失敗）
  3 表頭變異：中文 / 帶空白 / 全形 / 英文別名 表頭都要能匯入
  4 壞檔：空檔 / 半截檔 / 非 xlsx → 明確錯誤訊息、不得 500、不得留半匯入狀態
  5 原子：壞資料列(數量非數字) → 明確錯誤含行號，且 DB 筆數不變（一列都不准進去）

用法：SPEC_GATE_IMPORT_BASE=http://127.0.0.1:5095 python spec_gate_import.py
"""
import os, sys, io, json, threading, urllib.request, urllib.error, http.cookiejar, mimetypes, uuid

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = os.environ.get('SPEC_GATE_IMPORT_BASE', 'http://127.0.0.1:5095')
R = []


def jbody(b):
    r"""Flask 回的 JSON 中文是 \uXXXX 轉義 → 必須解碼後再比對（不可對原始字串做子字串比對）。"""
    try: return json.loads(b)
    except Exception: return {}


def jok(b):
    return jbody(b).get('ok') is True


def jerr(b):
    return str(jbody(b).get('error', ''))


def rec(n, ok, d=''):
    R.append((n, ok))
    print(f"  {'✅' if ok else '❌'} {n}" + (f" — {d}" if d else ''))


class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def login(self, u, p):
        body = json.dumps({'username': u, 'password': p}).encode()
        r = urllib.request.Request(BASE + '/api/login', data=body, method='POST',
                                   headers={'Content-Type': 'application/json'})
        try:
            return self.op.open(r, timeout=20).status
        except urllib.error.HTTPError as e:
            return e.code

    def upload(self, blob, filename='ds04.xlsx'):
        boundary = '----gate' + uuid.uuid4().hex
        body = b''
        body += ('--%s\r\n' % boundary).encode()
        body += ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode()
        body += b'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'
        body += blob + b'\r\n'
        body += ('--%s--\r\n' % boundary).encode()
        r = urllib.request.Request(BASE + '/api/ds04/import', data=body, method='POST',
                                   headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
        try:
            resp = self.op.open(r, timeout=120)
            return resp.status, resp.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')
        except Exception as e:
            return -1, str(e)

    def get(self, path):
        try:
            resp = self.op.open(urllib.request.Request(BASE + path), timeout=30)
            return resp.status, resp.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')
        except Exception as e:
            return -1, str(e)


def xlsx(headers, rows):
    """產生 xlsx bytes（記憶體內，不落地）。"""
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(list(headers))
    for r in rows:
        ws.append(list(r))
    bio = io.BytesIO(); wb.save(bio)
    return bio.getvalue()


ROWS = [['CSA', 'L1', 'ADIPOWER 26 SL', 'ART-001', 'PO-1001', 120, '2026-08-01', 'N'],
        ['CSA', 'L2', 'LA TRAINER', 'ART-002', 'PO-1002', 80, '2026-08-05', 'Y']]
ZH = ['部門', 'LEAN', '鞋型名稱', 'ART', '訂單號', '數量', '交期', '外包鞋面']


def count_orders(c):
    s, b = c.get('/api/ds04/orders?month=2026-08')
    try:
        d = json.loads(b)
        v = d.get('orders', d if isinstance(d, list) else [])
        return len(v) if isinstance(v, list) else -1
    except Exception:
        return -1


def main():
    c = Client()
    st = c.login('jim', 'admin123')
    if st not in (200, 302):
        rec('登入 jim(manager+)', False, f'HTTP {st}'); return finish()

    base_ok = xlsx(ZH, ROWS)

    # ── 1 重複匯入同檔 10 次（舊版固定暫存檔 → 間歇失敗）──
    fails = []
    for i in range(10):
        s, b = c.upload(base_ok)
        ok = (s == 200 and jok(b))
        if not ok: fails.append(f'#{i+1} HTTP{s} {b[:80]}')
    rec('重複匯入同一檔 10 次 → 10 次全成功', not fails, f'失敗 {len(fails)}/10' + ('　→ ' + '; '.join(fails[:3]) if fails else ''))

    # ── 2 併發 5 個匯入 → 全成功或明確排隊(409)，不得撞檔解析失敗 ──
    res = []
    lock = threading.Lock()

    def worker():
        cc = Client(); cc.login('jim', 'admin123')
        s, b = cc.upload(base_ok)
        with lock: res.append((s, b))
    ths = [threading.Thread(target=worker) for _ in range(5)]
    for t in ths: t.start()
    for t in ths: t.join()
    bad = []
    for s, b in res:
        if s == 200 and jok(b):
            continue
        if s == 409 and ('匯入進行中' in jerr(b)):
            continue                       # 明確排隊＝可接受
        bad.append(f'HTTP{s} {b[:90]}')
    n_ok = sum(1 for s, b in res if s == 200)
    n_q = sum(1 for s, b in res if s == 409)
    rec('併發 5 個匯入 → 全部成功或明確排隊(409 匯入進行中)，無撞檔失敗',
        not bad, f'成功={n_ok} 排隊={n_q} 異常={len(bad)}' + ('　→ ' + '; '.join(bad[:3]) if bad else ''))

    # ── 3 表頭變異：帶空白 / 全形 / 英文別名 ──
    variants = [
        ('帶空白', [' 部門 ', ' LEAN ', ' 鞋型名稱 ', ' ART ', ' 訂單號 ', ' 數量 ', ' 交期 ', ' 外包鞋面 ']),
        ('全形',   ['部門', 'ＬＥＡＮ', '鞋型名稱', 'ＡＲＴ', '訂單號', '數量', '交期', '外包鞋面']),
        ('英文別名', ['dept', 'lean', 'model', 'art', 'order no', 'qty', 'delivery', 'outsource']),
        ('大小寫混合', ['Dept', 'Lean', 'Model Name', 'Art', 'OrderNo', 'PCS', 'Due Date', 'Outsource']),
    ]
    vbad = []
    for name, hdr in variants:
        s, b = c.upload(xlsx(hdr, ROWS))
        if not (s == 200 and jok(b)):
            vbad.append(f'{name}: HTTP{s} {b[:70]}')
    rec('表頭變異（中文/帶空白/全形/英文別名/大小寫）皆可匯入', not vbad,
        f'失敗 {len(vbad)}/{len(variants)}' + ('　→ ' + '; '.join(vbad) if vbad else ''))

    # ── 4 壞檔：空檔 / 半截檔 / 非 xlsx → 明確錯誤、不 500 ──
    before = count_orders(c)
    bads = [('空檔', b''), ('半截檔', base_ok[:len(base_ok) // 3]), ('非xlsx（純文字）', b'this is not an excel file')]
    bbad = []
    for name, blob in bads:
        s, b = c.upload(blob)
        if s == 500 or s == -1:
            bbad.append(f'{name}: HTTP{s}（不得 500）')
        elif jok(b):
            bbad.append(f'{name}: 竟然成功了')
    after = count_orders(c)
    rec('壞檔（空檔/半截檔/非xlsx）→ 明確錯誤、不 500', not bbad,
        f'異常 {len(bbad)}' + ('　→ ' + '; '.join(bbad) if bbad else ''))
    rec('壞檔不留半匯入狀態（DB 筆數不變）', before == after and before >= 0, f'匯入前={before} 匯入後={after}')

    # ── 5 原子：壞資料列 → 明確錯誤含行號，DB 一列都不動 ──
    b0 = count_orders(c)
    bad_rows = [['CSA', 'L1', 'M', 'A1', 'PO-1', 100, '2026-08-01', 'N'],
                ['CSA', 'L2', 'M', 'A2', 'PO-2', 'abc', '2026-08-02', 'N']]   # 第 3 列數量非數字
    s, b = c.upload(xlsx(ZH, bad_rows))
    has_row = ('第 3 列' in jerr(b))
    b1 = count_orders(c)
    rec('壞資料列（數量非數字）→ 明確錯誤含行號，且 DB 一列都沒進去（原子）',
        s != 500 and not jok(b) and has_row and b0 == b1,
        f'HTTP{s} 含行號={has_row} 筆數 {b0}→{b1}；訊息={jerr(b)[:60]}')

    finish()


def finish():
    npass = sum(1 for _, ok in R if ok)
    print('\n' + '=' * 60)
    print(f'  spec_gate_import: {npass}/{len(R)} → {"✅ ALL GREEN" if npass == len(R) else "❌ FAIL"}')
    print('=' * 60)
    sys.exit(0 if npass == len(R) and R else 1)


if __name__ == '__main__':
    print(f'===== spec_gate_import（DS-04 匯入壓力/容錯）· BASE={BASE} =====')
    main()
