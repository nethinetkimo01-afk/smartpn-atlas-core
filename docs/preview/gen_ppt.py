#!/usr/bin/env python3
"""Generate S01-S17 PPT HTML slides for SmartPN Atlas."""
import os, textwrap

OUT = os.path.dirname(os.path.abspath(__file__))

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;background:#fff;color:#1A1A1A;display:flex;flex-direction:column;min-height:100vh;font-size:13px}
a{color:#54463A;text-decoration:none}

.slide-header{padding:36px 56px 0}
.title-row{display:flex;align-items:center;gap:14px;margin-bottom:6px}
.title-bar{width:3px;height:28px;background:#54463A;border-radius:2px;flex-shrink:0}
.slide-title{font-size:22px;font-weight:600;color:#1A1A1A;letter-spacing:-.5px;line-height:1.25}
.slide-formal{font-size:12px;color:#AAA;margin-bottom:28px;padding-left:17px;font-style:italic;line-height:1.5}

.split{display:flex;gap:0;padding:0 56px;flex:1}
.pane{flex:1;padding-right:24px}
.pane+.pane{padding-right:0;padding-left:24px;border-left:.5px solid #E5E5E5}

.pane-hdr{padding:8px 14px;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;border-radius:6px;margin-bottom:14px}
.pane-hdr.cur{background:#B71C1C;color:#fff}
.pane-hdr.aft{background:#1B5E20;color:#fff}
.pane-hdr.aft u{text-decoration:underline}

.tw{border:.5px solid #E5E5E5;border-radius:10px;overflow:hidden;margin-bottom:14px;font-size:11px}
table{width:100%;border-collapse:collapse}
thead th{background:#FAFAF8;padding:7px 12px;text-align:left;font-size:9px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:.04em;border-bottom:.5px solid #E5E5E5;white-space:nowrap}
tbody td{padding:9px 12px;border-bottom:.5px solid #F0F0F0;color:#1A1A1A;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
.red{color:#B71C1C;font-weight:600}
.grn{color:#1B5E20;font-weight:600}
.mut{color:#999}
.hl{background:#FFF8E6}
.fa-row{background:#FFFDE7}
.fb-row{background:#F3F8FF}
.ctr{text-align:center}

.badge{display:inline-block;font-size:9px;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap}
.b-priv{background:#F5F5F5;color:#888;border:.5px solid #E0E0E0}
.b-open{background:#EAF3DE;color:#2E7D32}
.b-shared{background:#F0F6FF;color:#1A5FB4}
.b-new{background:#FFEBE6;color:#B52A00}
.b-ok{background:#EAF3DE;color:#1B5E20}
.b-warn{background:#FFF3E0;color:#8B5000}

.note{font-size:10px;color:#888;padding:0 0 10px;font-style:italic}

.script-area{margin:20px 56px 0;padding:14px 18px;background:#FAFAF8;border-left:2.5px solid #54463A;border-radius:0 8px 8px 0;font-size:11px;color:#555;line-height:1.75}
.script-lbl{font-size:9px;font-weight:700;color:#54463A;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}

.scenario-tag{text-align:right;padding:14px 56px 22px;font-size:8px;color:#CCC;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin-top:auto}
"""

def page(num, title, formal, pane_left_hdr, pane_right_hdr, left_html, right_html, script):
    sn = f"S{num:02d}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{sn} — {title} · SmartPN Atlas</title>
<style>{CSS}</style>
</head>
<body>

<div class="slide-header">
  <div class="title-row">
    <div class="title-bar"></div>
    <div class="slide-title">{sn} — {title}</div>
  </div>
  <div class="slide-formal">{formal}</div>
</div>

<div class="split">
  <div class="pane">
    <div class="pane-hdr cur">{pane_left_hdr}</div>
    {left_html}
  </div>
  <div class="pane">
    <div class="pane-hdr aft">{pane_right_hdr}</div>
    {right_html}
  </div>
</div>

<div class="script-area">
  <div class="script-lbl">Jim's presentation script</div>
  {script}
</div>

<div class="scenario-tag">SCENARIO {num:02d} / SMARTPN ATLAS</div>
</body>
</html>"""

def tbl(headers, rows, row_classes=None):
    ths = ''.join(f'<th>{h}</th>' for h in headers)
    trs = ''
    for i, r in enumerate(rows):
        cls = ''
        if row_classes and i < len(row_classes):
            cls = f' class="{row_classes[i]}"'
        tds = ''.join(f'<td>{c}</td>' for c in r)
        trs += f'<tr{cls}>{tds}</tr>'
    return f'<div class="tw"><table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'

# ── S01 ────────────────────────────────────────────────────────────────────────
S01 = page(1,
  "Complete, Timely, and Private Material Library",
  "Brand obtains a larger, more current, more accurate, more complete, and permission-controlled material library.",
  "CURRENT — Internal Maintenance",
  "AFTER SMARTPN ATLAS — <u>Shared Library</u>",
  tbl(
    ['Supplier','#','Updated','Maintained By','Code','Name','Permission'],
    [['A','1','Past','Internal','Independent','Independent','<span class="badge b-priv">PRIVATE</span>'],
     ['A','2','Past','Internal','Independent','Independent','<span class="badge b-priv">PRIVATE</span>']],
  ),
  tbl(
    ['Supplier','#','Updated','Maintained By','Code','Name','Permission'],
    [['A','1','Past','Supplier','Shared Language','Shared Language','<span class="badge b-priv">PRIVATE</span>'],
     ['A','2','Past','Supplier','Shared Language','Shared Language','<span class="badge b-priv">PRIVATE</span>'],
     ['A','<span class="grn">3</span>','<span class="grn">Today</span>','<span class="grn">Supplier</span>','<span class="grn">Shared Language</span>','<span class="grn">Shared Language</span>','<span class="badge b-priv">PRIVATE</span>'],
     ['A','<span class="grn">4</span>','<span class="grn">Today</span>','<span class="grn">Supplier</span>','<span class="grn">Shared Language</span>','<span class="grn">Shared Language</span>','<span class="badge b-open">OPEN</span>']],
    ['','','','hl','hl']
  ),
  """After SmartPN Atlas, your material library is larger, more current, more accurate, and permission-controlled.
  <br><br>You had 2 items. Now you see 4. Items 3 and 4 are new — added Today.
  Before, your team collected data offline. Now Supplier maintains their own data.
  This reduces internal work and improves accuracy. Supplier is responsible for their own data quality.
  <br><br>Code and Name are now Shared Language across Brand, Factory, and Supplier.
  Everyone wants to protect their library. You can see all 4 items — but others see only 1, because only 1 is OPEN."""
)

# ── S02 ────────────────────────────────────────────────────────────────────────
S02 = page(2,
  "Shared Language and Shared BOM",
  "Same material — same code, same name — recognized across Brand, Factory, and Supplier.",
  "CURRENT — Independent Codes",
  "AFTER SMARTPN ATLAS — <u>Shared BOM</u>",
  tbl(
    ['Role','BOM Line','Code','Description','Source 1','Source 2'],
    [['Brand','Upper mesh panel','<span class="red">BR-COMP-7788</span>','Laminated black mesh','<span class="red">BR-MAT-7781</span>','<span class="red">BR-FILM-4420</span>'],
     ['Factory','Upper mesh panel','<span class="red">FAC-COMP-7008</span>','Laminated black mesh','<span class="red">FAC-M-2039</span>','<span class="red">FAC-FILM-445</span>'],
     ['Supplier','Upper mesh panel','<span class="red">SUP-COMP-610</span>','Laminated black mesh','<span class="red">SUP-A-991</span>','<span class="red">SUP-B-330</span>']],
  ),
  tbl(
    ['Role','BOM Line','Unified Code','Description','Source 1','Source 2'],
    [['Brand','Upper mesh panel','<span class="grn">SPA-COMP-0101</span>','Laminated black mesh','<span class="grn">SPA-MAT-0001</span>','<span class="grn">SPA-MAT-0002</span>'],
     ['Factory','Upper mesh panel','<span class="grn">SPA-COMP-0101</span>','Laminated black mesh','<span class="grn">SPA-MAT-0001</span>','<span class="grn">SPA-MAT-0002</span>'],
     ['Supplier','Upper mesh panel','<span class="grn">SPA-COMP-0101</span>','Laminated black mesh','<span class="grn">SPA-MAT-0001</span>','<span class="grn">SPA-MAT-0002</span>']],
  ),
  """You give BOM to your factory. But you cannot confirm they use the same material — because each party has a different code for the same thing.
  <br><br>Two factories means even more confusion. Three different codes, three different names, same material. Nobody can verify.
  <br><br>After SmartPN Atlas: one shared code, one shared name. Brand, Factory, Supplier — all using SPA-COMP-0101.
  Same code means same material. Supply chain is transparent. No more confirmation calls."""
)

# ── S03 ────────────────────────────────────────────────────────────────────────
S03 = page(3,
  "Shared Language Across Product Lines Under One Brand",
  "One brand, multiple product lines — one material identity across all.",
  "CURRENT — Independent Local IDs",
  "AFTER SMARTPN ATLAS — <u>One SmartPN ID</u>",
  tbl(
    ['Brand','Product Line','Local ID','Material'],
    [['Brand A','Footwear','<span class="red">SHOE-MAT-118</span>','Black recycled polyester mesh'],
     ['Brand A','Apparel','<span class="red">APP-MAT-552</span>','Black recycled polyester mesh'],
     ['Brand A','Bags','<span class="red">BAG-MAT-907</span>','Black recycled polyester mesh']],
  ),
  tbl(
    ['Brand','Product Line','Local ID','SmartPN Atlas ID','Material'],
    [['Brand A','Footwear','SHOE-MAT-118','<span class="grn">SPA-MAT-0001</span>','Black recycled polyester mesh'],
     ['Brand A','Apparel','APP-MAT-552','<span class="grn">SPA-MAT-0001</span>','Black recycled polyester mesh'],
     ['Brand A','Bags','BAG-MAT-907','<span class="grn">SPA-MAT-0001</span>','Black recycled polyester mesh']],
  ),
  """Same material. Three different local IDs — Footwear, Apparel, Bags each track it independently.
  <br><br>When you want to know total usage across product lines, you cannot aggregate — because the system doesn't know these are the same material.
  <br><br>After SmartPN Atlas: each product line keeps its local ID. But all three now link to SPA-MAT-0001.
  Aggregate volume, cross-division visibility, supplier negotiation leverage — all become possible."""
)

# ── S04 ────────────────────────────────────────────────────────────────────────
S04 = page(4,
  "Shared Language Across Brands Under One Group",
  "One group, multiple brands and product lines — same material visible at group level.",
  "CURRENT — Fragmented Group Data",
  "AFTER SMARTPN ATLAS — <u>Group-Level Visibility</u>",
  tbl(
    ['Group','Brand','Product Line','Local ID','Material'],
    [['Group A','Brand A','Footwear','<span class="red">A-SHOE-MAT-118</span>','Black RPET mesh'],
     ['Group A','Brand A','Apparel','<span class="red">A-APP-MAT-552</span>','Black RPET mesh'],
     ['Group A','Brand B','Footwear','<span class="red">B-SHOE-MAT-778</span>','Black RPET mesh'],
     ['Group A','Brand B','Bags','<span class="red">B-BAG-MAT-411</span>','Black RPET mesh']],
  ),
  tbl(
    ['Group','Brand','Product Line','Local ID','SmartPN ID','Material'],
    [['Group A','Brand A','Footwear','A-SHOE-MAT-118','<span class="grn">SPA-MAT-0001</span>','Black RPET mesh'],
     ['Group A','Brand A','Apparel','A-APP-MAT-552','<span class="grn">SPA-MAT-0001</span>','Black RPET mesh'],
     ['Group A','Brand B','Footwear','B-SHOE-MAT-778','<span class="grn">SPA-MAT-0001</span>','Black RPET mesh'],
     ['Group A','Brand B','Bags','B-BAG-MAT-411','<span class="grn">SPA-MAT-0001</span>','Black RPET mesh']],
  ),
  """At group level, same material appears under four different IDs across two brands and four product lines.
  Group procurement cannot aggregate. Supplier negotiation is fragmented. Volume leverage is lost.
  <br><br>After SmartPN Atlas: group procurement sees all four lines link to SPA-MAT-0001.
  Combined volume is visible. Negotiation power increases. Brand A and Brand B align on the same material reference."""
)

# ── S05 ────────────────────────────────────────────────────────────────────────
S05_center = """<div class="tw" style="margin-bottom:14px"><table>
<thead><tr><th colspan="5" style="background:#F5F0EC;color:#54463A;font-size:10px;text-align:center">BRAND SHARED BOM (issued to all factories)</th></tr>
<tr><th>BOM Line</th><th>Shared BOM ID</th><th>Source 1</th><th>Source 2</th></tr></thead>
<tbody><tr><td>Upper mesh panel</td><td>SPA-COMP-0101</td><td>SPA-MAT-0001</td><td>SPA-MAT-0002</td></tr></tbody>
</table></div>"""

S05 = page(5,
  "Shared BOM vs Actual BOM vs Actual DPP",
  "Brand issues one Shared BOM. Factories may substitute — SmartPN Atlas makes the difference visible.",
  "CURRENT — Factory Substitution Invisible",
  "AFTER SMARTPN ATLAS — <u>Substitution Transparent</u>",
  S05_center + tbl(
    ['Factory','BOM Line','Actual ID','Source 1','Source 2','Diff'],
    [['Factory A','Upper mesh panel','SPA-COMP-0101','SPA-MAT-0001','SPA-MAT-0002','<span class="badge b-ok">No diff</span>'],
     ['Factory B','Upper mesh panel','<span class="red">SPA-COMP-0101-B</span>','SPA-MAT-0001','<span class="red">SPA-MAT-0048</span>','<span class="badge b-warn">Source 2 changed</span>']],
  ),
  tbl(
    ['Factory','DPP Basis','Material Used','Credibility'],
    [['Factory A','Actual BOM','SPA-COMP-0101 + 0001 + 0002','<span class="badge b-ok">Matches Shared BOM</span>'],
     ['Factory B','Actual BOM','SPA-COMP-0101-B + 0001 + <span class="red">0048</span>','<span class="badge b-open">Brand-approved local sub</span>']],
  ),
  """Brand issues one Shared BOM. But you cannot confirm every factory uses exactly the same materials.
  Factory B substituted Source 2 — SPA-MAT-0002 replaced by SPA-MAT-0048. Was it brand-approved?
  <br><br>After SmartPN Atlas: the substitution is recorded. Factory B DPP uses SPA-MAT-0048 — the actual material used.
  DPP source data is based on actual factory BOM, not just shared BOM. More credible. More accurate."""
)

# ── S06 ────────────────────────────────────────────────────────────────────────
S06 = page(6,
  "Forecast Volume for Next-Season Negotiation",
  "Structured material identity and usage data — Brand calculates negotiation reference volume.",
  "CURRENT — Fragmented, Unstructured",
  "AFTER SMARTPN ATLAS — <u>Structured Reference</u>",
  tbl(
    ['Material Group','Local IDs','SS Qty','Source'],
    [['Black RPET mesh','<span class="red">BR-MAT-7781 / FAC-M-2039 / SUP-A-991</span>','120,000m','<span class="red">Supplier collected report</span>']],
  ),
  tbl(
    ['SmartPN Group','Mapped Local IDs','SS Qty','FW Forecast Ref','Calculation Source'],
    [['SPA-GRP-0001','BR-MAT-7781 / FAC-M-2039 / SUP-A-991','120,000m','<span class="grn">180,000m</span>','<span class="grn">Brand calc via SmartPN data</span>']],
  ),
  """You need to negotiate next season's material price. But your usage data is scattered — three different IDs for the same material, across brand, factory, supplier.
  <br><br>After SmartPN Atlas: all three IDs are mapped to SPA-GRP-0001. SS actual usage is 120,000m.
  Brand calculates FW forecast as 180,000m and uses this as negotiation reference.
  SmartPN Atlas does not create the forecast — it provides the structured data. Brand does the calculation."""
)

# ── S07 ────────────────────────────────────────────────────────────────────────
S07_left = tbl(
    ['Role','Local ID','Material','Result'],
    [['Brand design','BR-MAT-7781','Black recycled RPET mesh','Sends design reference'],
     ['Factory','FAC-M-2039','Black RPET mesh','<span class="red">Needs to confirm</span>'],
     ['Supplier','SUP-A-991','Recycled polyester mesh black','<span class="red">Needs to confirm</span>']],
) + '<p class="note">Scenario B: Factory A→B transfer also requires re-confirmation of equivalent material.</p>'

S07_right = tbl(
    ['Role','Local ID','SmartPN Atlas ID','Result'],
    [['Brand design','BR-MAT-7781','<span class="grn">SPA-MAT-0001</span>','<span class="grn">Same shared reference</span>'],
     ['Factory','FAC-M-2039','<span class="grn">SPA-MAT-0001</span>','<span class="grn">Same shared reference</span>'],
     ['Supplier','SUP-A-991','<span class="grn">SPA-MAT-0001</span>','<span class="grn">Same shared reference</span>']],
) + '<p class="note">Factory A→B transfer: both use SPA-COMP-0101 — zero re-confirmation needed.</p>'

S07 = page(7,
  "Zero Communication Gap",
  "Local IDs preserved. SmartPN Atlas ID removes identity ambiguity across all parties.",
  "CURRENT — Confirmation Required",
  "AFTER SMARTPN ATLAS — <u>0 Communication Gap</u>",
  S07_left,
  S07_right,
  """Brand sends BR-MAT-7781. Factory receives FAC-M-2039. Supplier records SUP-A-991. Three names, same material. Every handoff requires a confirmation call.
  When Factory A transfers a product to Factory B — Factory B must re-confirm every material. Time lost. Mistakes happen.
  <br><br>After SmartPN Atlas: all three local IDs map to SPA-MAT-0001. No confirmation needed. Factory A to Factory B — same SPA-COMP-0101.
  This does not mean people never communicate. It means material identity gap is eliminated."""
)

# ── S08 ────────────────────────────────────────────────────────────────────────
S08_left = '<p class="note" style="margin-bottom:10px">Sales data scattered across subsidiaries. No consolidated view. Collection status requires manual tracking across multiple systems.</p>'
S08_right = tbl(
    ['Subsidiary','Country','Product Group','Customer','Sales Vol','Sales Amt'],
    [['Supplier Vietnam Co.','Vietnam','RPET mesh group','Factory Group A','120,000m','240,000'],
     ['Supplier Indonesia Co.','Indonesia','RPET mesh group','Factory Group B','80,000m','168,000']],
) + tbl(
    ['Factory Company','Payment Terms','AR Amount','Expected Month','Expected Amt'],
    [['Factory A Vietnam Ltd.','Net 60','80,000','2026-06','80,000'],
     ['Factory B Indonesia Ltd.','Net 45','60,000','2026-05','60,000']],
)

S08 = page(8,
  "Supplier Group Owner Sees Sales and Collection Analysis",
  "Group-level dashboard — product group sales, customer share, expected collection by month.",
  "CURRENT — Fragmented Subsidiary Data",
  "AFTER SMARTPN ATLAS — <u>Consolidated Group View</u>",
  S08_left,
  S08_right,
  """As a supplier group owner, you want to know: which product group sells the most? Which customer is our biggest buyer?
  When do we expect to collect payment?
  <br><br>After SmartPN Atlas: consolidated view across all subsidiaries. Sales by product group. Customer share by company and country.
  Expected collection amount by month. All in one dashboard.
  Unit price maintenance per factory company — visible and controlled."""
)

# ── S09 ────────────────────────────────────────────────────────────────────────
S09_left = tbl(
    ['Step','Status','Who'],
    [['1','Draft','Supplier editor'],
     ['2','Saved draft','Supplier editor'],
     ['3','Pending review','Supplier editor → submit'],
     ['4','Approved','Supplier reviewer'],
     ['5','Published','Supplier publisher']],
) + '<p class="note">Without workflow: material data published immediately, no quality control.</p>'

S09_right = tbl(
    ['Step','Status','Action','Who'],
    [['1','<span class="badge b-warn">Draft</span>','Edit','editor-01'],
     ['2','<span class="badge b-warn">Saved draft</span>','Save','editor-01'],
     ['3','<span class="badge b-warn">Pending review</span>','Submit','editor-01'],
     ['4','<span class="badge b-ok">Approved</span>','Approve','reviewer-01'],
     ['5','<span class="badge b-open">Published</span>','Publish','publisher-01']],
) + '<p class="note">Brand user: sees published data. Non-brand user: sees only supplier-opened published data.</p>'

S09 = page(9,
  "Supplier Controls When to Publish and Who Can See",
  "Supplier decides publication timing and audience — through a structured review workflow.",
  "CURRENT — No Controlled Workflow",
  "AFTER SMARTPN ATLAS — <u>Supplier-Controlled Publication</u>",
  S09_left,
  S09_right,
  """Supplier wants to control when material data is published, and who can see it.
  Without a workflow, publication is immediate and uncontrolled.
  <br><br>After SmartPN Atlas: editor-01 creates and saves draft. Submits for review.
  reviewer-01 approves. publisher-01 publishes. Supplier sets who can see it.
  Brand sees it after publication. Non-brand user sees only what supplier opens. Full control."""
)

# ── S10 ────────────────────────────────────────────────────────────────────────
S10_left = tbl(
    ['Selected Material','SPU','SKU','Supplier','Lead Time'],
    [['unified name 01','spu-01','sku-01','supplier-01','30 days']],
) + '<p class="note">No system to find identical or alternative materials. Manual market search required.</p>'

S10_right = tbl(
    ['Type','Supplier','SPU','SKU','Name','Lead Time'],
    [['<span class="badge b-ok">Identical</span>','supplier-02','spu-01','sku-01','unified name 01','<span class="grn">20 days</span>'],
     ['<span class="badge b-shared">Alternative</span>','supplier-03','spu-01','sku-02','alternative name 01','<span class="grn">15 days</span>']],
)

S10 = page(10,
  "Brand Finds Identical and Alternative Materials Faster",
  "Identical = same SPU + SKU. Alternative = same SPU + different SKU.",
  "CURRENT — Manual Search Only",
  "AFTER SMARTPN ATLAS — <u>Instant Identical and Alternative Search</u>",
  S10_left,
  S10_right,
  """You are using unified name 01 from supplier-01. Lead time is 30 days. You want to know: is there a faster option?
  <br><br>After SmartPN Atlas: click Search Identical — supplier-02 offers the same spu-01 + sku-01 in 20 days.
  Click Search Alternative — supplier-03 offers spu-01 + sku-02 in 15 days.
  Identical or alternative — both are immediately visible. No manual market search."""
)

# ── S11 ────────────────────────────────────────────────────────────────────────
S11_left = tbl(
    ['Factory','Material ID','Name','Excess Qty','Status'],
    [['factory-01','factory-code','unified name 01','1','<span class="badge b-warn">Excess</span>']],
) + '<p class="note">Excess material has no handling path. Cannot sell, transfer, or recover value.</p>'

S11_right = tbl(
    ['Factory','Material ID','Name','Qty','Option 1','Option 2','Option 3'],
    [['factory-01','unified-01','unified name 01','1','Sell back: supplier-01','Transfer: factory-02','Sell to: factory-03']],
) + '<p class="note">Permission-controlled: factory group owner sees all excess. factory-02 and supplier-01 see only what they are authorized to see.</p>'

S11 = page(11,
  "Factory Reduces Excess Material by Finding Reuse and Resale Options",
  "Excess material mapped to SmartPN ID — handling options immediately visible.",
  "CURRENT — No Handling Path",
  "AFTER SMARTPN ATLAS — <u>Three Handling Options</u>",
  S11_left,
  S11_right,
  """Factory has excess material. Old system: no handling path. Material sits, value lost.
  <br><br>After SmartPN Atlas: factory-code maps to unified-01. SmartPN Atlas shows three options:
  Sell back to supplier-01. Transfer to factory-02. Sell to factory-03.
  Factory group owner sees all excess across group factories. factory-02 sees transfer option only if authorized. supplier-01 sees sell-back only if authorized."""
)

# ── S12 ────────────────────────────────────────────────────────────────────────
S12_left = '<p class="note" style="margin-bottom:10px">Product product-01, QR code qr-01. Same product, same QR code — but different raw material suppliers in different production batches. DPP cannot differentiate.</p>'
S12_right = tbl(
    ['Case','Product','QR','Supplier','Composition'],
    [['Batch A','product-01','qr-01','supplier-01','<span class="grn">60% recycled polyester / 40% TPU</span>'],
     ['Batch B','product-01','qr-01','supplier-02','<span class="red">55% recycled polyester / 45% TPU</span>']],
) + '<p class="note">Same product, same QR — different composition. SmartPN Atlas shows actual source data per batch.</p>'

S12 = page(12,
  "Same Product Same QR Code — Different DPP Composition",
  "Actual composition depends on raw material supplier per production batch — not just product design.",
  "CURRENT — One Composition for All Batches",
  "AFTER SMARTPN ATLAS — <u>Batch-Level Actual Composition</u>",
  S12_left,
  S12_right,
  """Same product. Same QR code. But Batch A uses supplier-01 — 60% recycled polyester / 40% TPU.
  Batch B uses supplier-02 — 55% recycled polyester / 45% TPU. Different composition.
  <br><br>If DPP shows only one composition for all batches — it is not accurate. Regulators will ask: which batch? Which supplier?
  After SmartPN Atlas: select Batch A — see supplier-01 data. Select Batch B — see supplier-02 data.
  DPP composition is based on actual source data, not a single fixed value."""
)

# ── S13 ────────────────────────────────────────────────────────────────────────
S13_left = tbl(
    ['Field','Status','Source'],
    [['product-code','<span class="badge b-ok">Mapped</span>','Supplier system'],
     ['material-code','<span class="badge b-ok">Mapped</span>','Supplier system'],
     ['composition','<span class="badge b-warn">Missing</span>','—'],
     ['recycled content','<span class="badge b-warn">Missing</span>','—'],
     ['evidence-file','<span class="badge b-warn">Missing</span>','—']],
)

S13_right = tbl(
    ['Field','Status','Source'],
    [['product-code','<span class="badge b-ok">Mapped</span>','Supplier system'],
     ['material-code','<span class="badge b-ok">Mapped</span>','Supplier system'],
     ['composition','<span class="badge b-open">Ready</span>','SmartPN Atlas (guided)'],
     ['recycled content','<span class="badge b-open">Ready</span>','SmartPN Atlas (guided)'],
     ['evidence-file','<span class="badge b-open">Ready</span>','SmartPN Atlas (guided)']],
) + '<p class="note">Exchange readiness changes from Missing to Ready after guided field completion.</p>'

S13 = page(13,
  "Supplier Exchanges Required Data Without Understanding Every Regulation",
  "Supplier follows SmartPN Atlas field guidance — not the full regulation text.",
  "CURRENT — Supplier Must Read Every Regulation",
  "AFTER SMARTPN ATLAS — <u>Guided Field Completion</u>",
  S13_left,
  S13_right,
  """Regulations require product-code, material-code, composition, recycled content, evidence-file.
  Supplier system can map the first two. The rest are missing. Supplier does not know which regulation requires what.
  <br><br>After SmartPN Atlas: SmartPN provides the field guidance. Supplier follows the guided form — not the regulation text.
  Missing fields are completed in SmartPN Atlas. Exchange readiness changes from Missing to Ready.
  Supplier does not need to understand every regulation. They follow the structure."""
)

# ── S14 ────────────────────────────────────────────────────────────────────────
S14_left = tbl(
    ['Area','SmartPN Atlas Role','Supplier Control'],
    [['Field structure','Provides structure','Decides when to complete'],
     ['Mapping','Supports mapping','Owns source data'],
     ['Missing fields','Provides guided fields','Decides whether to maintain'],
     ['Readiness','Shows status','Confirms completion'],
     ['Authorization','Provides permission tools','Decides what to share']],
)

S14_right = tbl(
    ['Field','Source','Status','Authorized To'],
    [['product-code','Mapped','<span class="badge b-open">Ready</span>','partner-01'],
     ['material-code','Mapped','<span class="badge b-open">Ready</span>','partner-01'],
     ['composition','SmartPN Atlas','<span class="badge b-open">Ready</span>','partner-01'],
     ['evidence-file','SmartPN Atlas','<span class="badge b-open">Ready</span>','<span class="red">Not authorized yet</span>']],
)

S14 = page(14,
  "Supplier Prepares Exchange-Ready Data While Controlling Authorization",
  "SmartPN Atlas provides structure and tools. Supplier decides what to share and with whom.",
  "CURRENT — No Structured Authorization Path",
  "AFTER SMARTPN ATLAS — <u>Supplier-Controlled Exchange</u>",
  S14_left,
  S14_right,
  """SmartPN Atlas provides the structure — field guidance, mapping tools, readiness view, permission controls.
  Supplier controls the data — what to maintain, when to complete, who to authorize.
  <br><br>After SmartPN Atlas: product-code, material-code, composition — all ready and authorized to partner-01.
  Evidence-file is ready but NOT yet authorized. Partner-01 sees only the three authorized fields.
  Supplier decides. SmartPN Atlas provides the tools."""
)

# ── S15 ────────────────────────────────────────────────────────────────────────
S15_left = '<p class="note" style="margin-bottom:10px">New material creation involves offline communication, email confirmation, manual record keeping. Time to market: weeks.</p><div class="tw"><table><thead><tr><th>Step</th><th>Time</th><th>Method</th></tr></thead><tbody><tr><td>Supplier creates material</td><td>Day 1</td><td class="red">Email / offline</td></tr><tr><td>Internal review</td><td>Day 5</td><td class="red">Manual approval</td></tr><tr><td>Brand notified</td><td>Day 10+</td><td class="red">Email</td></tr><tr><td>Brand can use</td><td>Week 3+</td><td class="red">After confirmation</td></tr></tbody></table></div>'

S15_right = tbl(
    ['Step','Status','Who','When'],
    [['Create material','<span class="badge b-warn">Draft</span>','supplier-01','Day 1'],
     ['Submit for review','<span class="badge b-warn">Pending</span>','supplier-01','Day 1'],
     ['Approve','<span class="badge b-ok">Approved</span>','reviewer-01','Day 2'],
     ['Publish','<span class="badge b-open">Published</span>','publisher-01','Day 2'],
     ['Set visibility','<span class="grn">brand-01 + factory-01</span>','publisher-01','Day 2']],
) + '<p class="note">brand-01 sees new material on Day 2. Non-authorized users cannot see it.</p>'

S15 = page(15,
  "Supplier Shortens New Material Launch Time",
  "Save → Submit → Approve → Publish → Permission. New material visible to brand in 2 days.",
  "CURRENT — Weeks of Offline Process",
  "AFTER SMARTPN ATLAS — <u>Days, Not Weeks</u>",
  S15_left,
  S15_right,
  """Supplier creates a new material. Old process: email, wait for review, email brand, wait for confirmation. Weeks pass.
  <br><br>After SmartPN Atlas: create → submit → approve → publish — all in 2 days.
  publisher-01 sets visibility to brand-01 and factory-01. Brand sees it on Day 2.
  Non-authorized users cannot see it. Supplier controls the launch. Timeline is compressed."""
)

# ── S16 ────────────────────────────────────────────────────────────────────────
S16_left = '<p class="note" style="margin-bottom:10px">Brand receives new material information through offline supplier communication — email, trade shows, sales visits. Delay: weeks to months.</p>'
S16_right = tbl(
    ['New Material','Supplier','Published','Visible To','Status'],
    [['unified-new-01 / new material name 01','supplier-01','Day 2','<span class="grn">brand-01 + factory-01</span>','<span class="badge b-open">Published</span>']],
) + '<p class="note">brand-01 sees new material on Day 2. Non-authorized users see nothing.</p>'

S16 = page(16,
  "Brand Obtains New Material Information Faster",
  "Same source as S15 — brand audience perspective. Supplier launches, brand receives on Day 2.",
  "CURRENT — Brand Waits Weeks",
  "AFTER SMARTPN ATLAS — <u>Brand Receives in 2 Days</u>",
  S16_left,
  S16_right,
  """From the brand's perspective: supplier launched a new material. When do you hear about it?
  Old process: email, trade show, sales visit — weeks or months after launch.
  <br><br>After SmartPN Atlas: supplier publishes on Day 2. Brand user logs in and sees unified-new-01 immediately.
  Non-authorized users see nothing — because supplier controls visibility.
  Faster information means faster development decisions."""
)

# ── S17 ────────────────────────────────────────────────────────────────────────
S17_left = '<p class="note" style="margin-bottom:10px">Supplier performance feedback is shared offline — Word documents, email, informal conversations. No structured record. No comparison possible.</p>'
S17_right = tbl(
    ['Material','Supplier','Rating','Reason','Visibility'],
    [['unified name 01','supplier-01','<span class="grn">★★★★★</span>','Stable quality / delivery','<span class="badge b-priv">Private: brand-01</span>'],
     ['unified name 01','supplier-02','<span class="red">★☆☆☆☆</span>','Unstable quality / delivery','<span class="badge b-priv">Private: brand-01</span>']],
) + '<p class="note">Both suppliers sell identical material. brand-01 sees both comments. Non-brand users see private comments only if authorized.</p>'

S17 = page(17,
  "Brand Creates Development and Purchasing Reference from Supplier Comments",
  "Structured supplier performance comments — private or shared, attached to the material record.",
  "CURRENT — Offline, Unstructured Feedback",
  "AFTER SMARTPN ATLAS — <u>Structured Performance Record</u>",
  S17_left,
  S17_right,
  """Two suppliers sell the same material — unified name 01. supplier-02 is cheaper. But is cheaper better?
  Old process: no structured record. Performance feedback lives in email, memory, offline documents.
  <br><br>After SmartPN Atlas: brand-01 leaves a comment — supplier-01 gets 5 stars (stable quality and delivery).
  supplier-02 gets 1 star (unstable). Both comments are private to brand-01.
  Next time brand sees this material — both supplier performance records appear immediately.
  Purchasing decision is informed. Hidden risk is visible."""
)

# ── Write all files ────────────────────────────────────────────────────────────
scenarios = [
  (1, S01), (2, S02), (3, S03), (4, S04), (5, S05),
  (6, S06), (7, S07), (8, S08), (9, S09), (10, S10),
  (11, S11), (12, S12), (13, S13), (14, S14), (15, S15),
  (16, S16), (17, S17),
]

for num, html in scenarios:
    path = os.path.join(OUT, f'S{num:02d}_PPT.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Written: S{num:02d}_PPT.html')

print(f'\nDone: {len(scenarios)} files written to {OUT}')
