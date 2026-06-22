# CV — STATUS（下個 session 先讀這個）　更新：2026-06-22

> 換 session 後，Claude 先讀整個 00_HANDOFF 到最新檔（**不要只讀清單上的 24，CV 內容地基在 38**），再讀本資料夾 CV/。不要再叫 Jim 重傳。

## 0. 這份是什麼
Jim 的**主動提案型 CV**：主動申請尚未公布、應屬中高階的職位/合作。**主角＝Jim（人）**，系統只是能力佐證，不是產品簡介。寄 HR、請轉交**經營團隊／市場開發(BD) Head**。母版可換公司。首發 Inspectorio。

## 1. 鐵則
- 先給結果再問；**先討論確認方向與內容，Jim OK 才生成**；不要丟一堆沒確認的東西要他糾錯。要確認的併成一份一次給他看。
- 版面/具象圖設計＝GPT 出（Claude 寫 prompt）；**圖回來後 Claude 自己嵌入版面、做後續所有調整，不回 GPT**。GPT 只出圖那一次。
- 純文字排版不行：**每頁要有一個「一看就懂」的圖當視覺主角**，文字配角、越簡單越好、要有反差。
- 不寫對方陌生的字、不掛品牌名("SmartPN Atlas")、不用 "Founder"、不放技術術語(Python/Flask/SQLite)。
- 存檔走 Code（Claude 出工單 → Code commit/push）；Jim 檔案一律在 Downloads（C:\Users\ie5\Downloads\），工單路徑照 Downloads 寫。
- 先搞懂 scenario 邏輯再畫；不懂先問。

## 2. CV 主軸
把市場現有條碼/編碼系統**升級到製造端可用**的 innovation：製造端從 STANDARD ZERO ZONE（材料身分不一致→無共同語言→無 trusted source）轉成有 Shared Language 的 STANDARD ZONE。Jim 同時握有讓它成功的四要素能力。

## 3. 四要素
1. 對品牌的具體貢獻（用 scenario 證明；**此階段先不挑 scenario**）。
2. 結構＋Demo 已驗證，商業化經驗坦白尚缺（想得出、建得出；商業化那一哩想藉這份工作走完）。
3. 東南亞導入團隊(guider)：data provider 缺的是 guider 不是意願；系統不是導入失敗主因，人才是；Jim 能組團隊帶上線。
4. data provider 被動→主動（見第 6 節）。

## 4. 結構（目錄定案；主角＝Jim）
1. Why I'm writing — 無對應職稱、屬中高階，主動爭取任職或合作；HR 轉交經營／BD Head。
2. Who I am（三層）：L1 製造現場(會做鞋/IE/全流程)；L2 系統開發「我能把我懂的轉成系統並落地」(標準化+協調+平衡用戶與開發，不寫程式)；L3 獨立與 AI 合作，帶出兩套系統(IE & Workforce Planning ＋ an innovation: 製造業材料身分與 governance 系統)，結尾過渡到第3段。
3. Proven results — and what I can bring to you：成果一 IE(290/20,434/4/20+)；成果二 the innovation＋四要素。
4. How I'd work with you — 越南/台灣、可出差、英文非母語坦白（已刪「退休後支薪/分紅」）。
5. The ask — 謙抑，爭取任職或合作。

## 5. 版面系統（Jim 已核准）
- 16:9 白底 Inter；近黑#1D1D1F 灰#6E6E73 橘金#B5540D 灰卡#F5F5F7 線#D2D2D7。
- 頂部常駐段別導覽：Why · Who I am · Results · How I'd work · The ask；當前段橘金、其餘淺灰。
- 內容頁不放大 section title；只放頁內小標 + 圖(視覺主角) + 最少文字。加目錄頁。
- 三階層級：導覽(段)→頁內小標(頁)→內文＋橘金(帶走點)。
- 待定：導覽當前段維持橘金，或改深黑把橘金只留內文(目前先橘金)。

## 6. 「data provider 被動→主動」頁（討論到這）
- 核心是**因果**：資料能被搜尋到 → 資料有商業價值 → 供應商才從被動變主動（商業價值是因，被動/主動是果）。
- 視覺主角：GPT 的 Passive(平淡臉)→Active(興奮臉，右上橘金小爆發線)；平淡→興奮，不要負面表情。圖在 Jim 端，需重新提供。
- 這頁不放收尾句；專表達「資料有無商業價值＝被動/主動的關鍵」。
- 圖下文字(待定)候選：Searchable data has commercial value — and that is what makes a provider active.

## 7. 產出檔
- cv_builder.py — 全本 14 頁 builder（已核准版面系統；只放確認內容，P11/P12 留空）。唯一渲染來源。
- 早前 01_COPY_15pages.md / 02_GPT_template_prompts.md 為舊草稿，內容以本 STATUS＋38 為準，勿用草稿裡 Claude 自編的東西(如 GS1/PLM)。

## 8. 渲染環境（重建約 1 分鐘）
weasyprint + Inter(fontTools 切 400/500/600)。指令：
pip install weasyprint pymupdf --break-system-packages -q ；下載 Inter 可變字型 raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter[opsz,wght].ttf ；用 instantiateVariableFont 切 400/500/600 存 ~/.fonts ；fc-cache -f ~/.fonts。

## 9. 下一步
1. 收尾被動→主動頁：取得 Passive→Active 圖 → 嵌入版面＋第6節因果文字 → self-QA。
2. 逐頁同法：想一看就懂隱喻 → 確認該頁邏輯 → 寫 prompt 給 GPT → 嵌入重做。
3. 全本套視覺主角後再挑 scenario(要素①、潛在貢獻)。
