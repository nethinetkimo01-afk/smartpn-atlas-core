# SmartPN Atlas Demo Software ??Menu Structure
Version: v1.0 | 2026-06-02
Status: Confirmed / Recovered. Not final UI spec. Jim must confirm before implementation.

---

## Entry Point

SmartPN Atlas Demo Software
- Brand / OEM Flow
- Supplier Flow
- SmartPN Creation
- Governance / Permission
- Factory / BOM Reference Boundary

---

## 1. Brand / OEM Flow

Brand / OEM Flow
- Material Search
  - Keyword Search
  - Material Search Results
  - Same-material / Equivalent-material Result Window
- Material Detail
  - Supplier-maintained Source-side Data
  - Permission-limited Fields
  - Comment / Review
  - Add to My Library / Brand Library
  - Compare
- Add to My Library / Brand Library
- Compare
  - Compare Same / Equivalent Materials
  - Compare Supplier-maintained Data
  - Compare Permission-visible Fields

UI Principle: Amazon / eBay / hotel booking style. Not ERP dense table.
Operating flow: Search ??Result ??Detail ??Add to Library ??Compare

---

## 2. Supplier Flow

Supplier Flow
- Company Info
  - Company Establishment / Company Profile
- Create / Maintain SmartPN
  - SmartPN Creation
- Permission Management
  - Release / Permission Decision
  - Access Control
  - Customer / Role / Field Visibility

Operating flow: Company info ??Create SmartPN ??Permission management

---

## 3. SmartPN Creation

SmartPN Creation
- Company Establishment
  - Supplier-side Company Establishment
  - Head Office / Subsidiary Mapping
  - Head Office Unified Management
- SmartPN Material Creation
  - Raw Material Creation
  - Secondary Processing Creation

---

## 4. Raw Material Creation Fields (Recovered Direction Only)

Raw Material Creation
- SmartPN ID
- Supplier Code
- Name
- Category
- Composition
- Color / Pantone
- Specs
- Status
- Created By
- Updated By

NOTE: These are recovered field directions, not final UI spec. Do not expand fields without Jim confirmation.

---

## 5. Secondary Processing Creation

Secondary Processing Creation
- Input Material Section
  - Material SmartPN
  - Processing Method
  - Material Unit
  - Material Ratio
- Output Material Section
  - Processed Output Material Name
  - Output Unit
  - Output Quantity
  - New Output SmartPN
- Secondary Processing Decision Rule
  - InputCount >= 2 = secondary processing
  - InputCount = 1 AND StructureChanged = TRUE = secondary processing

NOT secondary processing (unless structure changes):
- Single-material dyeing
- Single-material printing
- Embroidery
- General surface treatment

Example (confirmed): 44 inch ??2 x 22 inch
- Output quantity: always 1
- Material ratio: 0.5 for one 22 inch output
- Output SmartPN: different from original SmartPN

---

## 6. Governance / Boundary

Governance / Boundary
- Source Ownership
- Permission Governance
- Field Mapping
- Material Relationship
- Trusted Data Exchange
- BOM / ERP / PLM Reference Boundary

Factory / BOM Reference Boundary:
- SmartPN provides material identity reference only
- Brand / Factory keeps BOM in own ERP / PLM / PDM
- Factory demand uses secondary processing SmartPN order quantity
- Factory splits into: Purchase Order + Processing Order
- Raw material quantity calculated by ratio

---

## 7. Comment / Review

Location: Under Material Detail
- Brand / Company-private Material Comment
- Internal Use Experience
- Development / Sourcing Note
- Decision Memory

---

## Rejected ??Do NOT Use as Demo Menu

- 17 Scenario menu
- Original 10 flat menu
- Generic SaaS function overview
- LinkedIn / website / video topics
- Smoke-test proof modules as product navigation

---

## Candidate Supplier Sidebar (NOT CONFIRMED ??Do not implement)

Recovered candidate only. Jim must confirm before use:
Dashboard / Requests / Company Management / SmartPN / SmartPN x Subsidiary / Access Control / Quotation / Reports / Settings

---

## Complete Menu Tree

SmartPN Atlas Demo Software
- Brand / OEM Flow
  - Material Search
    - Keyword Search
    - Material Search Results
    - Same-material / Equivalent-material Result Window
  - Material Detail
    - Supplier-maintained Source-side Data
    - Permission-limited Fields
    - Comment / Review
    - Add to My Library / Brand Library
    - Compare
  - Add to My Library / Brand Library
  - Compare
- Supplier Flow
  - Company Info
    - Company Establishment
  - Create / Maintain SmartPN
    - SmartPN Creation
      - Company Establishment
      - SmartPN Material Creation
        - Raw Material Creation
        - Secondary Processing Creation
  - Permission Management
    - Release / Permission Decision
    - Access Control
    - Customer / Role / Field Visibility
- Governance / Boundary
  - Source Ownership
  - Permission Governance
  - Field Mapping
  - Material Relationship
  - Trusted Data Exchange
  - BOM / ERP / PLM Reference Boundary