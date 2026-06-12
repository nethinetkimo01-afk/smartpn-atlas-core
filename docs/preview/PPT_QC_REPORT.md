# PPT & Demo QC Report — S01–S17
QC Date: 2026-06-12 | Spec Reference: `00_HANDOFF/16_S02_TO_S17_COMPLETE_SPECS.md`

---

## Summary

| File Set | Total | PASS | DIFF |
|----------|-------|------|------|
| PPT (S01–S17) | 17 | 17 | 0 |
| DEMO (S01–S17) | 17 | 16 | 1 |

One diff found and fixed: S01 DEMO was missing its scenario-tag.

---

## PPT Files

| # | File | Title | Spec Match | Status |
|---|------|-------|------------|--------|
| S01 | S01_PPT.html | S01 — Complete, Timely, and Private Material Library | ✓ | **PASS** |
| S02 | S02_PPT.html | S02 — Real-time Material Info = Accurate Demand Forecast | ✓ | **PASS** |
| S03 | S03_PPT.html | S03 — Shared Language Across Product Lines | ✓ | **PASS** |
| S04 | S04_PPT.html | S04 — Shared Language Across Brands & Product Lines | ✓ | **PASS** |
| S05 | S05_PPT.html | S05 — Factory Gets Correct Material Count | ✓ | **PASS** |
| S06 | S06_PPT.html | S06 — Forecast Accuracy Stays at 100% | ✓ | **PASS** |
| S07 | S07_PPT.html | S07 — 0 Communication Gap | ✓ | **PASS** |
| S08 | S08_PPT.html | S08 — Supplier Group Owner Sees Sales and Collection Analysis | ✓ | **PASS** |
| S09 | S09_PPT.html | S09 — Supplier Controls Publishing | ✓ | **PASS** |
| S10 | S10_PPT.html | S10 — Brand Finds Identical and Alternative Materials Faster | ✓ | **PASS** |
| S11 | S11_PPT.html | S11 — Factory Reduces Excess Material | ✓ | **PASS** |
| S12 | S12_PPT.html | S12 — Same Product Same QR Code — Different DPP Composition | ✓ | **PASS** |
| S13 | S13_PPT.html | S13 — Supplier Exchanges Required Data Without Understanding Every Regulation | ✓ | **PASS** |
| S14 | S14_PPT.html | S14 — Supplier-to-Factory Authorization | ✓ | **PASS** |
| S15 | S15_PPT.html | S15 — Supplier Shortens New Material Launch Time | ✓ | **PASS** |
| S16 | S16_PPT.html | S16 — Brand Obtains New Material Information Faster | ✓ | **PASS** |
| S17 | S17_PPT.html | S17 — Brand Creates Development and Purchasing Reference from Supplier Comments | ✓ | **PASS** |

---

## DEMO Files

| # | File | Key Interactive Elements | Spec Data | Scenario Tag | Status |
|---|------|--------------------------|-----------|--------------|--------|
| S01 | S01_DEMO.html | Role toggle (Brand/External), PRIVATE→OPEN permission view, material table | ✓ | DIFF → **FIXED** | **PASS** |
| S02 | S02_DEMO.html | Current/After toggle, demand forecast delta data (120k→95k / 320k→361k) | ✓ | ✓ | **PASS** |
| S03 | S03_DEMO.html | Role-based material code/name display (brand vs supplier language) | ✓ | ✓ | **PASS** |
| S04 | S04_DEMO.html | Multi-brand filter view, shared language across brands | ✓ | ✓ | **PASS** |
| S05 | S05_DEMO.html | Factory A/B selector, BOM qty / actual order delta | ✓ | ✓ | **PASS** |
| S06 | S06_DEMO.html | Before/After toggle, SPA-GRP-0001 plan 120k→180k, safety stock calc | ✓ | ✓ | **PASS** |
| S07 | S07_DEMO.html | Before/After communication flow, 0 gap messaging demo | ✓ | ✓ | **PASS** |
| S08 | S08_DEMO.html | 3 tabs: Sales Analysis / Collection Analysis / Unit Price Maintenance | ✓ (Subsidiary/Country/Product Group/Customer columns, Net60/Net45 AR data) | ✓ | **PASS** |
| S09 | S09_DEMO.html | Supplier publish control, PRIVATE→SHARED→OPEN toggle | ✓ | ✓ | **PASS** |
| S10 | S10_DEMO.html | Find Same Material: Identical (SPN-004) + Alternative (SPN-005) results | ✓ | ✓ | **PASS** |
| S11 | S11_DEMO.html | Factory excess material view, role switch | ✓ | ✓ | **PASS** |
| S12 | S12_DEMO.html | Batch A/B selector, QR code, DPP composition comparison | ✓ | ✓ | **PASS** |
| S13 | S13_DEMO.html | Compliance field guided fill, Missing→Ready status transitions | ✓ | ✓ | **PASS** |
| S14 | S14_DEMO.html | Supplier/Partner-01 role switch, authorize button, permission level | ✓ | ✓ | **PASS** |
| S15 | S15_DEMO.html | Supplier launch workflow steps, timeline view | ✓ | ✓ | **PASS** |
| S16 | S16_DEMO.html | Brand-01/Other company role switch, new material info access timeline | ✓ | ✓ | **PASS** |
| S17 | S17_DEMO.html | Star rating system, comment form, role switch, ratings history | ✓ | ✓ | **PASS** |

---

## Diff Detail

### S01_DEMO — Missing scenario-tag (FIXED)

**Before:** Topbar contained only `<span class="brand">` + search box + role toggle. No scenario label.

**After:** Added `.scenario-tag` CSS + `<span class="scenario-tag">S01 — Complete, Timely, and Private Material Library</span>` to topbar, consistent with S02–S17 pattern.

---

## Spec Boundary Verification

### S08 — "No gross margin / no brand-level comparison" (CONFIRMED CORRECT)
Demo correctly omits: brand-level sales comparison, gross margin, cost analysis.
Demo correctly includes: product group + subsidiary/country KPIs only (spec boundary satisfied).

### S10 — FSM (Find Same Material)
Demo shows Identical = exact SPU+SKU match (SPN-004), Alternative = same category different SKU. Matches spec definition.

### S14 — GRANT layer
Supplier-to-Factory authorization demo shows field-level control (公司+單位+姓名 hierarchy implied). Spec boundary satisfied.

---

*Generated by Claude Code on 2026-06-12*
