# SmartPN Atlas ??Outreach Automation Definition
Version: v1.0 | 2026-05-30
Status: Ready to build in Make. Manual testing confirmed. Automate now.

---

## Purpose

Search for outreach targets automatically.
Produce intelligence report + contact draft for each target.
Do NOT auto-send. Output drafts only.
Jim reviews and decides what to send.

---

## Target Definition

NOT journalists first.
PRIMARY TARGET: People who influence or make material sourcing and development decisions.

Who they are:
- Material buyers / sourcing managers at brands
- Material developers / product development teams
- Factory sourcing teams
- Supplier group owners
- Platform operators (Material Exchange, Foursource, etc.)
- Industry association members (FDRA, AAFA, LEFASO, TWTA)

Where they pay attention:
- Material platforms (Material Exchange, Foursource, GoSourcing365)
- Trade show announcements (Texworld, MAGIC, APLF, Premiere Vision)
- Brand new material announcements
- Supplier new product launches
- Industry association newsletters
- LinkedIn material-related posts
- Chinese/Vietnamese/Indonesian industry media

---

## Keywords (English)

Core:
- material sourcing
- raw material supplier
- material library
- material identity
- supply chain traceability
- material compliance
- DPP digital product passport
- material data management
- shared BOM
- material standardization

Industry:
- footwear manufacturing
- apparel manufacturing
- textile sourcing
- footwear supplier
- apparel supplier

Action (find latest news):
- announced
- launched
- partnership
- new material
- new collection
- sustainability report
- supplier portal
- material platform

---

## Keywords (Chinese)

- ??鞈?- ??靘???- ?平靘???- ?﹝鋆賡?- ??蝞∠?
- 靘???摨?- ?訾??Ｗ?霅瑞
- ??璅???- ?曹澈隤?
- 靘??恣??
---

## Search Scope

Media (secondary):
- Sourcing Journal
- Just Style
- WWD
- Business of Fashion
- Apparel Magazine
- Fibre2Fashion
- 蝝∠???蝬莎?Chinese嚗?- ?啁蝝⊥???TTPA嚗?- LEFASO嚗ietnam嚗?
Platforms (primary):
- Material Exchange
- Foursource
- Texweb
- LinkedIn (material sourcing posts)

Brand announcements:
- Nike, Adidas, H&M, Zara, Gap, PVH, VF Corporation
- Any brand announcing new material initiative or supplier portal

Supplier announcements:
- Any supplier announcing new material launch or certification

---

## Output Format Per Target

For each target found, produce:

### Intelligence Report
[Target] Name / Title / Organization / URL
[Recent Activity] One sentence: what did they just publish or announce?
[Summary] 2-3 sentences: what are they focused on right now?
[Key Paragraph] 潃?Most relevant quote or finding, clearly marked
[SmartPN Entry Point] One paragraph: how do we enter their world?

### Contact Draft
Follow 22_WRITING_RULES.md exactly:
- Start with recognition/resonance (we agree with you)
- Build the logic chain
- STANDARD ZERO ZONE
- SHARED LANGUAGE alone is not enough
- SHARED LANGUAGE + GOVERNANCE LAYER
- Close with ask (evaluate / report / discuss)
- Signature: Jim / Founder SmartPN Atlas / LinkedIn only

Tone adjustment by target type:
- Journalist/editor: ask them to report on the angle
- Platform operator: ask about collaboration or listing
- Brand sourcing team: position as solution to their pain
- Supplier group owner: position as revenue opportunity

---

## Make Automation Flow

Step 1: Search (Claude API or web search tool)
- Run keywords against target scope
- Find items published in last 7 days
- Filter: must have a named person or organization

Step 2: Intelligence Report (Claude API)
- Feed article/announcement to Claude
- Produce standard intelligence report format
- Tag: journalist / platform / brand / supplier

Step 3: Contact Draft (Claude API)
- Use intelligence report as input
- Apply 22_WRITING_RULES.md
- Produce draft in correct language (English or Chinese)
- Apply correct tone for target type

Step 4: Output
- Save to Google Sheet or Airtable
- Columns: Date / Target / Type / URL / Intelligence Summary / Contact Draft / Status
- Status options: Draft / Jim Review / Approved / Sent / Replied

Step 5: Notify Jim
- Send summary email when new batch is ready
- Jim opens Google Sheet, reviews, decides what to send

---

## What Changes Over Time

Fixed (never change):
- Logic chain structure
- Writing rules
- Output format
- Tone rules

Variable (update as needed):
- Keywords (add/remove based on results)
- Target scope (add new platforms or media)
- Language mix (add languages if expanding to new markets)

---

## Confirmed Drafts Ready to Send

1. Shoe-In Show ??CONFIRMED, Jim already sent
2. Kate Nishimura (Sourcing Journal Deputy Editor) ??DRAFT READY, pending Jim review
3. All others ??pending automation output

---

## Kate Nishimura Draft (Ready for Review)

Subject: Your traceability report resonated ??but even worse in footwear and apparel

Hi Kate,

My name is Jim, from Taiwan.

I read Sourcing Journal and Oritain's traceability report with great interest.

The finding that more than 60% of brands have no visibility beyond Tier 1 resonated deeply with me.

But in footwear and apparel manufacturing specifically ??it's closer to zero.

Even Tier 1.

Not because brands don't want visibility. Not because the industry doesn't know the direction.

Everyone knows that building a SHARED LANGUAGE for raw materials ??giving every material a consistent identity across brand, factory, and supplier ??is the right path forward.

So why is the industry still in what I call the STANDARD ZERO ZONE?

Because SHARED LANGUAGE alone only solves half the problem.

A shared language means 100% open data. Pick up a shoe, scan it, and everything is visible ??material specs, unit prices, confidential formulas.

NO ONE WOULD LIKE TO SHARE THEIR BUSINESS SECRETS.

This is exactly why the industry remains stuck. The direction is right. But without a GOVERNANCE LAYER, it cannot scale in the real world.

The real solution is SHARED LANGUAGE + GOVERNANCE LAYER ??where you see only what you're authorized to see.

This is a problem the entire industry knows exists but has never been able to solve. I believe there is now a solution worth reporting on.

I have spent 20 years on the manufacturing side of footwear and apparel. My most meaningful work was standardizing the full operating process of a footwear manufacturing group into PDM and ERP systems. That experience is why I understand this problem at its root ??and why I believe this solution can finally move the industry forward.

I'd be happy to share more if you feel this is worth exploring for your readers.

Jim
Founder, SmartPN Atlas
https://www.linkedin.com/in/jim-k-969579339/
