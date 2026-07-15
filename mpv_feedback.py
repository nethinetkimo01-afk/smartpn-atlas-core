# -*- coding: utf-8 -*-
"""
mpv_feedback.py — 多方驗證反饋迴路（MPV feedback loop）。

讀 verification/round_NN/ 下四方 .json（builder / breaker / auditor / user）→ 交叉比對
→ 全票制裁決 → 寫 arbiter.md（含自動退回令）。

★ 裁決原則（45_MULTIPARTY_VERIFICATION §二、§六）：
  1. 全票制：四方全綠才放行。任一方紅 = 退回。**非多數決**。
  2. 交叉比對：建造者說綠、他方有可重現證據說紅 → **以紅為準**（建造者不得當自己的裁判）。
  3. 缺席即紅：四方少一份 = 不放行（沒驗＝沒過，不是「預設沒問題」）。
  4. 證據制：finding 沒有 repro（最小重現）→ 標記為「證據不足」，但**仍算紅**，
     由中樞人工判定；不允許因為「說不清楚」就當沒發生。
  5. 放行 ≠ 上線：本檔輸出「可送中樞複核」。**中樞必須用 Jim 真庫複跑**才對 Jim 說可以看。

用法：
  python mpv_feedback.py                 裁決最新一輪（verification/ 下編號最大的 round_NN）
  python mpv_feedback.py --round 3       裁決指定輪
  python mpv_feedback.py --new           開新一輪（建 round_NN/ + 四方 .json 範本）
"""
import os
import io
import sys
import re
import json
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(HERE, 'verification')
PARTIES = ['builder', 'breaker', 'auditor', 'user']
PARTY_ZH = {'builder': '建造者 Code', 'breaker': '破壞者 Breaker',
            'auditor': '對規者 Spec-Auditor', 'user': '使用者 User-Sim'}


def rounds():
    return sorted(glob.glob(os.path.join(VDIR, 'round_*')),
                  key=lambda p: int(re.search(r'round_(\d+)', p).group(1)))


def latest_round():
    r = rounds()
    if not r:
        raise SystemExit('❌ verification/ 下沒有任何 round_NN，先跑 python mpv_feedback.py --new')
    return r[-1]


def load(rdir):
    """讀四方 .json。缺席/壞檔都明確回報，不靜默略過。"""
    out = {}
    for p in PARTIES:
        fp = os.path.join(rdir, p + '.json')
        if not os.path.isfile(fp):
            out[p] = {'_missing': True}
            continue
        try:
            with open(fp, encoding='utf-8') as f:
                out[p] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            out[p] = {'_broken': str(e)}
    return out


def _findings(rep):
    fs = rep.get('findings') or []
    return [f for f in fs if isinstance(f, dict)]


def verdict_of(rep):
    """一方的判定。紅的來源有二：明寫 verdict=red，或**交出了 finding**。
    明寫 green 卻附 finding → 以 finding 為準（說綠不算數，證據算數）。"""
    if rep.get('_missing') or rep.get('_broken'):
        return 'red'
    v = str(rep.get('verdict', '')).lower()
    if _findings(rep):
        return 'red'
    return 'green' if v in ('green', 'pass', 'ok') else 'red'


def arbitrate(reps):
    """交叉比對 + 全票制。回傳 (放行?, 各方判定, 全部 findings, 交叉比對註記)。"""
    verdicts = {p: verdict_of(reps[p]) for p in PARTIES}
    all_findings = []
    for p in PARTIES:
        for f in _findings(reps[p]):
            f = dict(f)
            f['_from'] = p
            all_findings.append(f)

    notes = []
    # 交叉比對：建造者說綠，但他方有證據說紅 → 以紅為準。
    b = reps['builder']
    if not b.get('_missing') and verdict_of(b) == 'green':
        contra = [f for f in all_findings if f['_from'] != 'builder']
        if contra:
            notes.append(
                f'⚖️ 交叉比對：建造者自證綠，但他方交出 {len(contra)} 項證據 → **以紅為準**。'
                f'（建造者不得當自己的裁判；hub_ci 全綠只是入場券）')
    for p in PARTIES:
        if reps[p].get('_missing'):
            notes.append(f'⚖️ {PARTY_ZH[p]} **缺席** → 缺席即紅（沒驗＝沒過）。')
        elif reps[p].get('_broken'):
            notes.append(f'⚖️ {PARTY_ZH[p]} 的 .json 壞檔（{reps[p]["_broken"]}）→ 判紅。')
    weak = [f for f in all_findings if not f.get('repro')]
    if weak:
        notes.append(f'⚖️ 有 {len(weak)} 項 finding 缺「最小重現(repro)」→ 標證據不足，'
                     f'但仍算紅，由中樞人工判定（不允許因說不清就當沒發生）。')

    # ★ 資料來源自證（27 規則十二-7）：綠燈必須自證測的是哪個庫。
    src = (b.get('data_source') or {}) if isinstance(b, dict) else {}
    ah = src.get('actual_headers')
    if ah is None:
        notes.append('⚖️ 建造者未申報 data_source（測的是哪個庫）→ 綠燈不可採信，判紅。'
                     '請貼 hub_ci 的「來源身分」橫幅。')
        verdicts['builder'] = 'red'
    elif isinstance(ah, int) and ah < 100:
        notes.append(f'⚖️ 建造者申報 data_source.actual_headers={ah}（真庫應 ≈140）→ '
                     f'**不是 Jim 真庫**。凡依賴真實資料的結論一律不成立，判紅。')
        verdicts['builder'] = 'red'

    ok = all(v == 'green' for v in verdicts.values())
    return ok, verdicts, all_findings, notes


def render(rdir, reps, ok, verdicts, findings, notes):
    rn = os.path.basename(rdir)
    L = []
    L.append(f'# 裁決書 arbiter — {rn}')
    L.append('')
    L.append(f'> 由 `mpv_feedback.py` 自動生成。依 45_MULTIPARTY_VERIFICATION：'
             f'**全票制**，任一方紅即退回（非多數決）。')
    L.append('')
    commit = (reps['builder'] or {}).get('commit', '(未申報)')
    delivery = (reps['builder'] or {}).get('delivery', '(未申報)')
    L.append(f'- 交付：{delivery}')
    L.append(f'- commit：{commit}')
    L.append('')
    L.append('## 一、四方判定')
    L.append('')
    L.append('| 方 | 判定 | 摘要 |')
    L.append('|---|---|---|')
    for p in PARTIES:
        r = reps[p]
        if r.get('_missing'):
            s = '**缺席**'
        elif r.get('_broken'):
            s = '壞檔'
        else:
            s = r.get('summary', '(無摘要)')
        L.append(f'| {PARTY_ZH[p]} | {"🟢 綠" if verdicts[p] == "green" else "🔴 紅"} | {s} |')
    L.append('')
    if notes:
        L.append('## 二、交叉比對')
        L.append('')
        L.extend('- ' + n for n in notes)
        L.append('')
    L.append('## 三、證據清單')
    L.append('')
    if not findings:
        L.append('（無 finding）')
    else:
        for i, f in enumerate(findings, 1):
            L.append(f'### {i}. [{PARTY_ZH[f["_from"]]}] {f.get("summary", "(無摘要)")}')
            L.append('')
            L.append(f'- 嚴重度：{f.get("severity", "(未標)")}')
            L.append(f'- 證據：{f.get("evidence", "(未附)")}')
            L.append(f'- 最小重現：{f.get("repro") or "**(未附 → 證據不足，仍算紅)**"}')
            L.append('')
    L.append('## 四、裁決')
    L.append('')
    if ok:
        L.append('✅ **四方全綠 → 放行至中樞複核**')
        L.append('')
        L.append('> ⚠️ 放行 ≠ 上線。**中樞必須用 Jim 真庫（ME129）獨立複跑閘門**，'
                 '全綠才對 Jim 說「可以看」。本機綠燈只在本機那份資料上成立。')
    else:
        red = [PARTY_ZH[p] for p in PARTIES if verdicts[p] == 'red']
        L.append(f'🔴 **退回（RETURN）** — 紅方：{"、".join(red)}')
        L.append('')
        L.append('### 退回令（貼給 Code）')
        L.append('')
        L.append('```')
        L.append(f'RETURN / {rn} / commit {commit}')
        L.append(f'紅方：{"、".join(red)}')
        L.append('')
        if findings:
            L.append('必修（逐項附修好後的重現結果）：')
            for i, f in enumerate(findings, 1):
                L.append(f'  {i}. [{f.get("severity", "?")}] {f.get("summary", "")}')
                if f.get('repro'):
                    L.append(f'     重現：{f["repro"]}')
        for p in PARTIES:
            if reps[p].get('_missing'):
                L.append(f'  - 補交 {PARTY_ZH[p]} 的 {p}.json（缺席即紅）')
        L.append('')
        L.append('修好後：python hub_ci.py 全綠 → 開新一輪 --new → 四方重驗。')
        L.append('不得修改任何閘門判定（改判定＝作弊，該次交付作廢）。')
        L.append('```')
    L.append('')
    return '\n'.join(L)


TEMPLATE = {
    'builder': {
        'party': 'builder', 'delivery': '（交付名稱）', 'commit': '（sha）',
        # 範本預設 red：沒填＝沒驗＝不放行（fail-closed）。填完再改 green。
        'verdict': 'red', 'summary': '（未執行）',
        'data_source': {'_comment': '★必填：貼 hub_ci 的「來源身分」橫幅數字，'
                                    '否則綠燈不可採信（27 規則十二-7）',
                        'db': 'flask_backend/data/atlas.db',
                        'ie_process_rows': 0, 'ob_header_rows': 0, 'actual_headers': 0},
        'what_i_did': ['（做了什麼）'], 'evidence': ['（hub_ci 輸出全文 / 閘門 hash）'],
        'findings': [],
    },
    'breaker': {
        'party': 'breaker', 'verdict': 'red',
        'summary': '（未執行：攻不破 / 攻破 N 處）',
        'what_i_did': ['亂點', '並發', '壞資料', '邊界', '權限繞過', '狀態殘留'],
        # findings 必須留空陣列：範本裡的假 finding 會被當成真的攻破證據混進退回令。
        # 格式範例放 _example（底線開頭不參與裁決）。
        '_example_finding': {'severity': 'high', 'summary': '（哪裡壞）',
                             'evidence': '（回應碼/錯誤訊息/數字）',
                             'repro': '（最小重現步驟）'},
        'findings': [],
    },
    'auditor': {
        'party': 'auditor', 'verdict': 'red',
        'summary': '（未執行：符合 N/N 條）',
        'coverage': {'verified': 0, 'required': 0},
        'what_i_did': ['逐條對帳 28_BIANCHE_SPEC / 16_S02_TO_S17 / 27_WORKING_RULES'],
        'findings': [],
    },
    'user': {
        'party': 'user', 'verdict': 'red',
        'summary': '（未執行：全程走通 / 卡在第 N 步）',
        'what_i_did': ['匯入→勾選→計算→導出', '只用真實點擊，不呼叫內部 API'],
        'findings': [],
    },
}


def new_round():
    os.makedirs(VDIR, exist_ok=True)
    n = len(rounds()) + 1
    rdir = os.path.join(VDIR, f'round_{n:02d}')
    os.makedirs(rdir, exist_ok=True)
    for p in PARTIES:
        fp = os.path.join(rdir, p + '.json')
        if not os.path.isfile(fp):
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(TEMPLATE[p], f, ensure_ascii=False, indent=2)
    print(f'✅ 開新一輪：{rdir}')
    print(f'   四方 .json 範本已建。各方獨立填寫後跑：python mpv_feedback.py --round {n}')
    return rdir


def main():
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if '--new' in sys.argv:
        new_round()
        return
    if '--round' in sys.argv:
        n = int(sys.argv[sys.argv.index('--round') + 1])
        rdir = os.path.join(VDIR, f'round_{n:02d}')
        if not os.path.isdir(rdir):
            raise SystemExit(f'❌ 沒有這一輪：{rdir}')
    else:
        rdir = latest_round()

    reps = load(rdir)
    ok, verdicts, findings, notes = arbitrate(reps)
    md = render(rdir, reps, ok, verdicts, findings, notes)
    out = os.path.join(rdir, 'arbiter.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(md)
    print(md)
    print(f'\n▸ 已寫出：{out}')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
