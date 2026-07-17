#!/usr/bin/env python3
"""Fixup: the Webflow pages wrap the CTA + footer in a shared <div class="cta-footer">.
Move that whole block into Footer.astro and strip the dangling CTA fragment from pages."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted((ROOT / "src" / "pages").rglob("*.astro"))
FOOTER = ROOT / "src" / "components" / "Footer.astro"

MARK = '<div class="cta-footer">'


def fragment(text: str):
    i = text.find(MARK)
    if i == -1:
        return None, None
    j = text.rindex("</BaseLayout>")
    return text[i:j].rstrip(), (i, j)


index = (ROOT / "src" / "pages" / "index.astro").read_text()
cta_block, _ = fragment(index)
assert cta_block, "cta-footer not found in index.astro"

norm = lambda s: re.sub(r"\s+", " ", s).strip()
canon = norm(cta_block)

for page in PAGES:
    text = page.read_text()
    frag, span = fragment(text)
    if frag is None:
        print(f"NOTE: no cta-footer in {page.name}")
        continue
    if norm(frag) != canon:
        print(f"WARN: cta-footer differs in {page.name} ({len(frag)} vs {len(cta_block)} chars) — keeping page copy is NOT possible, please inspect")
    i, j = span
    page.write_text(text[:i].rstrip() + "\n" + text[j:])
    print("stripped", page.relative_to(ROOT))

# Rebuild Footer.astro: cta-footer wrapper + CTA section + footer section + closing div
footer_html = FOOTER.read_text()
footer_section = footer_html[footer_html.index("<section"):].rstrip()
new_footer = (
    "{/* Shared CTA + footer (Webflow `cta-footer` block) — extracted from the Webflow export. */}\n"
    + cta_block + "\n"
    + footer_section + "\n"
    + "    </div>\n"
)
FOOTER.write_text(new_footer)
print("rebuilt", FOOTER.relative_to(ROOT))
