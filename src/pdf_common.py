"""Shared layout for the PDFs (16:9 pages, grey-beige background, white cards, tags) and printing with headless Edge."""
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from pypdf import PdfReader, PdfWriter

DISCLAIMER = "Independent case study based on public data · not affiliated with or endorsed by HeroSoftware GmbH or Shopify"

CSS = """
@page { size: 1600px 900px; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Segoe UI', Arial, sans-serif; color: #0B0B0B; background: #F4F4F2; }
.page { width: 1600px; height: 900px; padding: 30px 44px 22px; display: flex; flex-direction: column; page-break-after: always; overflow: hidden; background: #F4F4F2; }
header { display: flex; justify-content: space-between; align-items: flex-start; gap: 30px; }
h1 { font-size: 27px; margin: 0 0 6px; font-weight: 700; line-height: 1.15; max-width: 1320px; }
.sub { margin: 0; color: #52514E; font-size: 15px; max-width: 1320px; }
.tag { font-size: 12px; font-weight: 700; letter-spacing: .08em; padding: 5px 10px; border-radius: 4px; white-space: nowrap; color: #52514E; }
.tag-public { background: #E3EEFB; color: #1C5CAB; } .tag-simulated { background: #FBE9E0; color: #9A3B12; }
.tag-mixed { background: #EEEAF7; color: #5A3F9A; } .tag-overview { color: #52514E; border: 1px solid #E1E0D9; }
main { flex: 1; display: flex; flex-direction: column; gap: 12px; margin-top: 14px; min-height: 0; }
footer { display: flex; justify-content: space-between; gap: 20px; font-size: 11px; color: #898781; margin-top: 10px; }
.card { background: #FCFCFB; border: 1px solid #E1E0D9; border-radius: 8px; padding: 12px 16px; min-height: 0; overflow: hidden; }
.card h2 { font-size: 16px; margin: 0 0 6px; } .card h3 { font-size: 14px; margin: 0 0 4px; }
.card p, .card li { font-size: 13.5px; line-height: 1.4; margin: 3px 0; color: #2B2A27; }
.card ul, .card ol { padding-left: 18px; margin: 4px 0; }
.row { display: grid; gap: 12px; flex: 1; min-height: 0; }
.c2 { grid-template-columns: 1fr 1fr; } .c3 { grid-template-columns: 1fr 1fr 1fr; } .c4 { grid-template-columns: repeat(4, 1fr); }
.c21 { grid-template-columns: 2fr 1fr; } .c12 { grid-template-columns: 1fr 2fr; } .c32 { grid-template-columns: 1.5fr 1fr; }
.auto { flex: 0 0 auto !important; } .f2 { flex: 2 !important; } .f13 { flex: 1.3 !important; }
.stack { display: flex; flex-direction: column; gap: 12px; min-height: 0; } .stack > .card { flex: 1; }
figure { margin: 0; height: 100%; display: flex; flex-direction: column; }
figure img { width: 100%; flex: 1; min-height: 0; object-fit: contain; }
figcaption { font-size: 11.5px; color: #52514E; margin-top: 3px; }
.tile .label { font-size: 12px; font-weight: 700; color: #52514E; letter-spacing: .04em; }
.tile .big { font-size: 40px; font-weight: 700; margin: 2px 0; color: #0B0B0B; }
.tile p { font-size: 13px; color: #52514E; }
.qs li { font-size: 14.5px !important; margin: 5px 0; } .qs b { color: #2A78D6; margin-right: 6px; }
.k { color: #52514E; font-size: 12px; letter-spacing: .05em; margin-right: 4px; font-weight: 700; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th { text-align: left; color: #52514E; font-weight: 600; border-bottom: 1px solid #E1E0D9; padding: 4px 6px; }
td { border-bottom: 1px solid #EFEEE9; padding: 4px 6px; vertical-align: top; }
td.drop { color: #B42F2F; font-weight: 600; } td.ok { color: #1B7F55; font-weight: 600; } td.mut { color: #898781; }
.small, .small li, .small td, .small th { font-size: 12.3px !important; }
.note { font-size: 11.5px !important; color: #6B6A65 !important; }
pre { background: #F4F4F2; border-radius: 6px; padding: 8px 10px; font-size: 12px; margin: 4px 0 8px; white-space: pre-wrap; }
.flow { display: flex; gap: 8px; align-items: stretch; }
.flow div { flex: 1; background: #F4F4F2; border-radius: 6px; padding: 8px 10px; font-size: 12.5px; line-height: 1.35; }
.flow div b { display: block; font-size: 13.5px; color: #2A78D6; margin-bottom: 2px; }
.flow div.h b { color: #9A3B12; } .flow div.opt { border: 1px dashed #A3A19A; }
.fc { display: flex; flex-direction: column; } .fc figure { flex: 1; min-height: 0; } .fc figure img { min-height: 0; object-position: center top; }
td.nw { white-space: nowrap; }
blockquote { margin: 6px 0; padding: 6px 10px; border-left: 3px solid #2A78D6; background: #F4F4F2; font-size: 13px; }
"""


def page(n, title, subtitle, tag, body, sources, collected):
    tag_html = f'<div class="tag tag-{tag.lower().split()[0]}">{tag}</div>'
    return f"""
<section class="page">
  <header><div><h1>{title}</h1><p class="sub">{subtitle}</p></div>{tag_html}</header>
  <main>{body}</main>
  <footer><span>{sources} · {collected}</span><span>{DISCLAIMER}</span><span>{n}</span></footer>
</section>"""


def card(inner, cls=""):
    return f'<div class="card {cls}">{inner}</div>'


def img(src, cap=""):
    return f'<figure><img src="{src}"/>{f"<figcaption>{cap}</figcaption>" if cap else ""}</figure>'


def tile(label, value, text):
    return card(f'<div class="label">{label}</div><div class="big">{value}</div><p>{text}</p>', "tile")


def html_doc(title, pages):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head>
<body>{''.join(pages)}</body></html>"""


def find_browser() -> str:
    for c in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              shutil.which("msedge") or "", shutil.which("google-chrome") or "", shutil.which("chromium") or ""]:
        if c and Path(c).exists():
            return c
    raise FileNotFoundError("Edge or Chrome is needed to print the PDF")


def print_pdf(html: Path, pdf: Path, title: str) -> int:
    """Print an HTML file to PDF with headless Edge/Chrome, then rewrite it with neutral metadata."""
    tmp = pdf.with_name("_print.pdf")
    profile = tempfile.mkdtemp()            # own profile: an open Edge window would otherwise take the call
    subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={profile}",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=5000",
                    f"--print-to-pdf={tmp}", html.as_uri()], check=True, timeout=180)
    last = -1
    for _ in range(120):                    # Edge can return before its child process has written the file
        time.sleep(1)
        size = tmp.stat().st_size if tmp.exists() else -1
        if size > 0 and size == last:
            break
        last = size
    shutil.rmtree(profile, ignore_errors=True)
    reader, writer = PdfReader(str(tmp)), PdfWriter()
    for pg in reader.pages:
        writer.add_page(pg)
    writer.add_metadata({"/Title": title, "/Author": "", "/Creator": "", "/Producer": "", "/Subject": "", "/Keywords": ""})
    with open(pdf, "wb") as fh:
        writer.write(fh)
    tmp.unlink()
    return len(PdfReader(str(pdf)).pages)
