#!/usr/bin/env python3
import base64
FACES=base64.b64encode(open("/mnt/user-data/uploads/1782120442510_image.png","rb").read()).decode()
INK="#1D1D1F"; GREY="#6E6E73"; FAINT="#AEAEB2"; LITE="#C7C7CC"; ACC="#B5540D"; CARD="#F5F5F7"; HAIR="#D2D2D7"
N=15
def nav(cur):
    secs=["Why","Who I am","Results","How I'd work","The ask"]
    out=[f'<span style="color:{ACC if i==cur else LITE};font-weight:{600 if i==cur else 400}">{s}</span>' for i,s in enumerate(secs)]
    return (f'<div style="position:absolute;left:64px;top:40px;font-size:13px">'
            + f'<span style="color:{HAIR};margin:0 10px">·</span>'.join(out)
            + f'</div><div style="position:absolute;left:64px;top:72px;width:1152px;height:1px;background:{HAIR}"></div>')
def head(t,sub=""):
    s=f'<div style="font-size:14px;color:{GREY};margin-top:8px">{sub}</div>' if sub else ""
    return f'<div style="position:absolute;left:64px;top:116px;width:1110px"><div style="font-size:27px;font-weight:600;letter-spacing:-.5px;line-height:1.18">{t}</div>{s}</div>'
def mk(n,note=""): return f'<div style="position:absolute;left:64px;bottom:32px;font-size:12px;color:{FAINT}">{n} / {N}{note}</div>'
def fo(t): return f'<span style="color:{ACC};font-weight:600">{t}</span>'
def card(t,b,hl=False,tag="div"):
    bd=f"border:1.5px solid {ACC};background:#fff" if hl else f"background:{CARD}"
    tc=ACC if hl else INK
    return (f'<div style="{bd};border-radius:14px;padding:17px 20px">'
            f'<div style="font-size:18px;font-weight:600;color:{tc}">{t}</div>'
            f'<div style="font-size:14px;color:{GREY};margin-top:6px;line-height:1.45">{b}</div></div>')
def body(html,top=240,w=1010,fs=18):
    return f'<div style="position:absolute;left:64px;top:{top}px;width:{w}px;font-size:{fs}px;line-height:1.6">{html}</div>'
P=[]

# 1 Why (first page)
P.append(nav(0)+head("Why I'm writing")+body(
 f'<p style="margin-bottom:16px">To the HR team — this is a {fo("self-recommendation")}, not an application to a posted role. I\'ve attached an honest analysis of my experience and what I can do, for your reference.</p>'
 f'<p style="margin-bottom:16px">Based on it, I believe I could contribute at a senior level in operations or business development.</p>'
 f'<p>If that fits a need you have, I\'d be grateful if you would pass this along to the relevant leader.</p>',230,1000,19)+mk(1))

# 2 contents
rows=[("Why I'm writing","Self-recommendation — please pass to the operations / business head.","01"),
      ("Who I am","The factory floor → turning what I know into systems → building with AI.","03"),
      ("Proven results — and what I can bring to you","Two systems built with AI; what the innovation is and what it brings.","04"),
      ("How I'd work with you","Vietnam & Taiwan, travel as needed, English not my first language.","14"),
      ("The ask","A role — or a collaboration — in operations or business.","15")]
rh=""
for t,s,p in rows:
    rh+=(f'<div style="display:flex;gap:18px;padding:15px 0;border-bottom:1px solid {HAIR}">'
         f'<div style="flex:1"><div style="font-size:19px;font-weight:600">{t}</div>'
         f'<div style="font-size:14px;color:{GREY};margin-top:4px">{s}</div></div>'
         f'<div style="font-size:13px;color:{FAINT}">{p}</div></div>')
P.append(f'<div style="position:absolute;left:64px;top:110px;width:1152px"><div style="font-size:32px;font-weight:600;letter-spacing:-1px">Contents</div><div style="width:48px;height:3px;background:{ACC};margin:12px 0"></div>{rh}</div>'+mk(2," · Contents"))

# 3 Who I am
P.append(nav(1)+head("Who I am")+
 f'<div style="position:absolute;left:64px;top:200px;width:1152px;display:flex;flex-direction:column;gap:12px">'
 +card("1 · The factory floor","Twenty years on the manufacturing side. Raw material to a finished shoe — customer development, IE, and the full chain: IDs, BOM, SOP, costing, inventory.")
 +card("2 · Turning what I know into systems","I don't write code. I turn what I know into systems that land — through standardization, coordination across teams, and balancing what users expect with what a system can deliver. I standardized a footwear group's PDM/ERP: 4 factories, 3 countries, built to replicate.")
 +card("3 · Building it with AI","Now I design and build systems myself, with AI. I've built two: an IE & workforce-planning system, and an innovation — a material identity & governance system for manufacturing.",True)
 +'</div>'+mk(3))

# 4 IE
P.append(nav(2)+head("System one — an IE system that replaced the spreadsheets","In production today")+
 f'<div style="position:absolute;left:64px;top:275px;display:flex;gap:52px">'
 +''.join(f'<div><div style="font-size:56px;font-weight:600;letter-spacing:-2px;color:{c}">{v}</div><div style="font-size:14px;color:{GREY};margin-top:8px">{l}</div></div>'
          for v,l,c in [("290","shoe models",INK),("20,434","IE process records",ACC),("4","departments",INK),("20+","factory users",INK)])
 +'</div>'
 +body("Factory IE used to live in scattered spreadsheets — collected, analyzed and lost by hand. I built one system that collects, analyzes and shows it in a single place, used across the factory.",440,1020,18)
 +f'<div style="position:absolute;left:64px;bottom:60px;font-size:14px;color:{GREY}">Designed and built with AI.</div>'+mk(4))

# 5 innovation intro
P.append(nav(2)+head("System two — an innovation: material identity for manufacturing")+body(
 f'<p style="margin-bottom:14px">Today the same material can carry a different identity at every step between brand, factory and supplier — so there is no common language, and no source anyone fully trusts.</p>'
 f'<p style="margin-bottom:14px">This upgrades the coding systems the market already uses so they work at the manufacturing side — giving the factory floor {fo("one shared language for materials")}. It is the layer, across brand, OEM and supplier, that no tool owns today.</p>'
 f'<p>An honest note: I\'ve designed the structure and built a working demo — not yet taken to market.</p>',235,1010,18)+mk(5))

# 6 FOUR PILLARS (system body) — restored
P.append(nav(2)+head("The system, in four parts")+
 f'<div style="position:absolute;left:64px;top:225px;width:1152px;display:grid;grid-template-columns:1fr 1fr;gap:14px">'
 +card("Identity","One shared ID — the same material has the same name, everywhere.",True)
 +card("Governance","The owner decides who may see and use it.")
 +card("Decision","A trusted source, so the right call can be made.")
 +card("Motivation","Data shifts from passive to active.")
 +'</div>'+mk(6))

# 7 Shared language two layers (Identity + Governance contrast)
P.append(nav(2)+head("A shared language has two layers")+
 body("<b>Identity</b> — same material, same name, everywhere.<br><b>Governance</b> — the owner decides who may see and use it.",235,520,18)
 +f'<div style="position:absolute;left:660px;top:225px;width:524px">'
 +f'<div style="background:{CARD};border-radius:14px;padding:18px 20px;margin-bottom:12px"><div style="font-size:13px;color:{GREY};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Open to all</div><div style="font-size:16px">No one adopts it — suppliers won\'t expose what they can\'t control.</div></div>'
 +f'<div style="border:1.5px solid {ACC};background:#fff;border-radius:14px;padding:18px 20px"><div style="font-size:13px;color:{ACC};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">With permission</div><div style="font-size:16px">The owner decides who sees what — so it finally spreads.</div></div></div>'
 +f'<div style="position:absolute;left:64px;bottom:56px;width:1100px;font-size:14px;color:{GREY}">Not a central database — each supplier keeps data in their own system; {fo("permission")} sends the right data to the right party, and it never leaves the owner.</div>'+mk(7))

# 8 Decision
P.append(nav(2)+head("Decision — a source everyone can trust")+body(
 f'<p style="margin-bottom:16px">When identity is shared and governed, the data tied to it can finally be trusted.</p>'
 f'<p>That gives a brand a {fo("trusted source")} for the right call — built on the factory\'s real bill of materials, not on guesswork — and credible analysis downstream.</p>',245,1000,19)+mk(8))

# 9 Motivation (faces)
P.append(nav(2)+'<div style="position:absolute;left:64px;top:116px;font-size:27px;font-weight:600;letter-spacing:-.5px">Motivation — data providers: from passive to active</div>'
 +f'<img src="data:image/png;base64,{FACES}" style="position:absolute;left:50%;top:185px;transform:translateX(-50%);width:540px"/>'
 +f'<div style="position:absolute;left:64px;bottom:56px;width:1152px;font-size:19px;line-height:1.5;color:{GREY}">When their data can be <b style="color:{INK}">found</b>, it gains <b style="color:{INK}">commercial value</b> — and that is what turns a passive provider into an active one.</div>'+mk(9))

# 10 four elements (success conditions)
P.append(nav(2)+head("What it takes to make this work")+
 f'<div style="position:absolute;left:64px;top:225px;width:1152px;display:grid;grid-template-columns:1fr 1fr;gap:14px">'
 +card("1 · Real contributions to a brand","Concrete value, not a vision.")
 +card("2 · A structure I've built","Designed and demonstrated; not yet commercialized.")
 +card("3 · A Southeast-Asia onboarding team","People to guide suppliers online.",True)
 +card("4 · Data providers: passive → active","Already shown — data they maintain themselves.")
 +'</div>'+mk(10))

# 11 element 3 SE asia
P.append(nav(2)+head("A Southeast-Asia onboarding team")+body(
 f'<p style="margin-bottom:16px">Suppliers in Southeast Asia are small and lightly standardized. It isn\'t that they\'re unwilling — {fo("they\'re missing a guide")}.</p>'
 f'<p style="margin-bottom:16px">I can build and lead a local team to bring them online — helping them create, classify and exchange their source data.</p>'
 f'<p>A system is rarely why a rollout fails. People are. That\'s the part I know how to lead.</p>',245,1000,19)+mk(11))

# 12 element 1 contributions to a brand (scenario blank)
P.append(nav(2)+head("Real contributions to a brand")+body(
 f'<p>A shared, {fo("trusted identity")} lets a brand find identical or alternative materials faster, compare suppliers on reliable data, and cut the cost of chasing material information across the chain.</p>',245,1000,19)
 +f'<div style="position:absolute;left:64px;top:360px;font-size:14px;color:{GREY}">(具體 scenario 案例之後再選填 — 留空)</div>'+mk(12," · scenario 待補"))

# 13 three contributions
P.append(nav(2)+head("What this brings to your company")+
 f'<div style="position:absolute;left:64px;top:235px;width:1152px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px">'
 +card("More SE-Asia suppliers","Brought online with usable, exchangeable data.")
 +card("A trusted source","For everyone downstream — and credible manufacturing-side analysis.",True)
 +card("Stronger stickiness","With the clients you already have.")
 +'</div>'
 +f'<div style="position:absolute;left:64px;top:410px;font-size:14px;color:{GREY}">For your clients: lower cost, a transparent supply chain.</div>'+mk(13))

# 14 how I'd work
P.append(nav(3)+head("How I'd work with you")+body(
 '<p style="margin-bottom:16px">Based mainly in Vietnam and Taiwan, and able to travel as needed.</p>'
 '<p>English isn\'t my first language. I\'ll say that plainly — and I\'d like the work to sharpen it.</p>',245,1000,19)+mk(14))

# 15 the ask
P.append(nav(4)+head("The ask")+body(
 '<p style="margin-bottom:16px">The pages above are my own analysis of what I can do, and the contribution I believe I could bring.</p>'
 f'<p style="margin-bottom:16px">Because this work has no matching title and likely sits at a senior level, I\'m writing on my own initiative — to ask, through you, for the chance of {fo("a role or a collaboration in operations or business")}.</p>'
 f'<p style="font-size:14px;color:{GREY}">Jim Kao · jim.kao@smartpn.com.tw · linkedin.com/in/jim-k-969579339</p>',245,1000,19)+mk(15))

html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jim Kao — CV preview</title>
<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#e9e9ec;font-family:'Inter',-apple-system,sans-serif;padding:24px 0}}
.stage{{display:flex;flex-direction:column;align-items:center;gap:22px}}
.frame{{width:100%;max-width:1000px;padding:0 16px}}
.scaler{{position:relative;width:100%;padding-top:56.25%;background:#fff;border:1px solid #d8d8dc;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.page{{position:absolute;top:0;left:0;width:1280px;height:720px;transform-origin:top left;color:{INK}}}
</style></head><body><div class="stage">
{''.join(f'<div class="frame"><div class="scaler"><div class="page">{p}</div></div></div>' for p in P)}
</div><script>
function fit(){{document.querySelectorAll('.scaler').forEach(function(sc){{sc.querySelector('.page').style.transform='scale('+(sc.clientWidth/1280)+')';}});}}
window.addEventListener('resize',fit);fit();
</script></body></html>'''
open("/mnt/user-data/outputs/Jim_CV_preview.html","w",encoding="utf-8").write(html)
print("pages",len(P),"bytes",len(html))
