# -*- coding: utf-8 -*-
"""
Task T 驗收：功能權限矩陣（帳號×單元；帳號管理頁維護；admin 不受限；遷移零變化；雙層 403）。

環境（隔離）：serve_test_isolated.py → http://127.0.0.1:5099（atlas_test.db 一致性副本）。
用法：先啟動隔離 server，再  py test_task_t_matrix.py

驗收：
  1. 造「只勾撥人」帳號 → /api/me/units=={allocate}；硬打其他 6 單元 API → 403；撥人 → 非 403。
  2. 現有角色行為零變化（admin 全過、manager 審核/基礎資料過+IE編輯擋、editor 指派可編、read_only 全擋）。
  3. 帳號管理頁矩陣 UI：勾選→存→重載一致。
"""
import sys, io, os, sqlite3, hashlib, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"
HID  = 5
PROC_H5 = 16269                       # header 5 的一個 ie_process id（IE編輯測試用）
DBP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "flask_backend", "data", "test_isolated", "atlas_test.db")
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "flask_backend", "test_output", "task_t_shots")
os.makedirs(SHOT, exist_ok=True)

RESULTS = []
def rec(t, ok, d=""):
    RESULTS.append((t, ok)); print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {t}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)

def dbexec(sql, p=()):
    c = sqlite3.connect(DBP, timeout=15)
    try: c.execute("PRAGMA busy_timeout=15000"); c.execute(sql, p); c.commit()
    finally: c.close()
def dbq(sql, p=(), one=False):
    c = sqlite3.connect(DBP, timeout=15); c.row_factory = sqlite3.Row
    try:
        rows=[dict(r) for r in c.execute(sql,p).fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally: c.close()

ACCTS = {"t_bo":"t123", "t_editor":"t123", "t_mgr":"t123"}
def setup():
    for uname, pw in ACCTS.items():
        role = {"t_bo":"read_only","t_editor":"data_entry","t_mgr":"manager"}[uname]
        h = hashlib.sha256(pw.encode()).hexdigest()
        dbexec("INSERT OR IGNORE INTO sys_users (username,display_name,role,password_hash,active,locked,created_at,updated_at) "
               "VALUES (?,?,?,?,1,0,datetime('now'),datetime('now'))", (uname, uname, role, h))
    uid = dbq("SELECT id FROM sys_users WHERE username='t_editor'", one=True)["id"]
    dbexec("INSERT OR IGNORE INTO ie_assignments (header_id,user_id) VALUES (?,?)", (HID, uid))
def cleanup():
    for uname in ACCTS:
        row = dbq("SELECT id FROM sys_users WHERE username=?", (uname,), one=True)
        if row:
            dbexec("DELETE FROM ie_assignments WHERE user_id=?", (row["id"],))
            dbexec("DELETE FROM sys_users WHERE id=?", (row["id"],))


def main():
    setup()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        api = ctx.request

        def login(u, p):
            r = api.post(f"{BASE}/api/login", data=json.dumps({"username":u,"password":p}),
                         headers={"Content-Type":"application/json"})
            return r.ok

        # 單元 → 代表端點（method, path, body）
        def hit(unit):
            m = {
              'ie_edit':   ('POST', '/api/ie/cell/save', {"cell_id":PROC_H5,"field":"process_name","value":"x","stage_id":None}),
              'select_parts':('POST','/api/allocation/check', {"id":1,"is_checked":True}),
              'allocate':  ('GET',  '/api/allocation/parts', None),
              'import':    ('POST', '/api/ie/import/apply', {"target_header_id":HID,"source_header_id":1,"segment":"cutting","zone":"z"}),
              'export':    ('GET',  '/api/ie/export/capacity', None),
              'audit':     ('GET',  '/api/ie/review/queue', None),
              'base_data': ('POST', '/api/equipment_types', {"name":"__t_probe__","sort_order":0}),
            }[unit]
            method, path, body = m
            if method=='GET':
                return api.get(f"{BASE}{path}")
            return api.post(f"{BASE}{path}", data=json.dumps(body or {}), headers={"Content-Type":"application/json"})

        # ══ 建「只勾撥人」帳號：以 jim 設定矩陣 ══
        try:
            login("jim","admin123")
            uid = dbq("SELECT id FROM sys_users WHERE username='t_bo'", one=True)["id"]
            r = api.put(f"{BASE}/api/users/{uid}/permissions",
                        data=json.dumps({"units":["allocate"]}), headers={"Content-Type":"application/json"})
            set_ok = r.ok and r.json().get("ok")
            rec("以 admin 設定 t_bo 矩陣={allocate}", bool(set_ok), f"resp={r.status} {r.text()[:120]}")
        except Exception as e:
            rec("設定 t_bo 矩陣", False, f"EXC {e}")

        # ══ 1) t_bo /api/me/units == {allocate} ══
        try:
            login("t_bo","t123")
            r = api.get(f"{BASE}/api/me/units"); j = r.json()
            units = sorted(j.get("units", []))
            rec("只勾撥人帳號 /api/me/units == ['allocate']", units==["allocate"], f"units={units}")
        except Exception as e:
            rec("t_bo units", False, f"EXC {e}")

        # ══ 2) t_bo 硬打其他 6 單元 → 403；撥人 → 非 403 ══
        try:
            login("t_bo","t123")
            statuses = {u: hit(u).status for u in ['ie_edit','select_parts','import','export','audit','base_data','allocate']}
            others_403 = all(statuses[u]==403 for u in ['ie_edit','select_parts','import','export','audit','base_data'])
            allocate_ok = statuses['allocate'] != 403
            rec("只勾撥人帳號：其他 6 單元 API=403 且撥人≠403", others_403 and allocate_ok,
                "\n".join(f"{u}={s}" for u,s in statuses.items()))
        except Exception as e:
            rec("t_bo 硬打 API", False, f"EXC {e}")

        # ══ 3) admin(jim) 全部非 403（不受矩陣限） ══
        try:
            login("jim","admin123")
            st = {u: hit(u).status for u in ['ie_edit','import','export','audit','base_data','allocate']}
            # base_data 造了 __t_probe__，清掉
            dbexec("DELETE FROM equipment_types WHERE name='__t_probe__'")
            all_ok = all(v!=403 for v in st.values())
            rec("admin 不受矩陣限：代表端點皆非 403", all_ok, "\n".join(f"{u}={s}" for u,s in st.items()))
        except Exception as e:
            rec("admin 全過", False, f"EXC {e}")

        # ══ 4) manager 零變化：審核/基礎資料 非403、IE編輯 403、導出 非403 ══
        try:
            login("t_mgr","t123")
            s_audit = hit('audit').status
            s_base  = hit('base_data').status; dbexec("DELETE FROM equipment_types WHERE name='__t_probe__'")
            s_ie    = hit('ie_edit').status
            s_exp   = hit('export').status
            ok = (s_audit!=403 and s_base!=403 and s_ie==403 and s_exp!=403)
            rec("manager 零變化（審核/基礎資料/導出過、IE編輯擋）", ok,
                f"audit={s_audit} base_data={s_base} ie_edit={s_ie}(期望403) export={s_exp}")
        except Exception as e:
            rec("manager 零變化", False, f"EXC {e}")

        # ══ 5) editor(data_entry, 指派HID5) 零變化：IE編輯 非403、審核 403、導出 403 ══
        try:
            login("t_editor","t123")
            s_ie   = hit('ie_edit').status         # 指派 → 可編
            s_aud  = hit('audit').status           # 非manager → 403
            s_exp  = hit('export').status          # 非manager → 403
            ok = (s_ie!=403 and s_aud==403 and s_exp==403)
            rec("editor 零變化（指派可 IE編輯、審核/導出擋）", ok,
                f"ie_edit={s_ie}(期望≠403) audit={s_aud}(403) export={s_exp}(403)")
        except Exception as e:
            rec("editor 零變化", False, f"EXC {e}")

        # ══ 6) read_only(tongcai) 零變化：閘門單元全 403；撥人(有alloc身分)非403 ══
        try:
            login("tongcai","x")
            s_ie   = hit('ie_edit').status
            s_exp  = hit('export').status
            s_aud  = hit('audit').status
            s_alloc= hit('allocate').status        # tongcai 有 alloc 身分 → 非403（零迴歸）
            ok = (s_ie==403 and s_exp==403 and s_aud==403 and s_alloc!=403)
            rec("read_only(tongcai) 零變化（閘門單元403、撥人非403）", ok,
                f"ie_edit={s_ie} export={s_exp} audit={s_aud} allocate={s_alloc}(期望≠403)")
        except Exception as e:
            rec("read_only 零變化", False, f"EXC {e}")

        # ══ 7) 帳號管理頁矩陣 UI：勾 import 存→重載一致 ══
        try:
            page = ctx.new_page(); page.on("dialog", lambda d: d.accept())
            page.goto(f"{BASE}/login", wait_until="domcontentloaded")
            page.fill("#username","jim"); page.fill("#password","admin123")
            page.click("#btnLogin"); page.wait_for_timeout(1000)
            page.goto(f"{BASE}/admin/users", wait_until="domcontentloaded")
            page.wait_for_selector("#tbody tr", timeout=6000)
            # 找 t_bo 列的「矩陣」鈕
            page.evaluate("""()=>{
              const rows=[...document.querySelectorAll('#tbody tr')];
              const tr=rows.find(r=>r.innerText.includes('t_bo'));
              tr.querySelector('button[onclick^=\"openPerm\"]').click();
            }""")
            page.wait_for_selector("#perm-modal.open", timeout=4000)
            page.check("#perm-import")
            page.click("button[onclick='savePerm()']")
            page.wait_for_timeout(900)
            shot = os.path.join(SHOT,"01_perm_saved.png")
            try: page.screenshot(path=shot)
            except: pass
            # 重載 API 驗證
            r = api.get(f"{BASE}/api/me/units")  # api still jim; check via list
            uid = dbq("SELECT id,permissions FROM sys_users WHERE username='t_bo'", one=True)
            perms = sorted(json.loads(uid["permissions"] or "[]"))
            ok = perms == ["allocate","import"]
            rec("帳號管理頁矩陣 UI：勾 import 存→DB 一致", ok, f"t_bo.permissions={perms}(期望 allocate+import)")
            page.close()
        except Exception as e:
            rec("矩陣 UI 存取一致", False, f"EXC {e}")

        browser.close()

    cleanup()
    print("\n"+"="*60)
    npass = sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS"); print("="*60)
    sys.exit(0 if npass==len(RESULTS) else 1)


if __name__ == "__main__":
    main()
