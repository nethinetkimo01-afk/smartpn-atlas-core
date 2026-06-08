# SmartPN Atlas ??Design System
Version: v1.1 | 2026-06-08
Status: Locked. All outputs must follow this system.

## Brand Positioning (LOCKED)
Primary slogan: Governed Shared Language in the STANDARD ZERO ZONE.
OLD slogan (REJECTED): One ID Across Brand, OEM and Supplier

## Three Visual Systems

### System 1: Demo Software + PPT Slides
Purpose: Customer presentation and product demo
Style: Clean, white, shopping website feel (Amazon / eBay reference)

Colors:
- Background: #FFFFFF
- Surface (subtle): #FAFAF8
- Subtle bg: #F5F5F3
- Primary text: #1A1A1A
- Secondary text: #666666
- Muted text: #999999
- Accent (SmartPN): #54463A
- Border: #E5E5E5
- Row highlight: #FAFAF8
- Open/Active: #3B6D11 (text) / #EAF3DE (background)
- New/Info: #185FA5 (text) / #E6F1FB (background)
- Today: #854F0B (text) / #FFF3E0 (background)
- Private: #888888 (text) / #F5F5F5 (background)

Typography (Inter font):
- Page title: 20px weight 500 color #1A1A1A
- Section label: 10px weight 500 uppercase letter-spacing 0.1em color #999
- Table header: 9px weight 500 uppercase letter-spacing 0.08em color #999
- Body: 12px weight 400 color #1A1A1A
- Accent body: 12px weight 500 color #54463A
- Big number: 48px weight 500 color #54463A

Tags/Badges:
- Open: bg #EAF3DE text #3B6D11
- Private: bg #F5F5F5 text #888 border #E0E0E0
- New today: bg #E6F1FB text #185FA5
- Today: bg #FFF3E0 text #854F0B

Table rules:
- Header border: 0.5px #E5E5E5
- Row border: 0.5px #F0F0F0
- Row highlight bg: #FAFAF8
- Use rowspan for repeating entities

Emphasis rule:
- General content: follow design system
- Points needing special attention: BREAK the rules
- Use red large text, strong background color, or any high-contrast method
- Purpose: customer eye goes there immediately without reading

PPT animation rule:
- One sentence you say = one animation step
- Each step reveals only what you are talking about at that moment
- Never show everything at once
- Customer should not need to read, only react

### System 2: LinkedIn Images
Purpose: Attract strangers, stop the scroll
Style: Fun, cute, high impact, not boring

Layout:
- Background: white, clean
- Left side: Jim 3D cartoon avatar (large head, expressive face)
- Right side: Text (category tag + main headline + subtitle)
- Bottom right: SmartPN Atlas + positioning line
- Top left: cr logo mark

Typography for LinkedIn:
- Category tag: small, colored (e.g. Footwear and Apparel:)
- Main headline: large, bold, black, high impact
- Subtitle: smaller, italic or regular
- Brand name: SmartPN Atlas in accent color

Avatar rules:
- Do NOT regenerate Jim avatar from scratch
- Use ChatGPT feature analysis to reproduce expressions
- Same base character, different expressions per post
- Avatar feature file: see 12_AVATAR_FEATURES.md (when available)

Content rules:
- Image purpose: attract attention, not explain function
- One strong idea per image
- Make viewer curious enough to read the caption
- End caption with: come to SmartPN Atlas to learn more

### System 3: Internal Scenario Tables (DEPRECATED)
- Black background + lime green #deff9a
- Status: REJECTED for customer-facing use
- Only existed in Gemini version
- Do not use

## Slogan Usage
Main positioning: Governed Shared Language in the STANDARD ZERO ZONE.
- STANDARD ZERO ZONE must always be ALL CAPS when used as a unit
- Do not write Standard Zero Zone (mixed case) - inconsistent
- Can use full slogan or just STANDARD ZERO ZONE as anchor phrase

## Apple 風格視覺方向（2026-06-08 加入）

適用範圍：Demo Software UI、Admin 後台介面、未來 SaaS 介面

### 核心原則
- 大量留白，內容呼吸感優先
- 去除所有裝飾性元素，只留功能性視覺
- 字重層次清晰：標題重、正文輕、輔助文字更輕

### 色彩
- 背景：純白 #FFFFFF 或系統灰 #F5F5F7
- 卡片/浮層：白色 + 極淡陰影（box-shadow: 0 2px 12px rgba(0,0,0,0.08)）
- 強調色：保留 SmartPN #54463A，搭配系統藍 #0071E3（互動元素）
- 避免大面積彩色區塊

### 字型
- 主字體：-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif
- 標題：24–32px weight 600, letter-spacing -0.02em
- 副標題：16–18px weight 500
- 正文：14px weight 400, line-height 1.6
- 輔助文字：12px weight 400, color #86868B

### 元件規則
- 圓角：12px（卡片）/ 8px（按鈕）/ 6px（標籤）
- 按鈕：填色按鈕用 #0071E3，文字白色；次要按鈕用白色 + border #D2D2D7
- 輸入框：1px border #D2D2D7，focus 時 border #0071E3 + 淡藍光暈
- 表格：無邊框，行間分隔用 #F5F5F7 底色交替
- 圖示：SF Symbols 風格（線條輕、無填色）

### 動效
- 過渡：ease-out，duration 200–300ms
- 不用彈跳、不用複雜路徑動畫
- Hover：輕微 scale(1.01) 或 background 淡化

## What Comes Next
- 12_AVATAR_FEATURES.md: Jim avatar visual features (from ChatGPT analysis)
- LinkedIn image template per scenario
- PPT animation template per scenario
- Demo screen per scenario
