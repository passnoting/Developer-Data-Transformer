import io, os, re, sys
from pathlib import Path

base = Path(__file__).resolve().parent
order = [
    "00_head.html",
    "00_summary.html",
    "01_premises.html",
    "02_method.html",
    "03_why.html",
    "04_gaps.html",
    "05_intro.html",
    "05a_apidata.html",
    "05b_agentobs.html",
    "05c_csvexcel.html",
    "05d_codetest.html",
    "05e_smb.html",
    "06_decision.html",
    "07_mvp.html",
    "08_gtm.html",
    "09_risks.html",
    "99_appendix.html",
]

parts = []
missing = []
for name in order:
    p = base / "parts" / name
    if not p.exists():
        missing.append(name)
        continue
    parts.append(p.read_text(encoding="utf-8"))

if missing:
    print("MISSING:", missing)
    sys.exit(1)

html = "\n".join(parts)

# <caption> must be the first child of <table>; ours sit after </tbody>.
# Move each one out as a sibling div right after the table — same visual position,
# valid HTML everywhere.
before = len(re.findall(r"<caption>", html))
html, n = re.subn(
    r"<caption>(.*?)</caption>\s*</table>",
    '</table>\n<p class="cap">\\1</p>',
    html,
    flags=re.S,
)
print(f"captions moved out of tables: {n}/{before}")
assert '\\"' not in html, "escaped quotes leaked into the HTML"
assert 'class="cap"' in html, "caption conversion produced no styled paragraphs"

out = base.parent / "report" / "index.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")

# --- validations ---
print(f"written: {out}")
print(f"bytes: {out.stat().st_size:,}")
print(f"chars: {len(html):,}")

for tag in ["html", "head", "body", "main", "table", "tr", "td", "div"]:
    o = len(re.findall(rf"<{tag}[\s>]", html))
    c = len(re.findall(rf"</{tag}>", html))
    flag = "OK" if o == c else "MISMATCH"
    print(f"  <{tag}> open={o} close={c} {flag}")

ids = re.findall(r'id="(s[0-9\-]*)"', html)
print("anchors:", ids)
toc = re.findall(r'href="#(s[0-9\-]*)"', html)
print("toc targets missing:", [t for t in set(toc) if t not in set(ids)])
print("anchors without toc:", [i for i in ids if i not in set(toc)])

print("unknown left:", html.count("unknown"))
print("TODO left:", html.count("TODO"))
