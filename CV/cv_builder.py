#!/usr/bin/env python3
# FINAL sendable CV. Approved layout system + locked content + own visuals.
import os, base64
from weasyprint import HTML
OUT="/mnt/user-data/outputs"
INK="#1D1D1F"; GREY="#6E6E73"; FAINT="#AEAEB2"; LITE="#C7C7CC"; ACC="#B5540D"; CARD="#F5F5F7"; HAIR="#D2D2D7"
FACES=base64.b64encode(open("/mnt/user-data/uploads/1782120442510_image.png","rb").read()).decode()
CSS=f"""
@page{{size:13.333in 7.5in;margin:0}} *{{margin:0;padding:0;box-sizing:border-box}}
html,body{{font-family:'Inter',sans-serif;color:{INK}}}
.page{{position:relative;width:1280px;height:720px;background:#fff;overflow:hidden;page-break-after:always}}
.nav{{position:absolute;left:96px;top:46px;font:400 13px 'Inter';letter-spacing:.3px;color:{LITE}}}
.nav .cur{{color:{ACC};font-family:'Inter Medium';font-weight:500}} .nav .sep{{color:{HAIR};margin:0 12px}}
.navline{{position:absolute;left:96px;top:82px;width:1088px;height:1px;background:{HAIR}}}
.sectitle{{font:600 34px 'Inter SemiBold';letter-spacing:-1px}}
.pghead{{font:600 28px/1.18 'Inter SemiBold';letter-spacing:-.5px}}
.body{{font:400 18px/1.55 'Inter';color:{INK}}}
.small{{font:400 14px/1.5 'Inter';color:{GREY}}}
.focal{{color:{ACC};font-family:'Inter Medium';font-weight:500}}
.mk{{position:absolute;left:96px;bottom:40px;font:400 12px 'Inter';color:{FAINT};letter-spacing:1px}}
.card{{background:{CARD};border-radius:14px;padding:20px 22px}}
.rtitle{{font:600 19px 'Inter SemiBold'}} .rsub{{font:400 14px/1.45 'Inter';color:{GREY};margin-top:5px}}
.row{{display:flex;align-items:flex-start;gap:18px;padding:15px 0;border-bottom:1px solid {HAIR}}}
.rpage{{margin-left:auto;font:400 13px 'Inter';color:{FAINT};padding-top:3px}}
.metric{{font:600 58px/1 'Inter SemiBold';letter-spacing:-2px}} .mlabel{{font:400 14px 'Inter';color:{GREY};margin-top:8px}}
.lhead{{display:flex;align-items:center;gap:15px;margin-bottom:8px}}
"""
SECS=["Why","Who I am","Results","How I'd work","The ask"]
def nav(c):
    return '<div class="nav">'+'<span class="sep">·</span>'.join(f'<span class="{"cur" if i==c else ""}">{s}</span>' for i,s in enumerate(SECS))+'</div><div class="navline"></div>'
def ic(name,size=28,color=GREY,sw=2):
    P={"mail":'<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 8l9 6 9-6"/>',
       "layers":'<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
       "db":'<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
       "tag":'<path d="M3 11l8-8 10 10-8 8z"/><circle cx="8" cy="8" r="1.6"/>',
       "grid":'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
       "people":'<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-5 6-5s6 1.7 6 5"/><path d="M16 5.5a3.2 3.2 0 0 1 0 6"/><path d="M17 15c2.5.4 4 2 4 5"/>',
       "search":'<circle cx="10" cy="10" r="6"/><line x1="20" y1="20" x2="15" y2="15"/>',
       "gift":'<path d="M20 12v8H4v-8"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="7" x2="12" y2="20"/><path d="M12 7S10 2 7 4s5 3 5 3M12 7s2-5 5-3-5 3-5 3"/>',
       "pin":'<path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
       "flag":'<line x1="6" y1="3" x2="6" y2="21"/><path d="M6 4h11l-3 4 3 4H6"/>'}
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{P[name]}</svg>'
def head(icn,title,sub=""):
    s=f'<div class="small" style="margin-left:43px;">{sub}</div>' if sub else ""
    return f'<div style="position:absolute;left:96px;top:128px;width:1050px;"><div class="lhead">{ic(icn,38,INK,1.8)}<div class="pghead">{title}</div></div>{s}</div>'
P=[]

# 1 Cover
P.append(f"""<div class="page">
 <div style="position:absolute;left:96px;top:150px;width:600px;">
  <div style="font:600 56px/1 'Inter SemiBold';letter-spacing:-1.5px;">Jim Kao</div>
  <div style="font:400 26px/1.34 'Inter';letter-spacing:-.4px;margin-top:22px;">Where data architecture and solutions<br>meet — at the factory floor</div></div>
 <svg style="position:absolute;left:770px;top:160px;" width="420" height="420" viewBox="0 0 420 420">
  <line x1="210" y1="70" x2="210" y2="205" stroke="{HAIR}" stroke-width="1.5"/><line x1="210" y1="205" x2="90" y2="340" stroke="{HAIR}" stroke-width="1.5"/><line x1="210" y1="205" x2="330" y2="340" stroke="{HAIR}" stroke-width="1.5"/>
  <circle cx="210" cy="60" r="6" fill="{INK}"/><circle cx="90" cy="350" r="6" fill="{INK}"/><circle cx="330" cy="350" r="6" fill="{INK}"/><circle cx="210" cy="205" r="13" fill="{ACC}"/>
  <text x="210" y="38" text-anchor="middle" font-family="Inter" font-size="17" font-weight="500">Data</text>
  <text x="90" y="384" text-anchor="middle" font-family="Inter" font-size="17" font-weight="500">Solutions</text>
  <text x="330" y="384" text-anchor="middle" font-family="Inter" font-size="17" font-weight="500">Standardization</text></svg>
 <div class="small" style="position:absolute;left:96px;bottom:74px;">Data Architect · Solutions · Standardization. I work only where the three intersect.<br>jim.kao@smartpn.com.tw · linkedin.com/in/jim-k-969579339</div></div>""")

# 2 Contents
rows=[("mail","Why I'm writing","A self-recommendation — please pass to the operations / business head.","03"),
      ("layers","Who I am","Three layers: the factory floor → turning what I know into systems → building with AI.","04"),
      ("grid","Proven results — and what I can bring to you","Two systems built with AI, and what they can do for you.","05"),
      ("pin","How I'd work with you","Based in Vietnam & Taiwan, travel as needed, English not my first language.","13"),
      ("flag","The ask","Open to a role — or a collaboration — in operations or business.","14")]
c='<div style="position:absolute;left:96px;top:120px;width:1088px;"><div class="sectitle">Contents</div><div style="width:48px;height:3px;background:'+ACC+';margin:14px 0;"></div>'
for icn,t,s,pg in rows:
    c+=f'<div class="row"><div style="padding-top:2px;">{ic(icn)}</div><div><div class="rtitle">{t}</div><div class="rsub">{s}</div></div><div class="rpage">{pg}</div></div>'
P.append(f'<div class="page">{c}</div><div class="mk">02 / 14 · Contents</div></div>')

# 3 Why I'm writing
P.append(f"""<div class="page">{nav(0)}{head('mail',"Why I'm writing")}
 <div class="body" style="position:absolute;left:96px;top:240px;width:980px;">
  <p style="margin-bottom:16px;">To the HR team — this is a <span class="focal">self-recommendation</span>, not an application to a posted role. I've put together an honest analysis of my experience and what I can do, for your reference.</p>
  <p style="margin-bottom:16px;">Based on it, I believe I could contribute at a senior level in operations or business development.</p>
  <p>If that fits a need you have, I'd be grateful if you would pass this along to the relevant leader.</p></div>
 <div class="mk">03 / 14</div></div>""")

# 4 Who I am
P.append(f"""<div class="page">{nav(1)}{head('layers','Who I am')}
 <div style="position:absolute;left:96px;top:235px;width:1088px;display:flex;flex-direction:column;gap:14px;">
  <div class="card"><div class="rtitle">1 · The factory floor</div><div class="rsub" style="font-size:15px;">Twenty years on the manufacturing side. I take a product from raw material to a finished shoe — customer development, IE, and the full chain: IDs, BOM, SOP, costing, inventory.</div></div>
  <div class="card"><div class="rtitle">2 · Turning what I know into systems</div><div class="rsub" style="font-size:15px;">I don't write code. I turn what I know into systems that land — through standardization, coordination across teams, and balancing what users expect with what a system can deliver. I standardized a footwear group's PDM/ERP: 4 factories, 3 countries, built to replicate.</div></div>
  <div class="card" style="background:#fff;border:1.5px solid {ACC};"><div class="rtitle" style="color:{ACC};">3 · Building it with AI</div><div class="rsub" style="font-size:15px;">Now I design and build systems myself, with AI. I've built two: an IE &amp; workforce-planning system, and an innovation — a material identity &amp; governance system for manufacturing.</div></div></div>
 <div class="mk">04 / 14</div></div>""")

# 5 System One IE
P.append(f"""<div class="page">{nav(2)}{head('db','System one — an IE system that replaced the spreadsheets','In production today')}
 <div style="position:absolute;left:96px;top:285px;display:flex;gap:54px;">
  <div><div class="metric">290</div><div class="mlabel">shoe models</div></div>
  <div><div class="metric focal">20,434</div><div class="mlabel">IE process records</div></div>
  <div><div class="metric">4</div><div class="mlabel">departments</div></div>
  <div><div class="metric">20+</div><div class="mlabel">factory users</div></div></div>
 <div class="body" style="position:absolute;left:96px;top:455px;width:1000px;">Factory IE used to live in scattered spreadsheets — collected, analyzed and lost by hand. I built one system that collects, analyzes and shows it in a single place, used across the factory.</div>
 <div class="small" style="position:absolute;left:96px;bottom:74px;">Designed and built with AI.</div>
 <div class="mk">05 / 14</div></div>""")

# 6 System Two innovation intro
P.append(f"""<div class="page">{nav(2)}{head('tag','System two — an innovation: material identity for manufacturing')}
 <div class="body" style="position:absolute;left:96px;top:240px;width:980px;">
  <p style="margin-bottom:16px;">Today the same material can carry a different identity at every step between brand, factory and supplier — so there is no common language, and no source anyone fully trusts.</p>
  <p style="margin-bottom:16px;">This upgrades the coding systems the market already uses so they work at the manufacturing side — giving the factory floor <span class="focal">one shared language for materials.</span></p>
  <p>An honest note: I've designed the structure and built a working demo. I haven't taken it to market — that's the step I'd take with the right company.</p></div>
 <div class="mk">06 / 14</div></div>""")

# 7 four elements
P.append(f"""<div class="page">{nav(2)}{head('grid','What it takes to make this work')}
 <div style="position:absolute;left:96px;top:240px;width:1088px;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
  <div class="card"><div class="rtitle">1 · Real contributions to a brand</div><div class="rsub" style="font-size:14px;">Concrete value, not a vision.</div></div>
  <div class="card"><div class="rtitle">2 · A structure I've built</div><div class="rsub" style="font-size:14px;">Shared identity + governance — designed &amp; demonstrated; not yet commercialized.</div></div>
  <div class="card"><div class="rtitle">3 · A Southeast-Asia onboarding team</div><div class="rsub" style="font-size:14px;">People to guide suppliers online.</div></div>
  <div class="card" style="background:#fff;border:1.5px solid {ACC};"><div class="rtitle" style="color:{ACC};">4 · Data providers: passive → active</div><div class="rsub" style="font-size:14px;">Data becomes a reason suppliers maintain it themselves.</div></div></div>
 <div class="mk">07 / 14</div></div>""")

# 8 element 2 structure
P.append(f"""<div class="page">{nav(2)}{head('layers',"Element 2 — a structure I've built")}
 <div class="body" style="position:absolute;left:96px;top:245px;width:520px;">
  <p style="margin-bottom:14px;">Two layers make a shared language work:</p>
  <p style="margin-bottom:14px;"><b>Identity</b> — the same material has the same name, everywhere.</p>
  <p><b>Governance</b> — the owner decides who may see and use it.</p></div>
 <div style="position:absolute;left:700px;top:240px;width:484px;">
  <div class="card" style="background:#fff;border:1.5px solid {ACC};text-align:center;padding:24px;margin-bottom:14px;"><span class="focal" style="font:600 22px 'Inter SemiBold';">Governance</span></div>
  <div class="card" style="text-align:center;padding:24px;"><span style="font:600 22px 'Inter SemiBold';">Identity</span></div></div>
 <div class="small" style="position:absolute;left:96px;bottom:74px;">Designed and demonstrated as a working system — not yet taken to market.</div>
 <div class="mk">08 / 14</div></div>""")

# 9 element 3 SE Asia
P.append(f"""<div class="page">{nav(2)}{head('people','Element 3 — a Southeast-Asia onboarding team')}
 <div class="body" style="position:absolute;left:96px;top:245px;width:980px;">
  <p style="margin-bottom:16px;">Suppliers in Southeast Asia are small and lightly standardized. It isn't that they're unwilling — <span class="focal">they're missing a guide.</span></p>
  <p style="margin-bottom:16px;">I can build and lead a local team to bring them online — helping them create, classify and exchange their source data.</p>
  <p>A system is rarely why a rollout fails. People are. That's the part I know how to lead.</p></div>
 <div class="mk">09 / 14</div></div>""")

# 10 element 4 passive->active (FACES image)
P.append(f"""<div class="page">{nav(2)}
 <div style="position:absolute;left:96px;top:120px;"><div class="lhead"><div class="pghead">Element 4 — data providers: from passive to active</div></div></div>
 <img src="data:image/png;base64,{FACES}" style="position:absolute;left:50%;top:185px;transform:translateX(-50%);width:560px;height:auto;"/>
 <div class="body" style="position:absolute;left:96px;bottom:80px;width:1088px;color:{GREY};">When their data can be <span style="color:{INK};font-family:'Inter Medium';">found</span>, it gains <span style="color:{INK};font-family:'Inter Medium';">commercial value</span> — and that is what turns a passive provider into an active one.</div>
 <div class="mk">10 / 14</div></div>""")

# 11 element 1 contributions to a brand (general content)
P.append(f"""<div class="page">{nav(2)}{head('search','Element 1 — real contributions to a brand')}
 <div class="body" style="position:absolute;left:96px;top:245px;width:980px;">
  <p>A shared, <span class="focal">trusted identity</span> lets a brand find identical or alternative materials faster, compare suppliers on reliable data, and cut the cost of chasing material information across the chain.</p></div>
 <div class="small" style="position:absolute;left:96px;top:360px;">（具體 scenario 案例之後再選填，不影響整體完整度。）</div>
 <div class="mk">11 / 14</div></div>""")

# 12 what I can bring summary
P.append(f"""<div class="page">{nav(2)}{head('gift','What I can bring to you')}
 <div style="position:absolute;left:96px;top:245px;width:1088px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
  <div class="card"><div class="rtitle">More SE-Asia suppliers</div><div class="rsub" style="font-size:14px;">Brought online with data that's usable and exchangeable.</div></div>
  <div class="card" style="background:#fff;border:1.5px solid {ACC};"><div class="rtitle" style="color:{ACC};">A trusted source</div><div class="rsub" style="font-size:14px;">For everyone downstream — and credible manufacturing-side analysis.</div></div>
  <div class="card"><div class="rtitle">Stronger stickiness</div><div class="rsub" style="font-size:14px;">With the clients you already have.</div></div></div>
 <div class="small" style="position:absolute;left:96px;top:430px;">For your clients: lower cost, a transparent supply chain.</div>
 <div class="mk">12 / 14</div></div>""")

# 13 how I'd work
P.append(f"""<div class="page">{nav(3)}{head('pin',"How I'd work with you")}
 <div class="body" style="position:absolute;left:96px;top:245px;width:980px;">
  <p style="margin-bottom:16px;">Based mainly in Vietnam and Taiwan, and able to travel as needed.</p>
  <p>English isn't my first language. I'll say that plainly — and I'd like the work to sharpen it.</p></div>
 <div class="mk">13 / 14</div></div>""")

# 14 the ask
P.append(f"""<div class="page">{nav(4)}{head('flag','The ask')}
 <div class="body" style="position:absolute;left:96px;top:245px;width:980px;">
  <p style="margin-bottom:16px;">The pages above are my own analysis of what I can do, and the contribution I believe I could bring.</p>
  <p style="margin-bottom:16px;">Because this work has no matching title and likely sits at a senior level, I'm writing on my own initiative — to ask, through you, for the chance of <span class="focal">a role or a collaboration in operations or business.</span></p>
  <p class="small">Jim Kao · jim.kao@smartpn.com.tw · linkedin.com/in/jim-k-969579339</p></div>
 <div class="mk">14 / 14</div></div>""")

HTML(string=f"<style>{CSS}</style>"+"".join(P)).write_pdf(f"{OUT}/Jim_CV_sendable_v1.pdf")
print("pages:",len(P))
