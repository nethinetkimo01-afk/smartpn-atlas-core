# SmartPN Atlas ??Supplier Revenue Package and Scenario Matrix
Version: v1.0 | 2026-05-29
Status: Active. Short-term revenue priority. Pending alignment with 17 Scenario system.

---

## Core Sales Logic

Target: Supplier Group Owner (Boss)
Entry point: Help boss see subsidiaries, products, customers, prices, certifications in one controlled view.
Revenue path: If view is useful ??boss follows SmartPN Atlas data steps ??short-term service revenue + future database foundation.

Data build sequence:
1. Product / Material ID Integration
2. SPU / SKU Separation
3. Subsidiary Product Sales Detail
4. Brand Certification / Approval
5. Unit Price Records

---

## 5 Audiences

1. GTS / Data Exchange Partner
2. Supplier Group Owner / Boss View
3. Supplier Sales / Supplier Team
4. Brand
5. OEM / Factory Group

Core rule: Same underlying data. Different permission-controlled views. SmartPN Atlas is controlled visibility, not full transparency.

---

## 23 Scenarios Master List

### GTS / Data Exchange Partner (4 scenarios)

GTS-01: Manufacturing-Side Source Data Readiness
- Question: Can SmartPN Atlas prepare supplier-maintained data before trusted exchange?
- Value: GTS can move trusted data. SmartPN Atlas makes manufacturing-side data ready before exchange.

GTS-02: Hosted Readiness Mode vs Data Exchange Mode
- Question: Is SmartPN Atlas a forced central database?
- Value: SmartPN Atlas can host readiness data OR prepare data exchange. No forced central system.

GTS-03: QR / DPP Output Proof From Source Fields
- Question: Can downstream output reuse supplier-maintained source fields?
- Value: Trusted outputs require trusted data at the source.

GTS-04: Shared BOM And Secondary Processing
- Question: Can GTS understand why manufacturing BOM needs more than raw material records?
- Value: SmartPN Atlas brings manufacturing-side BOM logic including secondary processed materials.

### Supplier Group Owner / Boss View (6 scenarios)

BOS-01: Group Executive Overview
- Question: What does the supplier group owner control today across subsidiaries, products, customers, prices?
- Value: Owner sees the group as one business instead of separate local files.

BOS-02: Subsidiary Product Map
- Question: Which subsidiary sells which product family and SKU?
- Value: Product overlap and gaps visible at group level.

BOS-03: Customer Product Sales Detail
- Question: Which customer buys which product from which subsidiary?
- Value: Owner sees customer concentration and cross-sell opportunities.

BOS-04: Brand Certification / Approval Dashboard
- Question: Which products are already approved for which brands?
- Value: Sales teams know what can be sold immediately and what needs renewal.

BOS-05: Customer-Specific Price History
- Question: How does price change by customer, subsidiary, and time?
- Value: Owner controls price discipline and validity risk.

BOS-06: SmartPN Atlas Data Readiness Score
- Question: Which data fields are still missing before supplier can serve brands better?
- Value: SmartPN Atlas turns data cleanup into a clear work plan.

### Supplier Sales / Supplier Team (4 scenarios)

SUP-01: New Material Online Publication
- Question: Can supplier publish new material without waiting for material fair?
- Value: New material exposure becomes continuous, not event-based.

SUP-02: Customer-Specific Visibility
- Question: Can supplier decide which customer sees which fields?
- Value: Shared identity does not mean uncontrolled disclosure.

SUP-03: Requirement Guidance
- Question: Can supplier follow SmartPN Atlas prompts instead of reading every policy document?
- Value: Supplier focuses on completing the right source data.

SUP-04: Price History By Brand / Customer / Time
- Question: Can supplier see price changes by customer over time?
- Value: Supplier manages pricing as structured data, not scattered quote files.

### Brand (5 scenarios)

BRD-01: Material Identity Across Brand / OEM / Supplier
- Question: Is same material represented consistently across different systems?
- Value: Same material can mean the same thing even when each party keeps its own ERP.

BRD-02: Price Transparency
- Question: Does brand know whether same material carries hidden price gaps across OEMs?
- Value: Brand moves from passive supplier-provided numbers to its own controlled visibility.

BRD-03: Group Purchasing / Volume Negotiation
- Question: Can brand group calculate total planned material volume across OEMs?
- Value: Brand plans negotiation using cross-OEM and cross-product visibility.

BRD-04: Alternative Material / Shorter Lead Time
- Question: Can brand find same or similar material with shorter lead time?
- Value: Fast-fashion sourcing reduces time-to-market by searching source data instead of asking offline.

BRD-05: DPP / Compliance Credibility From Source Data
- Question: Can downstream compliance output rely on supplier-maintained source data?
- Value: DPP is an output example. Core is trusted source data and shared identity.

### OEM / Factory Group (3 scenarios)

OEM-01: Factory Group Material ID Unification
- Question: Does same material have different IDs across factories in same OEM group?
- Value: OEM group reduces duplicated material setup.

OEM-02: OEM Group Purchasing Basis
- Question: Can OEM group calculate purchase volume for same material across factories?
- Value: Unified material identity gives OEM a real group purchasing basis.

OEM-03: Dead Stock Reduction
- Question: Can Factory A slow-moving stock be recognized as usable by Factory B?
- Value: Material identity turns dead stock into group-level reuse opportunity.

---

## Boss View ??6 Report Specs

Report 1: Group Executive Overview
- Total revenue by subsidiary
- Total revenue by customer / brand group
- Top products by revenue
- Gross margin by subsidiary
- Certification coverage
- Price validity risk
Format: BI dashboard + Excel summary

Report 2: Subsidiary Product Map
- Which subsidiary sells which SPU / SKU
- Product overlap across subsidiaries
- Product gaps
Format: Matrix table, BI heatmap

Report 3: Customer Product Sales Detail
- Which customers buy which products
- Customer concentration risk
- Cross-sell opportunities
Format: Customer x SPU matrix, filterable BI view

Report 4: Brand Certification / Approval Dashboard
- Products approved for which brands
- Pending or expired approvals
- Immediate sales opportunities
Format: Certification status table, expiry risk chart

Report 5: Customer-Specific Price History
- Same SPU sold to different customers at different prices
- Price changes over time
- Margin risk / quote validity risk
Format: Price history table, price variance chart

Report 6: SmartPN Atlas Data Readiness Score
- Which subsidiaries have complete data
- Which fields are missing
- What each team must clean next
Format: Readiness score by subsidiary, missing-field list, action owner table

---

## Permission Rules (Non-Negotiable)

- Brand may compare OEM and supplier-side prices for sourcing decisions
- Supplier should NOT see brand cross-OEM comparison or negotiation strategy
- OEM should NOT see another OEM brand-private notes or pricing
- Supplier sees own product, customer, price, certification, readiness records only
- Brand-private pricing, future purchasing plan, group negotiation analysis = brand-side private only

---

## Pending Alignment

These 23 scenarios need to be mapped against the 17 Scenario system (MASTER_CONTENT file).
Some may overlap. Jim to confirm which are the same and which are different.

Priority for short-term revenue: BOS-01 to BOS-06 (Supplier Boss View)
