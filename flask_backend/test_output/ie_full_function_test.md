# IE 系統功能 + 資料正確性 測試報告

**執行時間**: 2026-06-19 16:41:44  
**測試庫**: tests/atlas_test.db (複製自 data/atlas.db)
**資料規模**: 152 headers | 20434 ie_process | 0 ie_sheet_data

---

## Section A — 功能模擬（全角色 × 正反向）

**結果**: 31 PASS / 0 FAIL（共 31 項）

| # | 測試項目 | 結果 | 備註 |
|---|----------|------|------|
| A01 | 未登入 / → redirect /login | ✅ PASS | got 302 location=/login |
| A01 | 未登入 /ie → redirect /login | ✅ PASS | got 302 location=/login |
| A01 | 未登入 /ie/1/detail → redirect /login | ✅ PASS | got 302 location=/login |
| A02 | 未登入 /api/ie/list → 401 | ✅ PASS | got 401 |
| A03 | 未登入寫入API → 401 | ✅ PASS | got 401 |
| A04 | admin 登入成功 | ✅ PASS |  |
| A05 | test_admin /api/ie/list → 77 筆 | ✅ PASS | status=200 |
| A05 | test_manager /api/ie/list → 77 筆 | ✅ PASS | status=200 |
| A05 | test_de /api/ie/list → 77 筆 | ✅ PASS | status=200 |
| A05 | test_ro /api/ie/list → 77 筆 | ✅ PASS | status=200 |
| A06 | test_admin add_row → 200+ok | ✅ PASS | got 200, ok=True |
| A06 | test_manager add_row → 200+ok | ✅ PASS | got 200, ok=True |
| A07 | read_only add_row → 403 | ✅ PASS | got 403 |
| A08 | data_entry(已指派) save → 200 | ✅ PASS | got 200 |
| A09 | data_entry(未指派B) save → 403 | ✅ PASS | got 403 |
| A10 | data_entry can_edit(B) → false | ✅ PASS | got 200, can_edit=False |
| A11 | data_entry can_edit(A) → true | ✅ PASS | got 200, can_edit=True |
| A12 | admin add_row → delete_row → ok | ✅ PASS | add=200, del=200 |
| A13 | read_only delete_row → 403 | ✅ PASS | got 403 |
| A14 | manager save_group (合併) → 200 | ✅ PASS | got 200, ok=True |
| A15 | delete_group (解除合併) → 200 | ✅ PASS | got 200 |
| A16 | 另存新階段 → 200+stage_id | ✅ PASS | got 200, resp={'ok': True, 'stage_id': 2} |
| A17 | read_only 另存新階段 → 403 | ✅ PASS | got 403 |
| A18 | data_entry 送審 → 200 | ✅ PASS | got 200, resp={'ok': True, 'review_id': 1} |
| A19 | admin 設為合格版 → 200 | ✅ PASS | got 200 |
| A20 | admin /api/system/version_status → 200 | ✅ PASS | got 200, resp={'local_commit': 'b150aba', 'ok': True, 'remote_commit': 'b150aba', 'up_to_date': True} |
| A21 | data_entry version_status → 403 | ✅ PASS | got 403 |
| A22 | read_only version_status → 403 | ✅ PASS | got 403 |
| A23 | manager system/update 回傳合法狀態碼 | ✅ PASS | got 409: 本地有改動，請聯絡管理員 |
| A23b | (bonus) 本地有改動→409守衛啟動 | ✅ PASS | got 409: 本地有改動，請聯絡管理員 |
| A24 | ie/cell 回傳 zones 供前端語言切換 | ✅ PASS | got 200, zones=['裁斷機', 'ATOM', '水蜘蛛'] |

---

## Section B — 資料正確性

**結果**: 5 PASS / 0 FAIL（共 5 項）

| # | 測試項目 | 結果 | 備註 |
|---|----------|------|------|
| B01 | save→approve→query 值一致 (12.3456) | ✅ PASS | expect=12.3456 got=12.3456, approve={'ok': True} |
| B02 | 合併→群組值正確→解除→各行存在 | ✅ PASS | merge={'ok': True}, headcount_ok=True, unmerge_ok=True |
| B03 | 理論人數公式正確(std=12.0/30=0.4000) | ✅ PASS | std=12.0, theory=0.4, expect=0.4 |
| B04 | 另存新階段→新stage存在+原階段不變 | ✅ PASS | orig=2 after=3 new_stage=True |
| B05 | 重開新Session→值仍在(12.3456) | ✅ PASS | got=12.3456 |