# SmartPN Atlas ??S02 to S17 Complete Specifications
Version: v1.0 | 2026-05-29
Source: 2026-05-27_scenario_ppt_page_specification_v6.md
Status: ALL CONFIRMED. Do not modify without Jim approval.

Key finding: No animation logic exists for any scenario. Use Minimum demo interactions instead.

---

## S02 ??Shared Language and Shared BOM

Title: Shared language and Shared BOM.

Core: Proves two things simultaneously:
1. Shared language: same material recognized across brand, factory, supplier
2. Shared BOM: combined material + source materials BOM structure consistent across all parties

Current table:
Role | BOM line | Combined material ID | Description | Source 1 | Source 2
Brand | Upper mesh panel | BR-COMP-7788 | Laminated black mesh | BR-MAT-7781 | BR-FILM-4420
Factory | Upper mesh panel | FAC-COMP-7008 | Laminated black mesh | FAC-M-2039 | FAC-FILM-445
Supplier | Upper mesh panel | SUP-COMP-610 | Laminated black mesh | SUP-A-991 | SUP-B-330

After table:
Role | BOM line | Unified combined ID | Description | Unified source 1 | Unified source 2
Brand | Upper mesh panel | SPA-COMP-0101 | Laminated black mesh | SPA-MAT-0001 | SPA-MAT-0002
Factory | Upper mesh panel | SPA-COMP-0101 | Laminated black mesh | SPA-MAT-0001 | SPA-MAT-0002
Supplier | Upper mesh panel | SPA-COMP-0101 | Laminated black mesh | SPA-MAT-0001 | SPA-MAT-0002

Demo screens: material identity mapping table, local ID list by role, Shared BOM view, combined + two source materials

---

## S03 ??Shared Language Across Product Lines Under One Brand

Title: Shared language across product lines under one brand.

Core: One brand has footwear/apparel/bags product lines. Each maintains own material IDs. After SmartPN Atlas, same material connects to one identity across all product lines.

Current table:
Brand | Product line | Local ID | Material
Brand A | Footwear | SHOE-MAT-118 | Black recycled polyester mesh
Brand A | Apparel | APP-MAT-552 | Black recycled polyester mesh
Brand A | Bags | BAG-MAT-907 | Black recycled polyester mesh

After table:
Brand | Product line | Local ID | SmartPN Atlas ID | Material
Brand A | Footwear | SHOE-MAT-118 | SPA-MAT-0001 | Black recycled polyester mesh
Brand A | Apparel | APP-MAT-552 | SPA-MAT-0001 | Black recycled polyester mesh
Brand A | Bags | BAG-MAT-907 | SPA-MAT-0001 | Black recycled polyester mesh

Demo screens: product line switcher/filter, material identity mapping table, local IDs by product line, shared SmartPN Atlas ID

---

## S04 ??Shared Language Across Brands and Product Lines Under One Group

Title: Shared language across brands and product lines under one group.

Core: Group with multiple brands, each with multiple product lines. After SmartPN Atlas, same material visible at group level across all brands and product lines.

Current table:
Group | Brand | Product line | Local ID | Material
Group A | Brand A | Footwear | A-SHOE-MAT-118 | Black recycled polyester mesh
Group A | Brand A | Apparel | A-APP-MAT-552 | Black recycled polyester mesh
Group A | Brand B | Footwear | B-SHOE-MAT-778 | Black recycled polyester mesh
Group A | Brand B | Bags | B-BAG-MAT-411 | Black recycled polyester mesh

After table:
Group | Brand | Product line | Local ID | SmartPN Atlas ID | Material
Group A | Brand A | Footwear | A-SHOE-MAT-118 | SPA-MAT-0001 | Black recycled polyester mesh
Group A | Brand A | Apparel | A-APP-MAT-552 | SPA-MAT-0001 | Black recycled polyester mesh
Group A | Brand B | Footwear | B-SHOE-MAT-778 | SPA-MAT-0001 | Black recycled polyester mesh
Group A | Brand B | Bags | B-BAG-MAT-411 | SPA-MAT-0001 | Black recycled polyester mesh

Demo screens: group/brand/product-line filters, material identity mapping table, local IDs by brand, shared SmartPN Atlas ID

---

## S05 ??Shared BOM vs Actual BOM vs Actual DPP

Title: Shared BOM vs Actual BOM vs Actual DPP.

Core: Brand issues same Shared BOM to different factories. Factory may substitute source material if brand-approved. SmartPN Atlas makes differences visible. DPP source data should be based on factory actual BOM.

Boundary: SmartPN Atlas is NOT DPP compliance authority. Only proves downstream DPP data based on actual factory BOM is more credible.

Brand Shared BOM:
BOM line | Shared BOM ID | Material name | Source 1 | Source 2
Upper mesh panel | SPA-COMP-0101 | Laminated black mesh | SPA-MAT-0001 | SPA-MAT-0002

Factory Actual BOM:
Factory | BOM line | Actual combined ID | Actual source 1 | Actual source 2 | Difference
Factory A | Upper mesh panel | SPA-COMP-0101 | SPA-MAT-0001 | SPA-MAT-0002 | No difference
Factory B | Upper mesh panel | SPA-COMP-0101-B | SPA-MAT-0001 | SPA-MAT-0048 | Source 2 changed

DPP source data:
Factory | DPP basis | Material used | Credibility
Factory A | Actual BOM | SPA-COMP-0101 + 0001 + 0002 | Matches Shared BOM
Factory B | Actual BOM | SPA-COMP-0101-B + 0001 + 0048 | Brand-approved local replacement

Demo interactions: Select Factory A (matches), Select Factory B (highlight source 2 changed to SPA-MAT-0048), Show Factory B DPP uses SPA-MAT-0048

---

## S06 ??Forecast Volume for Next-Season Negotiation

Title: Forecast volume for next-season negotiation.

Core: Brand uses SmartPN Atlas structured material identity + usage data to calculate next-season negotiation reference volume. SmartPN Atlas does NOT create forecast. It provides structured identity + usage data for brand to calculate.

Current:
Material group | Local IDs | SS quantity | Source
Black recycled polyester mesh | BR-MAT-7781/FAC-M-2039/SUP-A-991 | 120,000m | Supplier collected report

After:
SmartPN group | Mapped local IDs | SS quantity | FW forecast reference | Calculation source
SPA-GRP-0001 | BR-MAT-7781/FAC-M-2039/SUP-A-991 | 120,000m | 180,000m | Brand calculation using SmartPN Atlas data

Demo interactions: Select SPA-GRP-0001, Show mapped IDs, Show SS 120k, Show FW forecast 180k, Show brand calculated this

---

## S07 ??0 Communication Gap

Title: 0 communication gap.

Core: Two scenarios:
A: Brand design/development communicates material needs with factory/supplier ??different IDs cause repeated confirmation
B: Product transfers from Factory A to Factory B ??different factory local IDs cause communication gap

After SmartPN Atlas: local IDs preserved, shared SmartPN Atlas ID removes ambiguity.

Boundary: Does not mean people never need to communicate. Only means material identity/BOM reference gap is removed or greatly reduced.

Current A:
Role | Local ID | Material | Communication result
Brand design | BR-MAT-7781 | Black recycled polyester mesh | Sends design reference
Factory | FAC-M-2039 | Black RPET mesh | Needs to confirm if same material
Supplier | SUP-A-991 | Recycled polyester mesh black | Needs to confirm against supplier record

Current B:
Transfer step | Factory | Local ID | Communication result
Original | Factory A | FAC-A-COMP-7008 | Factory A knows its own BOM
Transfer | Factory B | FAC-B-COMP-4410 | Factory B must re-confirm equivalent material

After A:
Role | Local ID | SmartPN Atlas ID | Communication result
Brand design | BR-MAT-7781 | SPA-MAT-0001 | Same shared reference
Factory | FAC-M-2039 | SPA-MAT-0001 | Same shared reference
Supplier | SUP-A-991 | SPA-MAT-0001 | Same shared reference

After B:
Transfer step | Factory | Local ID | SmartPN Atlas BOM ID | Communication result
Original | Factory A | FAC-A-COMP-7008 | SPA-COMP-0101 | Same Shared BOM reference
Transfer | Factory B | FAC-B-COMP-4410 | SPA-COMP-0101 | Same Shared BOM reference

Demo interactions: Show Current (different IDs, needs confirmation), Switch to After (all mapped to SPA-MAT-0001), Show Factory A to B transfer both mapped to SPA-COMP-0101

---

## S08 ??Supplier Group Owner Sees Sales Analysis and Collection Analysis

Title: Supplier group owner sees sales analysis and collection analysis.

Core: Supplier group owner / boss view.

Boundary (Jim confirmed):
- NO unit price vs cost comparison
- NO gross margin analysis
- NO sales comparison by brand
- NO brand-level sales dashboard
Reason: Supplier commercial target is factory, not brand. Support product group + customer/factory company sales analysis only.

KPIs:
- Sales volume by product group
- Customer/factory company share by subsidiary or country
- Expected monthly collection amount

Sales Analysis:
Supplier subsidiary | Country | Product group | Customer | Sales volume | Sales amount
Supplier Vietnam Co. | Vietnam | Recycled polyester mesh group | Factory Group A | 120,000m | 240,000
Supplier Indonesia Co. | Indonesia | Recycled polyester mesh group | Factory Group B | 80,000m | 168,000

Collection Analysis:
Factory company | Payment terms | AR amount | Expected collection month | Expected amount
Factory A Vietnam Ltd. | Net 60 | 80,000 | 2026-06 | 80,000
Factory B Indonesia Ltd. | Net 45 | 60,000 | 2026-05 | 60,000

Unit Price Maintenance:
Product group | Local ID | Factory company | Unit price | Currency | Valid from | Valid to
Recycled polyester mesh | SUP-A-991 | Factory A Vietnam | 2.00 | USD/m | 2026-01 | 2026-06
Recycled polyester mesh | SUP-A-991-V2 | Factory B Indonesia | 2.10 | USD/m | 2026-01 | 2026-06

Demo screens: parent/subsidiary maintenance, factory company/customer master, sales dashboard, collection dashboard, unit price maintenance, filters by subsidiary/country/product group/customer/month

---

## S09 ??Supplier Controls When to Publish Material Data and Who Can See It

Title: Supplier controls when to publish material data and who can see it.

User roles:
- Supplier editor: Create/edit/save draft/submit for review
- Supplier reviewer: Review/request revision/approve
- Supplier publisher/admin: Publish/manage permissions
- Brand user: See only published or authorized data
- Non-brand user: See only supplier-opened published data

Workflow:
Step | Status | Action | Who
1 | Draft | Edit | Supplier editor
2 | Saved draft | Save | Supplier editor
3 | Pending review | Submit | Supplier editor
4 | Approved | Approve | Supplier reviewer
5 | Published | Publish | Supplier publisher/admin

Demo data: material local ID=supplier-code, unified-01, unified name 01, editor-01, reviewer-01, publisher-01

Demo interactions: editor-01 edits/saves/submits, reviewer-01 approves, publisher-01 publishes, switch to Brand user (sees it), switch to Non-brand user (cannot see it)

---

## S10 ??Brand Finds Identical and Alternative Materials Faster

Title: Brand finds identical and alternative materials faster.

Search logic:
- Identical material: same SPU + same SKU
- Alternative material: same SPU + different SKU

Selected material: SPU=spu-01, SKU=sku-01, name=unified name 01, supplier=supplier-01, LT=30 days

Identical result:
Supplier | SPU | SKU | Name | Lead time | Type
supplier-02 | spu-01 | sku-01 | unified name 01 | 20 days | identical, shorter LT

Alternative result:
Supplier | SPU | SKU | Name | Lead time | Type
supplier-03 | spu-01 | sku-02 | alternative name 01 | 15 days | alternative material

Demo interactions: Select unified name 01, Click Search identical (same spu-01+sku-01, highlight 30->20 days), Click Search alternative (same spu-01 different sku-02)

---

## S11 ??Factory Reduces Excess Material by Finding Reuse and Resale Options

Title: Factory reduces excess material by finding reuse and resale options.

Current:
Factory | Material ID | Name | Excess qty | Status
factory-01 | factory-code | unified name 01 | 1 | excess material

After:
Factory | Material ID | Name | Excess qty | Option 1 | Option 2 | Option 3
factory-01 | unified-01 | unified name 01 | 1 | sell back to supplier-01 | transfer to factory-02 | sell to factory-03

Permission:
- Factory group owner: see excess across group factories
- factory-01 user: see and list own excess
- factory-02 user: see group-transfer option if authorized
- supplier-01 user: see sell-back option if authorized
- non-authorized factory: cannot see excess material

Demo interactions: Switch to factory-01, show excess factory-code qty 1, map to unified-01, show handling options, switch user to show permission control

---

## S12 ??Same Product and Same QR Code Can Have Different DPP Composition

Title: Same product and same QR code can have different DPP composition.

Core: Same product, same QR code, different raw material supplier = different composition. DPP composition must be based on actual source data.

Boundary: SmartPN Atlas is NOT complete DPP platform or regulatory compliance authority.

Product: product-01, QR code: qr-01, BOM line: material group 01

Composition by batch:
Case | Product | QR | Raw material | Supplier | Composition
Batch A | product-01 | qr-01 | raw material 01 | supplier-01 | 60% recycled polyester / 40% TPU
Batch B | product-01 | qr-01 | raw material 01 | supplier-02 | 55% recycled polyester / 45% TPU

Demo interactions: Select product-01, show qr-01, Select Batch A (supplier-01, 60/40), Select Batch B (supplier-02, 55/45), highlight same QR but different composition

---

## S13 ??Supplier Can Exchange Required Data Without Understanding Every Regulation

Title: Supplier can exchange required data without understanding every regulation.

Core: Supplier follows SmartPN Atlas field guidance instead of reading every regulation. Mapped data from existing systems, unmapped data maintained in SmartPN Atlas.

Platform positioning:
- NOT forced central database (supports mapping-based exchange + optional hosted fields)
- Supplier follows field guidance, not full regulation knowledge
- SmartPN Atlas complements weak supplier systems

Demo data fields:
- product-code: from supplier system (mapped)
- material-code: from supplier system (mapped)
- composition: stored in SmartPN Atlas (supplier system cannot map)
- recycled content: stored in SmartPN Atlas
- evidence-file: stored in SmartPN Atlas

Demo interactions: Show mapped fields, show missing fields, supplier fills missing fields in guided form, exchange readiness changes from missing to ready, show complete field set ready for exchange

---

## S14 ??Supplier Prepares Exchange-Ready Data While Controlling Authorization

Title: Supplier prepares exchange-ready data while controlling authorization.

Core: Data exchange authorization is controlled by supplier. SmartPN Atlas provides structure, mapping, readiness view, guided checklist, permission tools. Supplier prepares data and decides authorization.

Responsibility split:
Area | SmartPN Atlas role | Supplier control
Field structure | Provides structure and guidance | Decides when to complete
Mapping | Supports mapping | Owns source data
Missing fields | Provides guided fields | Decides whether to maintain
Readiness | Shows ready/missing status | Confirms completion
Authorization | Provides permission tools | Decides what to exchange and with whom

Demo data:
- product-code: mapped, ready, authorized to partner-01
- material-code: mapped, ready, authorized to partner-01
- composition: SmartPN Atlas, ready, authorized to partner-01
- evidence-file: SmartPN Atlas, ready, NOT authorized yet

Demo interactions: Switch to supplier, show ready/missing fields, complete guided field, mark selected fields authorized for partner-01, keep evidence-file not authorized, switch to partner (sees only authorized fields)

---

## S15 ??Supplier Shortens New Material Launch Time

Title: Supplier shortens new material launch time.

Workflow: Save -> Submit for review -> Approve -> Publish -> Permission settings

Audience title split:
- Supplier view: Supplier shortens new material launch time.
- Brand view: Brand obtains new material information faster. (= S16)

Demo data: supplier-01, supplier-code-new-01, unified-new-01, new material name 01, Published, visible to brand-01 and factory-01

Demo interactions: Supplier creates new material, saves/submits, reviewer approves, publisher publishes, supplier sets visibility to brand-01+factory-01, switch to brand user (sees it), switch to non-authorized user (cannot see it)

---

## S16 ??Brand Obtains New Material Information Faster

Title: Brand obtains new material information faster.

Core: Same source as S15, brand audience perspective.

Same demo data as S15.

Proof:
- Brand authorized user sees published new material after supplier opens visibility
- Non-authorized users cannot see new material
- Save/approve/publish/permission settings remain separate

Demo interactions same as S15 especially: switch to brand user (show new material), switch to non-authorized user (not visible)

---

## S17 ??Brand Creates Development and Purchasing Reference from Supplier Performance Comments

Title: Brand creates development and purchasing reference from supplier performance comments.

Core: Brand users leave comments on raw material supplier performance. Comments can be private (same company) or public/shared (per permission settings). Replaces offline supplier performance feedback.

Key insight for open spec: When two suppliers sell identical material, lowest-price supplier with unstable quality/delivery still creates losses. SmartPN Atlas lets viewer immediately see supplier performance difference.

Comment visibility:
- Private: only same company users see it
- Public/shared: visible to users allowed by permission settings

Demo data:
Material | Supplier | Rating | Reason | Visibility
unified name 01 | supplier-01 | 5 stars | stable quality/delivery | private to brand-01
unified name 01 | supplier-02 | 1 star | unstable quality/delivery | private to brand-01

Report:
Material | Supplier 1 | Supplier 2 | Difference
unified name 01 | supplier-01 / 5 stars | supplier-02 / 1 star | quality and delivery stability

Demo interactions: Select unified name 01, show both suppliers selling same material, add comment for supplier-01 (5 stars, private to brand-01), add comment for supplier-02 (1 star), show brand-01 sees both, switch to another company user (private comments not visible)

---

## Summary

All S02-S17: CONFIRMED EXISTS
External titles: CONFIRMED for all
Scripts/core ideas: CONFIRMED for all
Table/number designs: CONFIRMED for all
Animation logic: DOES NOT EXIST for any scenario
Minimum demo interactions: CONFIRMED for all
Latest source: 2026-05-27_scenario_ppt_page_specification_v6.md
