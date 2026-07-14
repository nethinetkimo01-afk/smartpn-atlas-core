# 44｜SmartPN 交換機制規格（產品本體）
Status: DRAFT。起因：Demo v3 有畫面無機制。43號檔管治理原則，本檔管運作機制。

## 零、定義
SmartPN 是欄位級的授權交換層：料號是身份，欄位是貨品，授權是合約，交換是履約，證據是收據。
資料不集中；SmartPN 只讓「誰能看到誰的哪一群欄位」有秩序、可追溯、可撤銷。

## 一、欄位分組（交換的最小單位）
六群：IDENTITY（料號/品名/類別/供應商）、PHYSICAL（克重/幅寬/厚度/成分/色牢度）、
PROCESS（加工方式/二次加工鏈/良率）、COMPLIANCE（第三方認證/效期/報告編號）、
CUSTOMS（HS code/原產地/關務代碼）、FINANCE（報價/幣別/付款條件/MOQ價階）。
同群對映鐵則：授權、比對、對映一律同群對同群。FINANCE 只能對映 FINANCE，PHYSICAL 只能對映
PHYSICAL。跨群禁止——防止用物性反推成本的結構性保護。
三態權限（每個欄位群 × 每個對象）：PUBLIC / PRIVATE / GRANTED(對象, 到期日)。
預設 IDENTITY=PUBLIC，其餘=PRIVATE。產品層禁止全域公開 FINANCE。

## 二、存取申請狀態機
REQUESTED --supplier approve--> ACTIVE --expiry/revoke--> EXPIRED
REQUESTED --supplier reject--> REJECTED
ACTIVE --supplier revoke(隨時,單方)--> REVOKED
REQUESTED --supplier counter--> CONDITIONAL（附條件核准：僅某群、限天數、不得轉授）
AccessRequest: id/requester(公司·單位·帳號三層)/owner/scope(材料集或全目錄)/groups[]/purpose/duration/created_at
Grant: id/request_id/groups[]/scope/expires_at/transferable=false/conditions[]
規則：
1. 未授權的欄位群，在索取方任何畫面與 API 都「不存在」——不是灰掉，是不存在（含搜尋/比對/下拉/匯出/API）
2. 供應商隨時可撤銷，即時生效；歷史值不追回，但停止同步且索取方標記「已撤銷，值為快照」
3. 到期前14天雙方提醒；到期自動停止同步
4. 每個狀態轉換都是一筆事件

## 三、物性與單位（PHYSICAL 資料模型）
Property { key, value, unit, method, tolerance, source{system,authority,sync_at,cached} }
key 例：weight/width/thickness/composition/colorfastness；composition 為 [{material,pct}]
Unit Registry：每個 key 綁合法單位集與換算率（g/m² ↔ oz/yd²、cm ↔ inch）。存一套、顯示多套。
必填集依類別：Textile（克重/幅寬/成分/色牢度）、Leather（厚度/面積/鞣製法）、
Chemical（固含量/黏度/VOC）。必填未齊 → DPP 就緒度 <100%，可上架但不可被 DPP 引用。
可比對條件：同 key + 同單位（換算後）+ 同 method。method 不同 → 顯示「不可比：量測方法不同」，
不給相似度分數（FSM 不騙人的底線）。

## 四、交換（Exchange）
定義：在一個 ACTIVE 授權下，把某欄位群的值從持有方傳遞到索取方，雙方各留不可否認記錄。
三模式：PUSH（供應商推）/ PULL（即時拉，值常變如報價）/ CACHED（快照+新鮮度，供應商無API）
ExchangeEvent { id, grant_id, from, to, material_ids[], groups[], mode, field_count, at,
payload_hash: sha256(值內容), source_system, initiated_by }
關鍵：SmartPN 存收據不存貨。爭議時雙方拿各自的值比 hash——這就是「非中央庫」的技術含義。
存證（選配）：開啟後 ExchangeEvent 進 append-only 日誌，可導出稽核；關閉只留最近 N 筆對帳。

## 五、API 對接
1. 認證：每公司 api_key+secret，scope 限定（哪些材料、哪些群、讀或寫）；可撤銷可輪替。
2. 欄位對映表（接得起來的關鍵）：
   { their:"MAT_WT_GSM", ours:"PHYSICAL.weight", unit_from:"g/m2", transform:null }
   { their:"ITEM_NO", ours:"IDENTITY.spn", match:"exact" }
   { their:"PRICE_USD", ours:"FINANCE.price", currency:"USD", requires_grant:true }
   Mapping 分批驗收（照43號D4）：財務批/關務批/物性批各自簽署；未簽署=不流通；
   簽署方=資料提供方，承擔該批資料正確性責任。
3. 端點最小集：
   GET  /v1/materials?updated_since=
   GET  /v1/materials/{spn}/fields?groups=PHYSICAL,COMPLIANCE
   POST /v1/materials/{spn}/fields        (需 owner 金鑰)
   GET  /v1/grants
   POST /v1/access-requests
   GET  /v1/exchange-events?since=
   每個回應帶 source{system,authority,sync_at,cached}——欄位級來源鏈是 API 一等公民。
4. 失敗與權威：PULL 失敗→回上次快照+stale=true，不假裝有值；多來源衝突→authority 高者勝
   （供應商 > 工廠 > 品牌快取），衝突留事件；對方無 API → CACHED + 人工上傳 + 新鮮度警示。

## 七、實作順序
1. MOCK_WORLD 擴充成本檔資料模型（fieldGroups/accessRequests/grants/properties+units/
   exchanges/apiSpec+mappings）
2. 三鏈路必須真的能點完：
   A 申請鏈：品牌選材料→選群→填用途/期限→送出 → 供應商核准(可附條件) → 品牌側該群欄位「從無到有」
   B 交換鏈：授權下按交換→產生 ExchangeEvent→雙方存證清單各出現一筆(hash相同)→供應商撤銷→
     品牌側標快照、停止同步
   C 對接鏈：供應商設 Mapping→分批簽署→未簽批次標「不流通」→簽了才在品牌側可見
3. 物性頁：單位下拉受 Unit Registry 約束、method 必填、缺必填顯示 DPP 就緒度不足
4. FSM：method 不同→明示「不可比」，不給相似度
5. 死按鈕歸零；引導腳本改走 A→B→C
驗收＝node real_click_test.js 兩檔全綠（死按鈕0、引導5步、機制五項全有）
