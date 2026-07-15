# -*- coding: utf-8 -*-
"""
data_leak_gate.py — 真實生產資料外洩閘門（入規27，中樞裁決 2026-07-15；hub_ci 常設閘門15）。

★為什麼有這支：
  2026-07-15 發現 f9126aa / fa0906e 把 IE-VER 對帳報告（real_db_for_recon/*.md）commit 進 dev-iever。
  報告內含鞋型、ART 料號、標時、實際人數、工序明細＝客戶真實生產資料。
  當時 .gitignore 明文寫「DB 檔不進 git（報告 .md 要追蹤）」——**擋住了大檔，卻放行了真資料本身**。
  根因：防護對象抓錯，防的是「檔案大小/格式」，該防的是「資料是不是真的」。
  入規27：真實生產資料永不進 git，不論 repo 公開或私有；報告留本機靠檔案傳遞。

斷言（對「本次 push 會送出去的新 blob」）：
  L1 ART 料號樣式  2碼大寫英文＋4碼數字（真庫實測 140/140 皆為此形）
  L2 鞋型清單      執行時從本機真庫即時取出（**絕不寫死在本檔**，見下方鐵則）
  L3 路徑政策      real_db_for_recon/ 底下任何檔案都不得進入任何 commit

★L1 一律嚴格（形狀命中就紅），不因「這顆不在真庫裡」而放行：
  真庫只有本機這份，ME129/未來新料號不在裡面——「不在真庫」不等於「不是真料號」。
  代價：規格/程式碼**不得出現符合 ART 形狀的字串**，示例一律寫「2碼英文+4碼數字」。
  這代價是划算的：少寫一個假料號範例，換到「新料號也擋得住」。
  （本檔自己就是實例：docstring 原本寫了形狀範例 → 被自己的閘門擋下 → 改成文字敘述。）

★掃「範圍內所有 commit」，不是只掃 HEAD：
  HEAD 乾淨、但中間某顆 commit 有真資料 → push 上去歷史裡照樣有，git 永遠記得。
  f9126aa 正是這情形（後續 commit 沒動它，HEAD 也還在）。

★鐵則：鞋型清單不得寫死在本檔。
  寫死＝這支「防洩漏的閘門」自己把真鞋型 commit 進 git，變成洩漏源本身。
  一律執行時從真庫（gitignored，不在 repo 內）讀，讀完只存在記憶體。

fail-closed：讀不到真庫 → exit 2 擋 push（無法舉證乾淨 ≠ 乾淨）。

用法：
  python data_leak_gate.py                   掃「本地有、origin 沒有」的所有 commit（預設）
  python data_leak_gate.py <base>..<head>    掃指定範圍
"""
import io
import os
import re
import sys
import sqlite3
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))

# 真庫候選（皆為 gitignored / repo 外；只讀，不寫）。找到第一個能用的就用。
DB_CANDIDATES = [
    os.path.join(ROOT, 'real_db_for_recon', 'atlas.db'),
    os.path.join(ROOT, 'flask_backend', 'data', 'atlas.db'),
    os.path.join(ROOT, 'flask_backend', 'atlas.db'),
]

# ART 料號的「形狀」＝2碼大寫英文＋4碼數字（真庫實測 140/140 皆此形）。
# 形狀不是真資料本身，可以寫死；真料號清單則絕不寫死（見 load_shoe_vocab 的鐵則）。
ART_RE = re.compile(r'\b[A-Z]{2}\d{4}\b')

# 二進位/非文字類：不掃內容（截圖等），但仍受 L3 路徑政策管。
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.xlsx', '.xls',
            '.db', '.db-wal', '.db-shm', '.pyc', '.woff', '.woff2', '.ttf'}

# 鞋型清單的雜訊過濾：太短或太通用的 key 會誤傷正常程式碼。
MIN_SHOE_LEN = 5

R = []


def rec(name, ok, detail=''):
    R.append((name, ok))
    print(f'  {"✅" if ok else "❌"} {name}' + (f' — {detail}' if detail else ''), flush=True)


def git(*args):
    return subprocess.run(['git'] + list(args), cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).stdout


def load_shoe_vocab():
    """從本機真庫即時取鞋型清單。回傳 (set, db路徑)；讀不到回 (None, None) → fail-closed。"""
    for db in DB_CANDIDATES:
        if not os.path.isfile(db):
            continue
        try:
            c = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
            c.execute('PRAGMA query_only=ON')
            names = [r[0] for r in c.execute(
                'SELECT model_name FROM ob_header WHERE model_name IS NOT NULL') if r[0]]
            c.close()
        except sqlite3.Error:
            continue
        vocab = set()
        for n in names:
            # 與 ie_ver_recon.py 同法：去掉 'Target Output ...' 尾巴 + 收斂空白 + 轉大寫
            key = re.split(r'Target\s*Output', n, flags=re.I)[0]
            key = re.sub(r'\s+', ' ', key).strip().upper()
            if len(key) >= MIN_SHOE_LEN:
                vocab.add(key)
        if vocab:
            return vocab, db
    return None, None


def push_range():
    if len(sys.argv) > 1 and '..' in sys.argv[1]:
        return sys.argv[1]
    # 本地有、任何 remote 都沒有的 commit ＝ 這次 push 會送出去的東西
    return None


def commits_in_range(rng):
    if rng:
        out = git('rev-list', rng)
    else:
        out = git('rev-list', 'HEAD', '--not', '--remotes')
    return [l for l in out.decode('utf-8', 'replace').split() if l]


def new_objects(rng):
    """這次 push 會**真的送出去的新 blob**：(path, blob_sha)。

    語意＝「remote 還沒有的物件」，用 rev-list --objects ... --not --remotes 求差集。
    為什麼不是「每顆 commit 的整棵樹」：
      整棵樹掃會把 remote 早就有的舊 blob 也算成本次 push 的罪狀（見下方「既有污染」段），
      那會讓每一次 push 都紅、閘門變成永遠擋著的假警報，最後被人繞過。
    為什麼不是「只掃 HEAD」：
      HEAD 乾淨、中間某顆 commit 有真資料 → 那些 blob 仍是 remote 沒有的新物件，
      仍會被本函式抓到（f9126aa 的報告檔正是此例，已實測會紅）。
    """
    args = ['rev-list', '--objects']
    args += [rng] if rng else ['HEAD']
    args += ['--not', '--remotes']
    out = git(*args).decode('utf-8', 'replace')
    cand = []
    for line in out.splitlines():
        sha, _, path = line.partition(' ')
        path = path.strip().strip('"')
        if path:  # 沒 path 的是 commit 物件
            cand.append((path, sha))
    if not cand:
        return []
    # rev-list --objects 連 tree（目錄）也會列出來，會把目錄誤算成檔案 → 只留 blob
    probe = subprocess.run(['git', 'cat-file', '--batch-check'], cwd=ROOT,
                           input='\n'.join(s for _, s in cand).encode(),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    types = {}
    for line in probe.stdout.decode('utf-8', 'replace').splitlines():
        p = line.split()
        if len(p) >= 2:
            types[p[0]] = p[1]
    return [(p, s) for p, s in cand if types.get(s) == 'blob']


def preexisting_leak(vocab):
    """既有污染（origin 早就有的）：不擋本次 push，但一定要講出來。
    擋不擋是中樞的決定（清 main 歷史＝改寫已 push 的分支），閘門的責任是不讓它悄悄過去。"""
    out = git('ls-tree', '-r', '--name-only', 'origin/main').decode('utf-8', 'replace')
    hit = []
    for path in out.splitlines():
        path = path.strip().strip('"')
        if not path or os.path.splitext(path)[1].lower() in SKIP_EXT:
            continue
        raw = git('cat-file', '-p', f'origin/main:{path}')
        if not raw or b'\x00' in raw[:8000] or len(raw) > 8 * 1024 * 1024:
            continue
        if scan_text(raw.decode('utf-8', 'replace'), vocab):
            hit.append(path)
    return hit


def scan_text(text, vocab):
    """回傳命中清單 [(類型, 樣本)]。樣本只印遮蔽後的形狀，不把真資料印進 CI log。"""
    hits = []
    arts = ART_RE.findall(text)
    if arts:
        hits.append(('ART料號', f'{len(arts)} 處（如 {arts[0][:2]}****）'))
    up = text.upper()
    shoes = [s for s in vocab if s in up]
    if shoes:
        hits.append(('鞋型', f'{len(shoes)} 個（如 {shoes[0][:3]}***）'))
    return hits


def main():
    print('=' * 68)
    print('data_leak_gate — 真實生產資料外洩閘門（入規27；hub_ci 閘門15）')
    print('=' * 68)

    vocab, db = load_shoe_vocab()
    if not vocab:
        # fail-closed：沒有真庫就無法比對鞋型 → 不准 push
        print('❌ 讀不到本機真庫（找不到/開不起來），無法建立鞋型清單 → 擋 push')
        print('   候選：' + ' / '.join(DB_CANDIDATES))
        print('   入規27 fail-closed：無法舉證「不含真實資料」≠「不含真實資料」')
        return 2
    print(f'鞋型清單來源（唯讀，本機 gitignored）：{db}')
    print(f'鞋型 key：{len(vocab)} 個（清單只在記憶體，不寫入任何檔案）')

    rng = push_range()
    shas = commits_in_range(rng)
    if not shas:
        print('\n（push 範圍內沒有 commit — 沒東西要送）')
        rec('L0 push 範圍可判定', True, '範圍為空')
        print('\n  data_leak_gate: 1/1 → ✅ ALL GREEN')
        return 0
    print(f'待 push commit：{len(shas)} 顆 → {", ".join(s[:7] for s in shas)}')
    print()

    objs = new_objects(rng)
    print(f'本次 push 送出的新 blob：{len(objs)} 個（remote 已有的舊物件不算本次罪狀，另見文末）')
    print()

    bad_path, bad_content = [], []
    for path, blob in objs:
        if 'real_db_for_recon' in path.replace('\\', '/'):
            bad_path.append(path)
            continue
        if os.path.splitext(path)[1].lower() in SKIP_EXT:
            continue
        raw = git('cat-file', '-p', blob)
        if not raw or b'\x00' in raw[:8000] or len(raw) > 8 * 1024 * 1024:
            continue
        hits = scan_text(raw.decode('utf-8', 'replace'), vocab)
        if hits:
            bad_content.append((path, hits))

    rec('L3 無 real_db_for_recon/ 檔案進入任何待 push commit', not bad_path,
        '' if not bad_path else f'{len(bad_path)} 個檔案')
    for path in bad_path[:10]:
        print(f'       {path}')

    art_bad = [b for b in bad_content if any(h[0] == 'ART料號' for h in b[1])]
    shoe_bad = [b for b in bad_content if any(h[0] == '鞋型' for h in b[1])]
    rec('L1 無 ART 料號樣式（2碼英文+4碼數字）', not art_bad,
        '' if not art_bad else f'{len(art_bad)} 個新 blob')
    rec('L2 無真庫鞋型名稱', not shoe_bad,
        '' if not shoe_bad else f'{len(shoe_bad)} 個新 blob')
    for path, hits in bad_content[:10]:
        print(f'       {path} — ' + '；'.join(f'{t}:{d}' for t, d in hits))

    # ── 既有污染：不擋本次 push，但不准悄悄過去 ──────────────────────────────
    if '--skip-preexisting' not in sys.argv:
        pre = preexisting_leak(vocab)
        if pre:
            print()
            print('  ⚠️ 既有污染（origin/main 早就有，非本次 push 造成，本閘門不擋）：')
            print(f'     {len(pre)} 個已 push 的檔案含真實生產資料樣式，例如：')
            for p in pre[:8]:
                print(f'       {p}')
            print('     ＝入規27 在本批之前就已被違反，且**已經在 GitHub 上**。')
            print('     清除需改寫已 push 的 main 歷史 → 屬中樞決定，非閘門/開發者可自行處置。')

    npass = sum(1 for _, ok in R if ok)
    allgreen = npass == len(R) and len(R) >= 3
    print('\n' + '=' * 68)
    print(f'  掃過 {len(objs)} 個新 blob（push 範圍 {len(shas)} 顆 commit）')
    print(f'  data_leak_gate: {npass}/{len(R)} → '
          f'{"✅ ALL GREEN" if allgreen else "❌ FAIL（待 push 內容含真實生產資料，擋 push）"}')
    if not allgreen:
        print('  處置：改寫該 commit 移除（新 commit 刪除＝歷史裡還在），報告留本機靠檔案傳遞。')
    print('=' * 68)
    return 0 if allgreen else 1


if __name__ == '__main__':
    sys.exit(main())
