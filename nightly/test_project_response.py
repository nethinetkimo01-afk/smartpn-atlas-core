#!/usr/bin/env python3
"""
Simulate a DATA SYSTEM Project conversation via Anthropic Messages API.

Usage:
    $env:ANTHROPIC_API_KEY = "sk-ant-..."
    python nightly/test_project_response.py

The script:
  1. Reads 24_DATA_SYSTEM.md → extracts ## 最新執行結果 block
  2. Builds a system prompt (Project Instructions) + user message "繼續 DATA SYSTEM"
  3. Calls claude-sonnet-4-6 via Messages API
  4. Prints the response so Jim can verify it's correct
"""
import os, sys, re, json
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
HANDOFF = ROOT / "00_HANDOFF"
MD_PATH = HANDOFF / "24_DATA_SYSTEM.md"

SYSTEM_PROMPT = """\
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


def read_handoff_block():
    """Extract ## 最新執行結果 block from 24_DATA_SYSTEM.md."""
    try:
        text = MD_PATH.read_text(encoding="utf-8")
        marker = "## 最新執行結果"
        if marker in text:
            block = text[text.index(marker):]
            # trim to just this section (stop at next ##)
            rest = block[len(marker):]
            next_sec = re.search(r"\n## ", rest)
            if next_sec:
                block = marker + rest[: next_sec.start()]
            return block.strip()
        return "(24_DATA_SYSTEM.md 中找不到 ## 最新執行結果 區塊)"
    except Exception as e:
        return f"(讀取失敗: {e})"


def call_api(api_key, system, user_msg):
    import urllib.request, urllib.error

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": user_msg}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
            return body["content"][0]["text"]
    except urllib.error.HTTPError as e:
        return f"API error {e.code}: {e.read().decode()}"
    except Exception as e:
        return f"Request failed: {e}"


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        sys.exit("ERROR: Set $env:ANTHROPIC_API_KEY before running this script.")

    print("=== DATA SYSTEM Project Response Simulation ===\n")
    print("Reading 24_DATA_SYSTEM.md ## 最新執行結果...")
    block = read_handoff_block()
    print(f"Block length: {len(block)} chars\n")

    # The user message includes the handoff block so the model can reference it
    user_msg = f"""繼續 DATA SYSTEM

以下是 24_DATA_SYSTEM.md 的「## 最新執行結果」區塊供你參考：

{block}"""

    print("Calling claude-sonnet-4-6...\n")
    print("=" * 60)
    response = call_api(api_key, SYSTEM_PROMPT, user_msg)
    print(response)
    print("=" * 60)
    print("\n✅ Test complete. Verify the response matches expected format.")


if __name__ == "__main__":
    main()
