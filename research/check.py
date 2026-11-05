import re
import pathlib

h = pathlib.Path("report/index.html").read_text(encoding="utf-8")
for t in ["b", "code", "em", "a", "blockquote", "strong", "span", "p", "h2", "h3", "h4", "nav", "header"]:
    o = len(re.findall(r"<%s[\s>]" % t, h))
    c = h.count("</%s>" % t)
    status = "OK" if o == c else "MISMATCH"
    print(f"{t:12s} {o:5d} {c:5d} {status}")

hrefs = re.findall(r'href="([^"]+)"', h)
bad = [x for x in hrefs if not (x.startswith("http") or x.startswith("#"))]
print("hrefs:", len(hrefs), "suspicious:", bad[:10])
ext = [x for x in hrefs if x.startswith("http")]
print("external:", len(ext), "unique:", len(set(ext)))
print("http only:", [x for x in ext if x.startswith("http://")][:5])
print("doubled space:", len(re.findall(r"  +", re.sub(r"<[^>]+>", " ", h))))
print("empty tags:", len(re.findall(r"<(b|em|code)></\1>", h)))
