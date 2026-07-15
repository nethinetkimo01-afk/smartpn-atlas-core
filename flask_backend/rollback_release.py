# -*- coding: utf-8 -*-
"""
rollback_release.py — 一鍵回滾上一版（Jim 要求 2026-07-15，G2）。

用途：開機 schema 守門擋下啟動時（程式比 DB 新 → 會白畫面），現場需要**立刻讓系統跑起來**，
      而不是等人來查。本檔把程式碼回滾到 RELEASE_GATE.json 的 last_good_commit。

★只回滾「程式碼」，不碰 DB：
  DB 是現場輸入的真實資料，回滾程式碼可逆、動 DB 不可逆。schema 不符時正確的方向是
  「把程式退回配得上這份 DB 的版本」，不是「把 DB 改成配得上程式」。

用法：
  python flask_backend/rollback_release.py           回滾到 last_good_commit
  python flask_backend/rollback_release.py --dry-run 只看會做什麼，不動手
"""
import io
import os
import sys
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
sys.path.insert(0, BASE)
import release_gate  # noqa: E402

DRY = '--dry-run' in sys.argv


def git(args):
    p = subprocess.run(['git'] + args, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout or '').strip(), (p.stderr or '').strip()


def main():
    g = release_gate.load_gate() or {}
    target = (g.get('last_good_commit') or '').strip()
    if not target:
        print('❌ RELEASE_GATE.json 沒有 last_good_commit，無法回滾。請聯絡中樞。')
        return 2

    _, cur, _ = git(['rev-parse', '--short', 'HEAD'])
    print(f'目前 HEAD      ：{cur}')
    print(f'回滾目標       ：{target}（last_good_commit）')

    if cur == target:
        print('✅ 已經在 last_good_commit，無需回滾。')
        print('   若仍啟動失敗 → 是 DB 缺 schema，請跑：python flask_backend\\migrate.py')
        return 0

    rc, _, err = git(['rev-parse', '--verify', f'{target}^{{commit}}'])
    if rc != 0:
        print(f'❌ 本機找不到 commit {target}，先取得：git fetch origin')
        return 2

    if DRY:
        print(f'[dry-run] 會執行：git checkout {target}')
        return 0

    print(f'回滾中：git checkout {target} ...')
    rc, out, err = git(['checkout', target])
    if rc != 0:
        print(f'❌ 回滾失敗：{err or out}')
        print('   若因本地改動擋住，請聯絡管理員（不自動丟棄現場檔案）。')
        return 1

    _, now, _ = git(['rev-parse', '--short', 'HEAD'])
    print(f'✅ 已回滾到 {now}')
    print('   請重新啟動 Flask：python flask_backend\\app.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
