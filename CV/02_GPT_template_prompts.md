# SmartPN CV — GPT 版型 Prompt 包（v1）

> 用法：**先把「① 一致性母規」整段貼給 GPT 設定好**，GPT 回覆 acknowledge 後，**同一個對話**裡逐一貼「② 版型 prompt」。同一 session、同一母規 → 七個版型才會是同一家族。
> 版面與圖＝GPT 出。我（Claude）只出 brief 與文字對位，不自畫。
> 母版換公司：母規不動，只改各頁 [FOCAL] 與側重。

---

## ① 一致性母規（先貼這段，最高約束）

```
You are designing a REUSABLE Apple-Keynote-style layout SYSTEM for a senior
executive's CV / proposal deck. I will send you ONE template at a time.
Every template MUST obey this design system exactly, so all pages read as one family.
Acknowledge this system first, then wait for each template request.

FORMAT
- Landscape page, 16:9 (Apple Keynote proportion).
- Pure white background #FFFFFF. No full-bleed photos, no textures.

TYPE
- Typeface: Inter (or SF Pro). Primary text near-black #1D1D1F.
- Secondary text / labels / eyebrows: muted grey #6E6E73.
- Tight, calm hierarchy. No bold everywhere.

THE ONE ACCENT (most important rule)
- Single accent colour: warm orange-gold #B5540D.
- It marks EXACTLY ONE element per page — the single thing the reader must remember.
- Never decorative. Never more than one orange element on a page.

SURFACES
- Light grey cards #F5F5F7, corner radius 12–16px.
- Hairlines #D2D2D7 at 0.5px. Subtle shadows only, or none.
- No gradients, no extra colours, no icon-clutter.

LAYOUT
- Left-aligned grid. Generous margins (≥7% each side). Lots of whitespace. Calm.
- Each page has ONE visual protagonist (image or diagram) the eye hits FIRST;
  text is secondary. The reader should leave with "the picture + the one orange mark".

REUSABILITY
- Each template is a TEMPLATE, not a finished page.
- Use bracketed placeholders so I can pour real copy in later:
  [EYEBROW] [TITLE] [FOCAL] [BODY] [IMAGE ZONE] [METRIC] [LABEL].
- Keep the [IMAGE ZONE] clearly marked as where a custom visual will be placed.

OUTPUT
- Deliver each template as a clean, editable layout.
- State the grid (margins, columns, where each placeholder sits) so it can be reproduced 1:1.
```

---

## ② 七個版型 Prompt（逐一貼，每個都接在母規之後）

每個 prompt 第一句都是 `Using the SmartPN CV design system above:`，確保繼承母規。

---

### T1 — D01 Quiet Cover　｜用於 P1 封面、P5 過渡、P15 結尾
```
Using the SmartPN CV design system above:
Design the "Quiet Cover" template (D01).
- One calm hero image as the visual protagonist, right ~55% of the page, full height.
- Left ~45%: small grey [EYEBROW] at top; a large near-black [TITLE]; a [SUBTITLE]
  line that contains exactly one orange [FOCAL] phrase; a 0.5px hairline;
  then a small grey [SUPPORTING LINE].
- Maximum whitespace, minimum elements. A subtle page marker bottom-left.
- This template is reused for opening, transition, and closing — keep it austere and quiet.
```

### T2 — D02 Four Value Cards　｜用於 P7 SmartPN 四支柱
```
Using the SmartPN CV design system above:
Design the "Four Value Cards" template (D02).
- Short [TITLE] top-left, containing one orange [FOCAL] word.
- Four equal #F5F5F7 cards (one row, or 2×2), radius 14px. Each card =
  a bold [CARD TITLE] + a one-line [CARD BODY].
- Exactly ONE card title may carry the orange accent (the focal); the rest stay near-black.
- Keep it image-light; the four cards ARE the visual protagonist. Even spacing, calm.
```

### T3 — D03 Before / After　｜用於 P9 Governance 對比、P10 Motivation 對比
```
Using the SmartPN CV design system above:
Design the "Before / After" contrast template (D03).
- [TITLE] top, with one orange [FOCAL] phrase.
- Body split into two vertical halves with a thin #D2D2D7 divider:
  LEFT = [BEFORE] (the stuck / old state), RIGHT = [AFTER] (the better state).
- Distinguish the two sides by weight, position, and a small grey [LABEL] —
  NOT by loud colours. The single orange accent stays on [FOCAL] only.
- A simple minimal diagram zone in each half. Reusable for any two-state contrast.
```

### T4 — D04 Concept Model　｜用於 P3 全鏈路、P8 兩層、P11 缺口、P13 貢獻
```
Using the SmartPN CV design system above:
Design the "Concept Model" template (D04).
- [TITLE] top, with one orange [FOCAL] phrase.
- Centre: a clean minimal DIAGRAM as the visual protagonist — a model of 2–4
  connected parts ([PART A] → [PART B] → [PART C]), thin connectors, lots of air,
  label-driven, no clip-art, no 3D.
- One element of the diagram may carry the orange accent. A short [BODY] line beneath.
- Must flex to show: a chain, stacked layers, or "three known things + one empty gap".
```

### T5 — D05 Proof Metrics　｜用於 P4 標準化實績、P6 IE 系統數字
```
Using the SmartPN CV design system above:
Design the "Proof Metrics" template (D05).
- [TITLE] top-left, with one orange [FOCAL] phrase.
- Hero: 2–3 very large [METRIC] numbers, each with a small grey [METRIC LABEL] under it,
  generous spacing. The big numbers ARE the visual protagonist — big and quiet.
- Exactly ONE metric may be orange (the focal). Optional one-line [BODY].
- Reusable for any metrics page.
```

### T6 — D06 Leadership Narrative　｜用於 P2 為何寫、P14 工作背景
```
Using the SmartPN CV design system above:
Design the "Leadership Narrative" template (D06).
- Single calm left-aligned column. Small grey [EYEBROW]; a [TITLE];
  then 2–4 short [BODY] paragraphs with comfortable line-height; one orange
  [FOCAL] phrase inline.
- Optional quiet portrait / abstract [IMAGE ZONE] on one side, restrained.
- The most text-forward template — but still airy, executive, reflective.
```

### T7 — Scenario（共用版面，複製 17 次）　｜用於 P12 與 17 場景
```
Using the SmartPN CV design system above:
Design the "Scenario" template — built to be COPIED 17 times with different content,
so every scenario page looks identical except its content.
- Top: a small grey [GROUP LABEL] (Brand / Factory / Supplier / Cross-use) and a
  [SCENARIO TITLE]; the scenario title carries the single orange accent.
- Centre: one simple [SCENARIO DIAGRAM] zone (the visual protagonist) +
  a one-line [SCENARIO BODY].
- A subtle [INDEX] marker (e.g., S05 / 17).
- Critical: ONE reusable master — same grid, same placeholder positions every time.
- Also give an optional "index / overview" variant that lists all 17 grouped by the four
  groups above.
```

---

## ③ 版型 → 頁面對照（定案後照這個套現有文案）

| 版型 | 頁 |
|---|---|
| D01 Quiet Cover | P1, P5, P15 |
| D02 Four Value Cards | P7 |
| D03 Before / After | P9, P10 |
| D04 Concept Model | P3, P8, P11, P13 |
| D05 Proof Metrics | P4, P6 |
| D06 Leadership Narrative | P2, P14 |
| Scenario（共用） | P12 + 17 場景 |

→ 七個版型其實只要做 **7 個母版**，15 頁全靠複製套用。

---

## ④ 一致性小提醒（確保不走鐘）
1. **同一個 GPT 對話**裡做完七個，不要分開開新對話。
2. 母規貼一次後，每個版型 prompt 都以 `Using the design system above` 開頭。
3. 先要 GPT 出**空版型（含 [placeholder]）**給你定案，**不要**一開始就塞真內容——定案後我再把 15 頁文案灌進去。
4. 若 GPT 某版型偏離母規（多了顏色、塞滿、圖搶不過文字），就回他一句：`Re-check against the design system: one accent only, one visual protagonist, more whitespace.`

---

## ⑤ 還缺的（等你補，補了就全齊）
- **P6 三個數字**：records / models / users。
- 其餘 14 頁文案已備妥，版型一定案即可全套灌入。
