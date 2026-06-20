#!/usr/bin/env python3
# SmartPN CV builder (rebuilt to spec, 2026-06-20)
# Design system = locked consistency master. Renderer = weasyprint (no browser needed).
from weasyprint import HTML
import os

OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

# ---- locked design tokens ----
INK      = "#1D1D1F"   # near-black primary
GREY     = "#6E6E73"   # secondary / labels
FAINT    = "#AEAEB2"   # page markers
ACCENT   = "#B5540D"   # the ONE orange-gold focal, one per page
CARD     = "#F5F5F7"   # light grey surface
HAIRLINE = "#D2D2D7"
PAGE_W, PAGE_H = "13.333in", "7.5in"   # 16:9 (1280x720 @96dpi)

BASE_CSS = f"""
@page {{ size: {PAGE_W} {PAGE_H}; margin: 0; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:100%; height:100%; background:#FFFFFF;
  font-family:'Inter',sans-serif; color:{INK};
  -weasy-font-feature-settings:'kern' 1; }}
.page {{ position:relative; width:1280px; height:720px; background:#FFFFFF; overflow:hidden; }}
.eyebrow {{ font:500 13px/1 'Inter Medium'; letter-spacing:2px; color:{GREY};
  text-transform:uppercase; }}
.focal {{ color:{ACCENT}; font-family:'Inter Medium'; font-weight:500; }}
.hair {{ height:1px; background:{HAIRLINE}; border:0; }}
.marker {{ position:absolute; font:400 12px 'Inter'; color:{FAINT}; letter-spacing:1px; }}
"""

def render(name, body_html, extra_css=""):
    html = f"<style>{BASE_CSS}{extra_css}</style>{body_html}"
    pdf = f"{OUT}/{name}.pdf"
    HTML(string=html).write_pdf(pdf)
    return pdf

# ---------------- P1 — D01 Quiet Cover ----------------
def p1_cover():
    css = """
    .cover{display:flex;height:720px;}
    .left{width:46%;display:flex;flex-direction:column;justify-content:center;
      padding:0 56px 0 96px;}
    .name{font:600 64px/1.0 'Inter SemiBold';letter-spacing:-1.5px;margin:18px 0 26px;}
    .sub{font:400 30px/1.32 'Inter';letter-spacing:-0.4px;}
    .left .hair{width:78%;margin:30px 0 18px;}
    .supp{font:400 17px/1.55 'Inter';color:#6E6E73;}
    .right{width:54%;padding:96px 96px 96px 40px;display:flex;}
    .panel{flex:1;background:#F5F5F7;border-radius:20px;position:relative;
      background-image:radial-gradient(#E2E2E6 1.4px, transparent 1.4px);
      background-size:26px 26px;background-position:18px 18px;}
    .panel .tag{position:absolute;left:24px;bottom:22px;font:500 13px 'Inter Medium';
      color:#9A9AA0;letter-spacing:.3px;}
    """
    body = """
    <div class="page"><div class="cover">
      <div class="left">
        <div class="eyebrow">Founder · SmartPN Atlas</div>
        <div class="name">Jim Kao</div>
        <div class="sub">Where data architecture and solutions meet —<br>
          <span class="focal">at the factory floor.</span></div>
        <hr class="hair">
        <div class="supp">Data Architect&nbsp;·&nbsp;Solutions&nbsp;·&nbsp;Standardization<br>
          I work only where the three intersect.</div>
      </div>
      <div class="right">
        <div class="panel"><div class="tag">Hero visual — designed in GPT&nbsp;·&nbsp;D01</div></div>
      </div>
    </div>
    <div class="marker" style="left:96px;bottom:40px;">01 / 15</div>
    </div>
    """
    return render("CV_P1_cover_D01", body, css)

if __name__ == "__main__":
    print(p1_cover())
