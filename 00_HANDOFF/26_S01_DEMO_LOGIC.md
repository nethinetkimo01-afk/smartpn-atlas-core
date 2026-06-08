# S01 ??Demo Logic and Design Specification
Version: v1.0 | 2026-06-02
Status: CONFIRMED. Use for PPT animation, Demo software, and LinkedIn image.

---

## S01 Title
Complete, Timely, and Private Material Library

## Core Message
Your material library is built by your team. Your supplier maintains theirs.
Every day, new materials are added on their side. You do not see them.
SHARED LANGUAGE + GOVERNANCE LAYER is the solution.

---

## PPT Animation Logic (One sentence = one element appears)

Step 1: Supplier A appears
Step 2: Data 1, Data 2 appear (Past, Internal Team)
You say: "You have 2 materials from Supplier A"

Step 3: Question marks appear where Data 3 and 4 should be
You say: "But actually there are 4"

Step 4: Updated column appears - Data 3 and 4 show TODAY in RED
You say: "2 were added today by your supplier"

Step 5: Maintained by column appears - shows Supplier
You say: "Because supplier maintains their own data"

Step 6: Permission column appears - Data 4 shows OPEN in RED
You say: "And this one is visible to you"

---

## Table Structure (Both PPT and Demo Software)

Columns: SUPPLIER | DATA | UPDATED | MAINTAINED BY | CODE | NAME | PERMISSION

Current (before):
Row 1: A | 1 | Past | Internal Team | Independent | Independent | PRIVATE
Row 2: A | 2 | Past | Internal Team | Independent | Independent | PRIVATE
Row 3: (empty)
Row 4: (empty)

After SmartPN Atlas:
Row 1: A | 1 | Past | Supplier | Shared Language | Shared Language | PRIVATE
Row 2: A | 2 | Past | Supplier | Shared Language | Shared Language | PRIVATE
Row 3: A | 3 | TODAY (RED) | Supplier | Shared Language | Shared Language | PRIVATE
Row 4: A | 4 | TODAY (RED) | Supplier | Shared Language | Shared Language | OPEN (RED)

---

## Design Rules

Colors:
- TODAY = RED (same red as Incomplete in LinkedIn image)
- OPEN = RED
- Normal rows = black text, white background

Key visual logic:
- TODAY and Incomplete use SAME RED color
- Reader eye connects: TODAY caused the Incomplete
- One color tells the whole story

---

## Demo Software Interactions

1. Show Current state (2 rows, Internal Team, Independent codes)
2. Click After SmartPN Atlas
3. Row 3 and 4 appear with TODAY in red
4. Maintained by changes to Supplier
5. Code and Name change to Shared Language

---

## LinkedIn Image Connection

LinkedIn image uses same logic:
- "Your Material Library Is Incomplete." - Incomplete in RED
- Two lists: Yours vs Actual
- Actual shows Material 3 and 4 with TODAY in same RED
- Reader eye connects Incomplete = TODAY = same problem

---

## Reduce Unfamiliarity Rule

PPT design = Demo software design = same visual system
- Same colors (#54463A accent, RED for emphasis)
- Same terminology (Shared Language, Maintained by, OPEN / PRIVATE)
- Same mock data structure
- Customer never sees something new when moving from PPT to Demo