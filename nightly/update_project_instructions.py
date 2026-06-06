#!/usr/bin/env python3
"""
Update DATA SYSTEM Claude.ai Project Instructions via session key.

Usage:
    $env:CLAUDE_SESSION_KEY = "sk-ant-..."
    python nightly/update_project_instructions.py

The script:
  1. Authenticates with claude.ai using session key
  2. Finds the DATA SYSTEM project
  3. PATCHes the project prompt_template with the instructions below
"""
import os, sys, json, requests
from pathlib import Path

INSTRUCTIONS = """\
你是 DATA SYSTEM 專案的 Claude。

每次對話開始，立刻執行，不問 Jim 任何事：

1. 讀取 24_DATA_SYSTEM.md 的「## 最新執行結果」區塊，報告：
   - 執行時間、各任務狀態
   - LEAN 比對結果（一致/不符/分類原因）
   - ART 缺失清單（DS04有/廠務無）
   - OCS 狀態
2. 判斷每個差異是人為數據錯誤還是邏輯錯誤
3. 列出今天需要 Jim 確認的事項（不包含 MP 和 EOLR，這兩個 PENDING 不討論）

禁止：問 MP 規則、問 EOLR mapping、未確認前自己猜測邏輯
"""

BASE_URL = "https://claude.ai/api"


def get_session():
    key = os.environ.get("CLAUDE_SESSION_KEY", "").strip()
    if not key:
        sys.exit("ERROR: Set $env:CLAUDE_SESSION_KEY before running this script.")
    return key


def make_headers(session_key):
    return {
        "Cookie": f"sessionKey={session_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://claude.ai/",
    }


def get_org(session_key):
    r = requests.get(f"{BASE_URL}/organizations", headers=make_headers(session_key))
    r.raise_for_status()
    orgs = r.json()
    if not orgs:
        sys.exit("ERROR: No organizations found.")
    org = orgs[0]
    print(f"  Org: {org['name']} ({org['id']})")
    return org["id"]


def find_project(session_key, org_id):
    r = requests.get(
        f"{BASE_URL}/organizations/{org_id}/projects",
        headers=make_headers(session_key),
    )
    r.raise_for_status()
    projects = r.json()
    for p in projects:
        if "DATA" in p.get("name", "").upper() or "SYSTEM" in p.get("name", "").upper():
            print(f"  Project: {p['name']} ({p['uuid']})")
            return p["uuid"]
    # Fallback: list all and let user pick
    print("  DATA SYSTEM project not found. Available projects:")
    for p in projects:
        print(f"    - {p['name']} ({p['uuid']})")
    sys.exit("ERROR: Could not find DATA SYSTEM project.")


def update_instructions(session_key, org_id, project_id):
    payload = {"prompt_template": INSTRUCTIONS}
    r = requests.put(
        f"{BASE_URL}/organizations/{org_id}/projects/{project_id}",
        headers=make_headers(session_key),
        json=payload,
    )
    if r.status_code in (200, 204):
        print("  ✅ Project Instructions updated successfully.")
    else:
        print(f"  ❌ Update failed: {r.status_code} {r.text[:300]}")
        sys.exit(1)


def main():
    print("=== Update DATA SYSTEM Project Instructions ===\n")
    key = get_session()
    print("Step 1: Get organization...")
    org_id = get_org(key)
    print("Step 2: Find DATA SYSTEM project...")
    project_id = find_project(key, org_id)
    print("Step 3: Update instructions...")
    update_instructions(key, org_id, project_id)
    print("\nDone. Test with: python nightly/test_project_response.py")


if __name__ == "__main__":
    main()
