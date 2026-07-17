#!/usr/bin/env python3
"""One-time conversion of the Webflow export (theme/ + src/pages/index.html)
into a proper Astro architecture: BaseLayout + Navbar/Footer components + pages.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
THEME = ROOT / "theme"
WF_SITE = "6a56f7723d4c8a4daf3c58b1"

SITE_NAME = "National AI Technologies"
DEFAULT_DESC = (
    "Oman’s flagship sovereign AI platform. World-class AI, 100% Omani-made, "
    "aligned with Oman Vision 2040. Enterprise-grade AI with complete data sovereignty."
)

# route -> (source file, page title, description override, noindex)
PAGES = {
    "index": (SRC / "pages" / "index.html", "National AI Technologies | Oman’s Sovereign AI Platform", None, False),
    "about-us": (THEME / "about-us.html", "About Us", "Learn about National AI Technologies, Oman’s sovereign AI company aligned with Oman Vision 2040.", False),
    "features": (THEME / "features.html", "Features", "Explore the capabilities of Oman’s sovereign AI platform: LLMs, generative AI, and predictive analytics.", False),
    "pricing": (THEME / "pricing.html", "Pricing", "Flexible plans for Oman’s sovereign AI platform, from startups to government enterprises.", False),
    "blog": (THEME / "blog.html", "Blog", "News and insights from National AI Technologies.", False),
    "career": (THEME / "career.html", "Careers", "Join National AI Technologies and help build Oman’s sovereign AI future.", False),
    "contact-us": (THEME / "contact-us.html", "Contact Us", "Get in touch with the National AI Technologies team.", False),
    "integration": (THEME / "integration.html", "Integrations", "Connect Oman’s sovereign AI platform with the tools you already use.", False),
    "team-members": (THEME / "team-members.html", "Team", "Meet the team behind National AI Technologies.", False),
    "privacy-policy": (THEME / "privacy-policy.html", "Privacy Policy", None, False),
    "checkout": (THEME / "checkout.html", "Checkout", None, True),
    "order-confirmation": (THEME / "order-confirmation.html", "Order Confirmation", None, True),
    "paypal-checkout": (THEME / "paypal-checkout.html", "PayPal Checkout", None, True),
    "detail_blog": (THEME / "detail_blog.html", "Blog Post", None, False),
    "detail_career": (THEME / "detail_career.html", "Career Details", None, False),
    "detail_category": (THEME / "detail_category.html", "Category", None, False),
    "detail_integration": (THEME / "detail_integration.html", "Integration Details", None, False),
    "detail_product": (THEME / "detail_product.html", "Product Details", None, False),
    "401": (THEME / "401.html", "Restricted Access", None, True),
    "404": (THEME / "404.html", "Page Not Found", None, True),
    "authentication/sign-in": (THEME / "authentication" / "sign-in.html", "Sign In", None, False),
    "authentication/sign-up": (THEME / "authentication" / "sign-up.html", "Sign Up", None, False),
    "authentication/forgot-password": (THEME / "authentication" / "forgot-password.html", "Forgot Password", None, False),
    "authentication/reset-password": (THEME / "authentication" / "reset-password.html", "Reset Password", None, False),
    "utility-pages/style-guide": (THEME / "utility-pages" / "style-guide.html", "Style Guide", None, True),
    "utility-pages/license": (THEME / "utility-pages" / "license.html", "License", None, True),
    "utility-pages/changelog": (THEME / "utility-pages" / "changelog.html", "Changelog", None, True),
}


def balanced_block(html: str, start: int, tag: str) -> int:
    """Return exclusive end index of the element whose opening tag starts at `start`."""
    depth = 0
    for m in re.finditer(rf"<(/?){tag}(?=[\s>])", html[start:], re.I):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return html.index(">", start + m.end()) + 1
    raise ValueError(f"unbalanced <{tag}> at {start}")


def rewrite_links(html: str) -> str:
    html = re.sub(r'href="(?:\.\./)?index\.html(#[^"]*)?"',
                  lambda m: f'href="/{m.group(1) or ""}"', html)
    html = re.sub(r'href="(?:\.\./)?((?:authentication|utility-pages)/[A-Za-z0-9_-]+)\.html(#[^"]*)?"',
                  r'href="/\1\2"', html)
    html = re.sub(r'href="(?:\.\./)?([A-Za-z0-9_-]+)\.html(#[^"]*)?"',
                  r'href="/\1\2"', html)
    # local asset folders -> absolute paths (skip CDN urls: preceded by '/')
    html = re.sub(r'(?<![\w/.-])(?:\.\./)?(images|documents|videos|fonts)/', r'/\1/', html)
    return html


def parse_attrs(attr_str: str, skip=("class",)) -> dict:
    attrs = {}
    for m in re.finditer(r'([\w:.-]+)(?:="([^"]*)")?', attr_str):
        name, val = m.group(1), m.group(2) or ""
        if name not in skip:
            attrs[name] = val
    return attrs


def extract_parts(html: str):
    """Return dict with wfPage, style, jsonld list, bodyAttrs, wrapperAttrs, hasNavbar, content."""
    wf_page = re.search(r'data-wf-page="([^"]+)"', html).group(1)

    head = html[: html.index("<body")]
    style_m = re.search(r"<style>(.*?)</style>", head, re.S)
    style = style_m.group(1).strip() if style_m else None
    jsonld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', head, re.S)

    body_m = re.search(r"<body([^>]*)>", html)
    body_attrs = parse_attrs(body_m.group(1), skip=())

    pw_m = re.search(r'<div([^>]*)class="page-wrapper"([^>]*)>', html)
    wrapper_attrs = parse_attrs(pw_m.group(1) + pw_m.group(2))
    pw_end = pw_m.end()

    banner_m = re.search(r'<div[^>]*role="banner"[^>]*>', html)
    has_navbar = banner_m is not None
    if has_navbar:
        nav_start = banner_m.start()
        nav_end = balanced_block(html, nav_start, "div")
        content_start = nav_end
    else:
        content_start = pw_end

    footer_m = re.search(r'<section[^>]*class="[^"]*\bfooter\b[^"]*"[^>]*>', html)
    if not footer_m:
        raise ValueError("footer not found")
    content = html[content_start:footer_m.start()].rstrip()
    content = rewrite_links(content)
    # normalize leading whitespace
    content = "\n".join(line for line in content.splitlines() if line.strip() or True).strip("\n")

    return {
        "wfPage": wf_page,
        "style": style,
        "jsonld": jsonld,
        "bodyAttrs": body_attrs,
        "wrapperAttrs": wrapper_attrs,
        "hasNavbar": has_navbar,
        "content": content,
        "navbar": html[nav_start:nav_end] if has_navbar else None,
        "footer": html[footer_m.start(): balanced_block(html, footer_m.start(), "section")],
    }


def strip_current(html: str) -> str:
    html = html.replace(' aria-current="page"', "")
    html = re.sub(r'\s+w--current(?=[" ])', "", html)
    return html


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def main():
    index_html = (SRC / "pages" / "index.html").read_text(encoding="utf-8")
    index_parts = extract_parts(index_html)

    # ---------- components ----------
    navbar = strip_current(rewrite_links(index_parts["navbar"]))
    footer = strip_current(rewrite_links(index_parts["footer"]))
    write(SRC / "components" / "Navbar.astro",
          "{/* Site navigation — extracted from the Webflow export. */}\n" + navbar + "\n")
    write(SRC / "components" / "Footer.astro",
          "{/* Site footer — extracted from the Webflow export. */}\n" + footer + "\n")

    # ---------- pages ----------
    for route, (src_file, title, desc, noindex) in PAGES.items():
        html = src_file.read_text(encoding="utf-8")
        p = extract_parts(html)

        depth = route.count("/")
        rel = "../" * (depth + 1)
        full_title = title if route == "index" else f"{title} | {SITE_NAME}"

        props = [f"  title={json.dumps(full_title)}"]
        if desc:
            props.append(f"  description={json.dumps(desc)}")
        props.append(f'  pageId="{p["wfPage"]}"')
        if not p["hasNavbar"]:
            props.append("  showNavbar={false}")
        if noindex:
            props.append("  noindex")
        if p["bodyAttrs"]:
            props.append(f"  bodyAttrs={{{json.dumps(p['bodyAttrs'])}}}")
        if p["wrapperAttrs"]:
            props.append(f"  wrapperAttrs={{{json.dumps(p['wrapperAttrs'])}}}")

        head_bits = ""
        if p["style"] or p["jsonld"]:
            bits = []
            if p["style"]:
                bits.append(f"    <style is:inline>{p['style']}</style>")
            for ld in p["jsonld"]:
                bits.append(f'    <script is:inline type="application/ld+json">{ld.strip()}</script>')
            head_bits = '  <Fragment slot="head">\n' + "\n".join(bits) + "\n  </Fragment>\n"

        page = (
            "---\n"
            f"import BaseLayout from '{rel}layouts/BaseLayout.astro';\n"
            "---\n\n"
            f"<BaseLayout\n" + "\n".join(props) + "\n>\n"
            + head_bits
            + p["content"] + "\n"
            "</BaseLayout>\n"
        )
        write(SRC / "pages" / f"{route}.astro", page)


if __name__ == "__main__":
    main()
