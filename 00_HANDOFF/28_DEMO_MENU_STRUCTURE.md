# SmartPN Atlas Demo — Menu Structure

Version: v1.0 | 2026-06-08
Source: Recovered from local HTML files in D:\SmartPN_Atlas_Workspace\
Status: CONFIRMED EXISTS. Two demo versions with different scope.

---

## Version A: Phase 1 Demo SaaS（完整版）

File: `D:\SmartPN_Atlas_Workspace\03_Outputs\05_Scenario_System\smartpn_atlas_phase1_demo_saas\index.html`
Also at: `D:\SmartPN_Atlas_Workspace\docs\preview\demo_v2_1\index.html`

Sidebar Menu (17 items):

| # | Menu Item | View ID |
|---|-----------|---------|
| 1 | Dashboard | dashboard |
| 2 | Material Search | search |
| 3 | Material Detail | detail |
| 4 | Supplier Profile | supplier |
| 5 | Supplier Maintenance | maintain |
| 6 | SPU / SKU | spu |
| 7 | Secondary Processing | secondary |
| 8 | Permission Control | permission |
| 9 | Field Mapping | mapping |
| 10 | My Library | library |
| 11 | Compare | compare |
| 12 | Find Same Material | same |
| 13 | BOM Reference | bom |
| 14 | Chat / Request | request |
| 15 | Change Log | change |
| 16 | Governance | governance |
| 17 | Private Notes / Price | private |
| 18 | Scenario Coverage | scenario |

---

## Version B: Formal Demo B（GTS 精簡版）

File: `D:\SmartPN_Atlas_Workspace\docs\preview\smartpn_formal_demo_b\index.html`
Scope: Confirmed SmartPN 建立 + recovered candidate flows. Internal only.

Sidebar Menu (7 items):

| # | Menu Item | Sub-label | Page ID |
|---|-----------|-----------|---------|
| 1 | SmartPN 建立 | 公司建立 | company |
| 2 | SmartPN 物料建立 | 原物料建立 | material |
| 3 | SmartPN 物料建立 | 二次加工建立 | secondary |
| 4 | Material Search | Detail + Find Same Material | search |
| 5 | Requests | Brand / OEM request flow | request |
| 6 | Access Control | Multi-layer permission | permission |
| 7 | Shared BOM Flow | Factory substitution / DPP | sharedbom |

Status bar (4 badges):
- Identity: Supplier-maintained
- Boundary: No BOM storage
- Permission: Shared ≠ fully open
- Scenario base: Demo first, scenario later

---

## Version Comparison

| Dimension | Phase 1 Demo SaaS | Formal Demo B |
|-----------|-------------------|---------------|
| Audience | Internal / investor | GTS / key partner |
| Menu items | 18 | 7 |
| Scope | Full platform | Scoped to confirmed flows |
| Language | English | Mixed EN/ZH |
| Status bar | None | 4 boundary badges |
| Find Same Material | Standalone menu item | Embedded in Material Detail modal |

---

## Source Files (all confirmed present)

```
D:\SmartPN_Atlas_Workspace\
├── 03_Outputs\05_Scenario_System\
│   ├── smartpn_atlas_phase1_demo_saas\index.html   ← Phase 1 complete
│   ├── smartpn_atlas_demo_v2_1\index.html
│   ├── smartpn_atlas_demo_v2\index.html
│   └── smartpn_atlas_demo_v1\index.html
├── 01_Project_Core\05_Prototype\
│   ├── smartpn-atlas-demo-v0\index.html
│   ├── smartpn-atlas-demo-v0\gts-guided-demo.html
│   └── smartpn-atlas-demo-v0\gts-dpp-output-demo.html
└── docs\preview\
    ├── smartpn_formal_demo_b\index.html            ← Formal Demo B (GTS)
    ├── demo_v2_1\index.html
    └── demo_v2\index.html
```

---

## Navigation Flow (CONFIRMED by Jim 2026-06-10)

```
Material card (with image)
  → Material Detail (SPU + SKU page)
      → click Supplier name → Company Profile page
      → click "Find Same Material"
          → carries current SPU + SKU conditions into search
          → Identical:   same SPU + same SKU  (S10 logic)
          → Alternative: same SPU + different SKU
          → customer can modify conditions and re-search
```

Key concepts:
- Each material card displays a product image placeholder (Apple-style: centered image, #F5F5F7 rounded background)
- Detail page is split into SPU block (material identity) + SKU block (variant selector, Apple picker style)
- Supplier name on detail page is a clickable link → Company Profile
- Find Same Material button passes spuCode + skuKey as filter conditions into search
- Search results under FSM mode show two labeled sections: Identical / Alternative
- Filter conditions are editable (user can clear or modify before re-searching)

---

## Permission Design (CONFIRMED by Jim 2026-06-10)

### 1. Product permission: SPU-level authorization

- Permission is set at SPU level (authorization atom, per `02_GOVERNANCE.json`)
- SKU inherits permission from its parent SPU
- Permission levels: OPEN / SHARED / PRIVATE

### 2. Custom Field Groups (NEW — GRANT layer in action)

Supplier can create named field groups, then grant groups to specific accounts:

| Step | Action |
|------|--------|
| 1 | Supplier creates a named group, e.g. `關務欄位` (Customs fields) |
| 2 | Supplier checks (✓) which fields belong to this group (e.g. composition, HS code, country of origin) |
| 3 | Supplier grants the group by name to a specific account |
| Result | That account can view exactly those fields — nothing else |

Example:
- Group `Customs` → fields: composition, HS code, origin → shared with Account X
- Group `Finance` → fields: price, MOQ, lead time → shared with Account Y
- Group `Technical` → fields: tensile strength, density, standard → shared with Account Z

### 3. GRANT layer connection

> This is the GRANT layer in action: the data owner defines what to group, and grants groups to the right people.

- Data owner = Supplier (not platform, not brand)
- Authorization atom = Field Group, within SPU permission boundary
- Access is not taken. It is granted.

---

## Next Steps

- [ ] Confirm which version is the current official demo for GTS presentation
- [ ] S01 Demo software: confirm it uses Formal Demo B layout or Phase 1 layout
- [ ] S02–S17: each scenario maps to which menu items in Phase 1 version
