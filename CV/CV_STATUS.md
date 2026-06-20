# CV — STATUS（下個 session 先讀這個）

> 用途：這是 Jim 的「主動提案型 CV」工作包的進度入口。換 session 後，Claude 先用 raw 通道讀回本資料夾，**不要再叫 Jim 重傳任何檔**。
> raw 範例：`https://raw.githubusercontent.com/nethinetkimo01-afk/smartpn-atlas-core/main/CV/cv_builder.py`

---

## 0. 一句話
這是 **Jim 的 CV**（主角＝Jim），形式＝主動申請一個尚未公布的職缺。SmartPN Atlas 只是 P7–P13 的能力佐證之一，不是產品簡介。首發 Inspectorio，母版換公司只改變量。

## 1. 鐵則（違反過會被糾正）
- 先給結果再問；不要列清單要 Jim 核；不要一次問一堆。
- **GPT 只負責「一次性出版型長相」**；版型定案＝規格。之後所有對位/灌字/調整/修錯，**Claude 自己用 builder 做到底、自渲染、自 self-QA、自出 PDF，不回 GPT。**
- 不糾錯：圖文重疊、附沒用程式碼、沒讀懂指令 → 交付前自己攔。
- 視覺一致性母規（下方第 4 節）是最高約束，每頁都繼承。
- 交付給 Jim 只給成品；builder 僅作備援。
- **成果一律由 Claude 自己存進本資料夾**，不要散掉、不要事後要 Jim 重傳。

## 2. 流程（現在在哪）
1. 全貌確認 ✅（15 頁 / 四幕，見 `01_COPY_15pages.md`）
2. 15 頁英文文案 ✅（`01_COPY_15pages.md`）
3. GPT 版型 prompt ✅（`02_GPT_template_prompts.md`，含一致性母規＋7 版型）
4. **第一款基調渲染 ✅**（封面 D01 → `renders/CV_P1_cover_D01.pdf`/`.png`）由新 builder `cv_builder.py` 產出
5. ⏳ **等 Jim：** 拿基調＋母規去 GPT 出多款視覺方向 → Jim 選一款
6. ⏳ Jim 選定後：Claude 照基調把 D01–D07 全做到底 → 灌 15 頁 → 出整本 PDF

## 3. 待 Jim 補/確認
- **P6 三個數字**：IE 系統 records / models / users（唯一卡內容的點）。
- 基調（白底/Inter/單一橘金/左對齊大留白）是否接受。
- GPT 出的視覺方向選哪一款。

## 4. 一致性母規（locked design tokens）
- 版面：landscape 16:9（1280×720 @96dpi）。純白底 #FFFFFF。
- 字：Inter。主字近黑 #1D1D1F；次要/標籤灰 #6E6E73；頁碼 #AEAEB2。
- **唯一強調色** 橘金 #B5540D：每頁只標一個要被記住的重點，絕不裝飾、絕不超過一處。
- 卡片灰 #F5F5F7，圓角 12–16px；分隔線 #D2D2D7 0.5px。
- 左對齊網格、邊距 ≥7%、大留白。每頁一個視覺主角（圖），文字配角。
- 七版型：D01 Quiet Cover / D02 Four Value Cards / D03 Before-After / D04 Concept Model / D05 Proof Metrics / D06 Leadership Narrative / D07 Scenario（共用，複製 17 次）。

## 5. 版型 → 頁對照
| 版型 | 頁 |
|---|---|
| D01 Quiet Cover | P1, P5, P15 |
| D02 Four Value Cards | P7 |
| D03 Before/After | P9, P10 |
| D04 Concept Model | P3, P8, P11, P13 |
| D05 Proof Metrics | P4, P6 |
| D06 Leadership Narrative | P2, P14 |
| D07 Scenario（共用） | P12 ＋ 17 場景 |

## 6. 渲染環境（換 session 重建，約 1 分鐘，不需 Jim）
容器無瀏覽器，用 **weasyprint**（pango/cairo 已內建）。Inter 用 fontTools 從可變字型切靜態字重：
```bash
pip install weasyprint pymupdf --break-system-packages -q
mkdir -p ~/.fonts && cd ~
curl -sL -o Inter-var.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
python3 - <<'PY'
from fontTools import ttLib
from fontTools.varLib.instancer import instantiateVariableFont
import os
for w,fam in {400:"Inter",500:"Inter Medium",600:"Inter SemiBold"}.items():
    f=ttLib.TTFont("Inter-var.ttf"); instantiateVariableFont(f,{"wght":w,"opsz":18},inplace=True)
    n=f["name"]
    for nid,val in [(1,fam),(4,fam),(6,fam.replace(' ','')),(16,fam)]: n.setName(val,nid,3,1,0x409)
    f.save(os.path.expanduser(f"~/.fonts/{fam.replace(' ','-')}.ttf"))
PY
fc-cache -f ~/.fonts
```
然後 `python3 CV/cv_builder.py` 即可重出封面。其餘版型依第 4 節母規續寫進同一 builder。

## 7. 檔案清單
- `cv_builder.py` — 新 builder（規格化重做用，唯一渲染來源）
- `01_COPY_15pages.md` — 15 頁英文文案（含每頁橘金重點＋給 GPT 圖示說明）
- `02_GPT_template_prompts.md` — 一致性母規 ＋ 7 版型 GPT prompt
- `renders/CV_P1_cover_D01.pdf` / `.png` — 第一款基調成品
- `CV_STATUS.md` — 本檔（入口）
