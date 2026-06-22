#!/usr/bin/env python3
# Full proactive CV — approved layout system. Confirmed content only; blanks where undecided.
# No brand name, no "Founder", no tech jargon (per Jim 2026-06-22).
from weasyprint import HTML
import os
OUT="/mnt/user-data/outputs"
INK="#1D1D1F"; GREY="#6E6E73"; FAINT="#AEAEB2"; LITE="#C7C7CC"; ACC="#B5540D"; CARD="#F5F5F7"; HAIR="#D2D2D7"
CSS=f"""
@page{{size:13.333in 7.5in;margin:0}} *{{margin:0;padding:0;box-sizing:border-box}}
html,body{{font-family:'Inter',sans-serif;color:{INK}}}
.page{{position:relative;width:1280px;height:720px;background:#fff;overflow:hidden;page-break-after:always}}
.nav{{position:absolute;left:96px;top:46px;font:400 13px 'Inter';letter-spacing:.3px;color:{LITE}}}
.nav .cur{{color:{ACC};font-family:'Inter Medium';font-weight:500}}
.nav .sep{{color:{HAIR};margin:0 12px}}
.navline{{position:absolute;left:96px;top:82px;width:1088px;height:1px;background:{HAIR}}}
.eyebrow{{font:500 13px/1 'Inter Medium';letter-spacing:2px;color:{GREY};text-transform:uppercase}}
.sectitle{{font:600 34px/1.1 'Inter SemiBold';letter-spacing:-1px}}
.pghead{{font:600 30px/1.15 'Inter SemiBold';letter-spacing:-.6px}}
.body{{font:400 18px/1.55 'Inter';color:{INK}}}
.small{{font:400 14px/1.5 'Inter';color:{GREY}}}
.focal{{color:{ACC};font-family:'Inter Medium';font-weight:500}}
.mk{{position:absolute;left:96px;bottom:40px;font:400 12px 'Inter';color:{FAINT};letter-spacing:1px}}
.metric{{font:600 60px/1 'Inter SemiBold';letter-spacing:-2px}}
.mlabel{{font:400 14px 'Inter';color:{GREY};margin-top:8px}}
.row{{display:flex;align-items:flex-start;gap:20px;padding:16px 0;border-bottom:1px solid {HAIR}}}
.rtitle{{font:600 19px 'Inter SemiBold'}}
.rsub{{font:400 14px/1.45 'Inter';color:{GREY};margin-top:4px}}
.rpage{{margin-left:auto;font:400 13px 'Inter';color:{FAINT};white-space:nowrap;padding-top:4px}}
.card{{background:{CARD};border-radius:14px;padding:22px 24px}}
.blank{{border:1px dashed {HAIR};background:{CARD};border-radius:14px;display:flex;align-items:center;
  justify-content:center;color:#9A9AA0;font:500 14px 'Inter Medium'}}
.lhead{{display:flex;align-items:center;gap:16px;margin-bottom:8px}}
"""
SECS=["Why","Who I am","Results","How I'd work","The ask"]
def nav(cur):
    parts=[f'<span class="{"cur" if i==cur else ""}">{s}</span>' for i,s in enumerate(SECS)]
    return '<div class="nav">'+'<span class="sep">·</span>'.join(parts)+'</div><div class="navline"></div>'
def icon(name,size=28,color=GREY,sw=2):
    P={
     "mail":'<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 8l9 6 9-6"/>',
     "layers":'<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
     "db":'<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
     "tag":'<path d="M3 11l8-8 10 10-8 8z"/><circle cx="8" cy="8" r="1.6"/>',
     "grid":'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
     "people":'<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-5 6-5s6 1.7 6 5"/><path d="M16 5.5a3.2 3.2 0 0 1 0 6"/><path d="M17 15c2.5.4 4 2 4 5"/>',
     "cycle":'<path d="M4 12a8 8 0 0 1 13-6l3 2"/><path d="M20 4v4h-4"/><path d="M20 12a8 8 0 0 1-13 6l-3-2"/><path d="M4 20v-4h4"/>',
     "pin":'<path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
     "flag":'<line x1="6" y1="3" x2="6" y2="21"/><path d="M6 4h11l-3 4 3 4H6"/>',
    }
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{P[name]}</svg>')
def head(ic,title,sub=""):
    s=f'<div class="small" style="margin-left:56px;">{sub}</div>' if sub else ""
    return (f'<div style="position:absolute;left:96px;top:130px;width:1000px;">'
            f'<div class="lhead">{icon(ic,40,INK,1.8)}<div class="pghead">{title}</div></div>{s}</div>')
P=[]

# 1 Cover (de-branded)
P.append(f"""<div class="page">
 <div style="position:absolute;left:96px;top:150px;width:600px;">
  <div class="h2" style="font:600 56px/1 'Inter SemiBold';letter-spacing:-1.5px;">Jim Kao</div>
  <div class="sub" style="font:400 26px/1.34 'Inter';letter-spacing:-.4px;margin-top:22px;">
   Where data architecture and solutions<br>meet — at the factory floor</div></div>
 <svg style="position:absolute;left:770px;top:160px;" width="420" height="420" viewBox="0 0 420 420">
  <line x1="210" y1="70" x2="210" y2="205" stroke="{HAIR}" stroke-width="1.5"/>
  <line x1="210" y1="205" x2="90" y2="340" stroke="{HAIR}" stroke-width="1.5"/>
  <line x1="210" y1="205" x2="330" y2="340" stroke="{HAIR}" stroke-width="1.5"/>
  <circle cx="210" cy="60" r="6" fill="{INK}"/><circle cx="90" cy="350" r="6" fill="{INK}"/>
  <circle cx="330" cy="350" r="6" fill="{INK}"/><circle cx="210" cy="205" r="13" fill="{ACC}"/>
  <text x="210" y="38" text-anchor="middle" font-family="Inter" font-size="17" font-weight="500">Data</text>
  <text x="90" y="384" text-anchor="middle" font-family="Inter" font-size="17" font-weight="500">Solutions</text>
  <text x="330" y="384" text-anchor="middle" font-family="Inter" font-size="17" font-weight="500">Standardization</text></svg>
 <div class="small" style="position:absolute;left:96px;bottom:74px;">
  Data Architect · Solutions · Standardization. I work only where the three intersect.<br>
  jim.kao@smartpn.com.tw · linkedin.com/in/jim-k-969579339</div></div>""")

# 2 Contents
def contents():
    rows=[
      ("mail","Why I'm writing","No matching title yet, and likely senior — so I'm reaching out directly. Please pass to the operations / business-development head.","03"),
      ("layers","Who I am","Three layers: the factory floor → turning what I know into systems → building it with AI.","04"),
      ("grid","Proven results — and what I can bring to you","Two systems built with AI: an IE system, and an innovation for material identity.","05"),
      ("pin","How I'd work with you","Based in Vietnam & Taiwan, travel as needed, English not my first language.","13"),
      ("flag","The ask","Open to a role — or a collaboration.","14"),
    ]
    b='<div style="position:absolute;left:96px;top:120px;width:1088px;"><div class="sectitle">Contents</div>'
    b+=f'<div style="width:48px;height:3px;background:{ACC};margin:14px 0 14px;"></div>'
    for ic,t,s,pg in rows:
        b+=(f'<div class="row"><div style="padding-top:2px;">{icon(ic)}</div>'
            f'<div><div class="rtitle">{t}</div><div class="rsub">{s}</div></div><div class="rpage">{pg}</div></div>')
    b+='</div>'
    return f'<div class="page">{b}<div class="mk">02 / 14 · Contents</div></div>'
P.append(contents())

# 3 Why I'm writing  [Why=0]
P.append(f"""<div class="page">{nav(0)}{head("mail","Why I'm writing")}
 <div class="body" style="position:absolute;left:96px;top:250px;width:980px;">
  <p style="margin-bottom:18px;">There may not be a posted title for this — and it likely sits at a senior level. So rather than apply to a listing, I'm writing directly. <span class="focal">Please pass this to the operations or business-development head.</span></p>
  <p style="margin-bottom:18px;">What follows is what I can do, and the contribution I believe I could bring to your company.</p>
  <p>Because there is no matching title, I'm reaching out on my own initiative — open to a role, or to a collaboration.</p></div>
 <div class="mk">03 / 14</div></div>""")

# 4 Who I am — three layers  [Who I am=1]
P.append(f"""<div class="page">{nav(1)}{head('layers','Who I am')}
 <div style="position:absolute;left:96px;top:240px;width:1088px;display:flex;flex-direction:column;gap:16px;">
  <div class="card"><div class="rtitle">1 · The factory floor</div>
   <div class="rsub" style="font-size:15px;">Twenty years on the manufacturing side. I can take a product from raw material to a finished shoe — customer development, IE, and the full development-to-production process.</div></div>
  <div class="card"><div class="rtitle">2 · Turning what I know into systems</div>
   <div class="rsub" style="font-size:15px;">I don't write code. I turn what I know into systems that actually land — through strong standardization, coordination across teams, and balancing what users expect against what a system can realistically deliver.</div></div>
  <div class="card" style="background:#fff;border:1.5px solid {ACC};"><div class="rtitle" style="color:{ACC};">3 · Building it with AI</div>
   <div class="rsub" style="font-size:15px;">Now I can design and build systems myself, working with AI. I've built two: an IE &amp; workforce-planning system, and an innovation — a material identity &amp; governance system for manufacturing.</div></div></div>
 <div class="mk">04 / 14</div></div>""")

# 5 System One — IE  [Results=2]  (no jargon footer)
P.append(f"""<div class="page">{nav(2)}{head('db','An IE system that replaced the spreadsheets','System one of two · in production today')}
 <div style="position:absolute;left:96px;top:290px;display:flex;gap:56px;">
  <div><div class="metric">290</div><div class="mlabel">shoe models</div></div>
  <div><div class="metric focal">20,434</div><div class="mlabel">IE process records</div></div>
  <div><div class="metric">4</div><div class="mlabel">departments</div></div>
  <div><div class="metric">20+</div><div class="mlabel">factory users</div></div></div>
 <div class="body" style="position:absolute;left:96px;top:470px;width:1000px;">
  Factory IE used to live in scattered spreadsheets — collected by hand, analyzed by hand, lost by hand.
  I built one system that collects, analyzes, and shows it in a single place, used across the factory.</div>
 <div class="small" style="position:absolute;left:96px;bottom:74px;">Designed and built with AI.</div>
 <div class="mk">05 / 14</div></div>""")

# 6 System Two — the innovation (intro + honest note)  [Results]
P.append(f"""<div class="page">{nav(2)}{head('tag','An innovation: material identity for manufacturing','System two of two')}
 <div class="body" style="position:absolute;left:96px;top:250px;width:980px;">
  <p style="margin-bottom:18px;">Today, the same material can carry a different identity at every step between brand, factory and supplier — so there is no common language, and no source anyone fully trusts.</p>
  <p style="margin-bottom:18px;">This innovation takes the kind of coding systems the market already uses and upgrades them to work at the manufacturing side — giving the factory floor <span class="focal">one shared language for materials.</span></p>
  <p>An honest note: I've designed the structure and built a working demo. I have not yet taken it to market — that is the step I'd want to take with the right company.</p></div>
 <div class="mk">06 / 14</div></div>""")

# 7 What it takes — four elements overview  [Results]
P.append(f"""<div class="page">{nav(2)}{head('grid','What it takes to make this work')}
 <div style="position:absolute;left:96px;top:250px;width:1088px;display:grid;grid-template-columns:1fr 1fr;gap:18px;">
  <div class="card"><div class="rtitle">1 · Real contributions to a brand</div><div class="rsub" style="font-size:14px;">Not a vision — concrete ways it pays off for a brand.</div></div>
  <div class="card"><div class="rtitle">2 · A structure I've built</div><div class="rsub" style="font-size:14px;">A shared language + governance — designed and demonstrated; not yet commercialized.</div></div>
  <div class="card"><div class="rtitle">3 · A Southeast-Asia onboarding team</div><div class="rsub" style="font-size:14px;">People to guide suppliers online — because rollouts fail on people, not systems.</div></div>
  <div class="card" style="background:#fff;border:1.5px solid {ACC};"><div class="rtitle" style="color:{ACC};">4 · Data providers: passive → active</div><div class="rsub" style="font-size:14px;">Turning data from a cost into a reason suppliers maintain it themselves.</div></div></div>
 <div class="mk">07 / 14</div></div>""")

# 8 Element 2 — structure built  [Results]
P.append(f"""<div class="page">{nav(2)}{head("layers","A structure I've designed and built")}
 <div class="body" style="position:absolute;left:96px;top:250px;width:520px;">
  <p style="margin-bottom:16px;">Two layers make a shared language work:</p>
  <p style="margin-bottom:16px;"><b>Identity</b> — the same material has the same name, everywhere.</p>
  <p><b>Governance</b> — the owner decides who may see and use it.</p></div>
 <div style="position:absolute;left:700px;top:240px;width:484px;">
  <div class="card" style="background:#fff;border:1.5px solid {ACC};text-align:center;padding:26px;margin-bottom:16px;"><span class="focal" style="font:600 22px 'Inter SemiBold';">Governance</span></div>
  <div class="card" style="text-align:center;padding:26px;"><span style="font:600 22px 'Inter SemiBold';">Identity</span></div></div>
 <div class="small" style="position:absolute;left:96px;bottom:74px;">Designed and demonstrated as a working system — not yet taken to market.</div>
 <div class="mk">08 / 14</div></div>""")

# 9 Element 3 — SE Asia onboarding team  [Results]
P.append(f"""<div class="page">{nav(2)}{head('people','A Southeast-Asia onboarding team')}
 <div class="body" style="position:absolute;left:96px;top:250px;width:980px;">
  <p style="margin-bottom:18px;">Suppliers in Southeast Asia are small and lightly standardized. It isn't that they're unwilling — <span class="focal">they're missing a guide.</span></p>
  <p style="margin-bottom:18px;">So I'd build a local team to guide them online: helping them create, classify and exchange their source data.</p>
  <p>A system is rarely why a rollout fails. People are. That's the part I know how to lead.</p></div>
 <div class="mk">09 / 14</div></div>""")

# 10 Element 4 — passive -> active  [Results]
P.append(f"""<div class="page">{nav(2)}{head('cycle','Data providers: from passive to active')}
 <div style="position:absolute;left:96px;top:270px;width:500px;">
  <div class="small" style="text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Before</div>
  <div class="card" style="height:200px;padding:26px;"><div class="body">Suppliers filled in data only when a brand demanded it. Data was a cost.</div></div></div>
 <div style="position:absolute;left:640px;top:270px;width:500px;">
  <div class="small" style="text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;color:{ACC};">After</div>
  <div class="card" style="height:200px;padding:26px;background:#fff;border:1.5px solid {ACC};"><div class="body">They can be found by brands and choose who to share with. Data becomes a way to win business — so they maintain it themselves.</div></div></div>
 <div class="mk">10 / 14</div></div>""")

# 11 Element 1 — contributions to a brand  BLANK
P.append(f"""<div class="page">{nav(2)}{head('grid','Real contributions to a brand')}
 <div class="blank" style="position:absolute;left:96px;top:250px;width:1088px;height:340px;">內容待確認（要素 ① 用哪幾個 scenario 證明，尚未挑選）— 留空，待補</div>
 <div class="mk">11 / 14 · BLANK</div></div>""")

# 12 What I can bring summary  BLANK
P.append(f"""<div class="page">{nav(2)}{head('grid','What I can bring to you')}
 <div class="blank" style="position:absolute;left:96px;top:250px;width:1088px;height:340px;">內容待確認（潛在貢獻彙整，待 scenario 與細節定後再補）— 留空</div>
 <div class="mk">12 / 14 · BLANK</div></div>""")

# 13 How I'd work  [How I'd work=3]
P.append(f"""<div class="page">{nav(3)}{head("pin","How I'd work with you")}
 <div class="body" style="position:absolute;left:96px;top:250px;width:980px;">
  <p style="margin-bottom:18px;">Based mainly in Vietnam and Taiwan, and able to travel as needed.</p>
  <p>English isn't my first language. I'll say that plainly — and I'd like the work to sharpen it.</p></div>
 <div class="mk">13 / 14</div></div>""")

# 14 The ask  [The ask=4]
P.append(f"""<div class="page">{nav(4)}{head('flag','The ask')}
 <div class="body" style="position:absolute;left:96px;top:250px;width:980px;">
  <p style="margin-bottom:18px;">The pages above are what I can do, and the contribution I believe I could bring.</p>
  <p style="margin-bottom:18px;">Because this work has no matching title and likely sits at a senior level, I'm writing on my own initiative — <span class="focal">to ask for the chance of a role, or a collaboration.</span></p>
  <p class="small">Jim Kao · jim.kao@smartpn.com.tw · linkedin.com/in/jim-k-969579339</p></div>
 <div class="mk">14 / 14</div></div>""")

HTML(string=f"<style>{CSS}</style>"+"".join(P)).write_pdf(f"{OUT}/Jim_CV_v2_draft.pdf")
print("pages:",len(P))
