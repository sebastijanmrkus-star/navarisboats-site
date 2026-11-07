"""Build the standalone English/Croatian site in site/.

Usage (from the repo root): python3 scripts/build_site.py

English text is read from the Wix snapshots in pages/html/, Croatian text from
translations/hr-wix.txt (the same file that was loaded into Wix Multilingual),
so both versions of the site stay in step with the Wix site.
"""
import html
import os
import re
import sys
from html.parser import HTMLParser

from PIL import Image, ImageChops

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
YEAR = 2026
PHONE_DISPLAY = "+385 99 8853 578"
PHONE_TEL = "+385998853578"
EMAIL = "info@navarisboats.com"

# ---------------------------------------------------------------- sources
SNAPSHOTS = {
    "home": "pages/html/home.html",
    "contact": "pages/html/contact.html",
    "privacy": "pages/html/english-privacy-policy.html",
    "accessibility": "pages/html/accessibility-statement.html",
}

VOID = {"br", "img", "hr", "input", "meta", "link", "wbr", "source"}


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def element_inner(raw, comp_id):
    """Inner HTML of the rendered element with this Wix component id."""
    m = re.search(r'<(div|a|section)\b[^>]*\bid="%s"[^>]*>' % re.escape(comp_id), raw)
    if not m:
        raise KeyError(comp_id)
    pos, depth = m.end(), 1
    for t in re.finditer(r"<(/?)([a-zA-Z0-9]+)\b[^>]*?(/?)>", raw[pos:]):
        closing, name, selfclose = t.group(1), t.group(2).lower(), t.group(3)
        if name in VOID or selfclose:
            continue
        depth += -1 if closing else 1
        if depth == 0:
            return raw[pos:pos + t.start()]
    raise ValueError("unbalanced " + comp_id)


def load_hr():
    hr, cur = {}, None
    for line in read("translations/hr-wix.txt").split("\n"):
        m = re.match(r"^=== (\S+) (\S+)\s*$", line)
        if m:
            cur = (m.group(1), m.group(2))
            hr[cur] = []
        elif cur:
            hr[cur].append(line)
    return {k: "\n".join(v).strip().replace("{ZWSP}", "​") for k, v in hr.items()}


HR = load_hr()
RICH = "compFeatures-wRichText-data-styledText-text"
_snap_cache = {}


def en_rich(page, comp_id):
    if page not in _snap_cache:
        _snap_cache[page] = read(SNAPSHOTS[page])
    return element_inner(_snap_cache[page], comp_id)


def hr_val(entity, field=RICH):
    return HR[(entity, field)]


# ---------------------------------------------------------------- cleaning
ACCENT_RE = re.compile(r"color:\s*(#e33b08|rgb\(\s*227,\s*59,\s*8\s*\))", re.I)


class Cleaner(HTMLParser):
    """Turns Wix rich text into plain semantic HTML.

    Keeps headings/p/ul/li/br/a, turns the brand-orange spans into
    <span class="accent"> and italic spans into <em>, drops every class and style.
    """

    KEEP = {"p", "ul", "ol", "li", "br", "a", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em"}

    def __init__(self, link_fallback=None, inline=False):
        super().__init__(convert_charrefs=True)
        self.out, self.stack = [], []
        self.link_fallback = link_fallback
        self.inline = inline

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "span":
            style = a.get("style", "") or ""
            if ACCENT_RE.search(style):
                self.out.append('<span class="accent">'); self.stack.append("</span>")
            elif "italic" in style:
                self.out.append("<em>"); self.stack.append("</em>")
            else:
                self.stack.append("")
            return
        if tag not in self.KEEP:
            return
        if self.inline and tag not in {"br", "a", "strong", "em"}:
            if tag in {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6"} and self.out:
                self.out.append("<br>")
            return
        if tag == "br":
            self.out.append("<br>")
            return
        if tag == "a":
            href = a.get("href") or self.link_fallback
            if href:
                ext = href.startswith("http")
                self.out.append('<a href="%s"%s>' % (html.escape(href), ' target="_blank" rel="noopener"' if ext else ""))
            else:
                self.out.append("<a>")
            return
        self.out.append("<%s>" % tag)

    def handle_endtag(self, tag):
        if tag == "span":
            if self.stack:
                self.out.append(self.stack.pop())
            return
        if tag not in self.KEEP or tag == "br":
            return
        if self.inline and tag not in {"a", "strong", "em"}:
            return
        self.out.append("</%s>" % tag)

    def handle_data(self, data):
        self.out.append(html.escape(data.replace("​", ""), quote=False))

    def result(self):
        s = "".join(self.out).replace("\xa0", " ")
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"(<br>\s*)+", "<br>", s)                       # Wix doubles <br> for spacing
        s = re.sub(r"<(p|li)>\s*(<br>\s*)?</\1>", "", s)           # empty spacer lines
        s = re.sub(r"<li>\s*<p>(.*?)</p>\s*</li>", r"<li>\1</li>", s)
        s = re.sub(r"\s*(</?(?:p|ul|ol|li|h\d)>)\s*", r"\1", s)
        s = re.sub(r"^(<br>)+|(<br>)+$", "", s.strip())
        s = re.sub(r"<br>(</(?:p|li|h\d)>)", r"\1", s)
        s = re.sub(r"\s+(</(?:p|li|h\d|span|em)>)", r"\1", s)
        # keep numbers on the same line as their unit ("15 DANA", "25 %", "300 L", "4,8 m")
        units = r"%|L|MM|mm|m|KS|HP|DANA|DAYS|DANI|GODINE|YEAR|EUR"
        s = re.sub(r"(\d) (?=(?:%s)(?![\w]))" % units, "\\1\u00a0", s)
        return s


def first_href(fragment):
    m = re.search(r'<a\b[^>]*href="([^"]+)"', fragment)
    return html.unescape(m.group(1)) if m else None


def clean(fragment, inline=False, link_fallback=None):
    c = Cleaner(link_fallback=link_fallback, inline=inline)
    c.feed(fragment)
    c.close()
    return c.result()


def lead_in(block):
    """Bold the 'Label:' at the start of each list item / paragraph."""
    return re.sub(r"<(li|p)>([^<:]{3,70}):", r"<\1><strong>\2:</strong>", block)


def linkify(s):
    s = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", s)  # Wix already auto-links some of these; start from plain text
    s = s.replace(PHONE_DISPLAY, '<a href="tel:%s">%s</a>' % (PHONE_TEL, PHONE_DISPLAY))
    return s.replace(EMAIL, '<a href="mailto:%s">%s</a>' % (EMAIL, EMAIL))


def T(page, comp_id, lang, inline=False):
    """Cleaned text of one Wix text component in the requested language."""
    en = en_rich(page, comp_id)
    if lang == "en":
        return clean(en, inline=inline)
    return clean(hr_val(comp_id), inline=inline, link_fallback=first_href(en))


# ---------------------------------------------------------------- strings
PAGES = {  # page key -> (EN path, HR path, Wix page id)
    "home": ("index.html", "hr/index.html", "sbj2r"),
    "contact": ("contact.html", "hr/kontakt.html", "iyv84"),
    "privacy": ("privacy-policy.html", "hr/pravila-privatnosti.html", "j0r08"),
    "accessibility": ("accessibility-statement.html", "hr/izjava-o-pristupacnosti.html", "gwvg1"),
}
EN_TITLES = {"home": "Home", "contact": "Contact", "privacy": "Privacy Policy", "accessibility": "Accessibility Statement"}

UI = {
    "en": {
        "site": "NAVARIS BOATS. UNBEATABLE VALUE",
        "skip": "Skip to content",
        "lang": "Language",
        "phone": "Phone",
        "mail": "Mail",
        "email_label": "Email",
        "more": "View More",
        "models": "Our boats",
        "rights": "All rights reserved.",
        "desc_home": "NAVARIS BOATS builds aluminium RIBs and boats from 4.8 m to 10.5 m, sea-tested off Mljet and Lastovo and based in Ploče, Croatia. Boat + engine packages with a 3-year warranty and 15-day delivery.",
        "desc_contact": "Contact NAVARIS BOATS by phone or email, or visit our showroom. Monday to Friday, 9 AM to 6 PM.",
        "alt_hero": "NAVARIS RIB at speed on the Adriatic, with a Croatian island behind",
        "alt_craft": "NAVARIS aluminium RIB under way",
        "alt_adriatic": "Island coastline on the open Adriatic",
        "alt_charter": "Guests aboard a NAVARIS boat on the Adriatic",
        "alt_logo": "NAVARIS BOATS logo",
        "alt": {"7.6": "NAVARIS 7.6M RIB", "7.0": "NAVARIS 7.0M RIB with a Mercury 150 HP engine",
                "4.8": "NAVARIS 4.8M RIB with a Mercury 60 HP engine", "8.0": "NAVARIS 8.0M boat with a Mercury Verado 300 HP engine"},
    },
    "hr": {
        "site": "NAVARIS BOATS. NENADMAŠNA VRIJEDNOST",
        "skip": "Preskoči na sadržaj",
        "lang": "Jezik",
        "phone": hr_val("comp-mvqxlrml", "compFeatures-stylableButton-data-label"),
        "mail": hr_val("comp-mvqxmn7c", "compFeatures-stylableButton-data-label"),
        "email_label": "E-pošta",
        "more": hr_val("comp-mvqv5qrc", "compFeatures-stylableButton-data-label"),
        "models": "Naša plovila",
        "rights": "Sva prava pridržana.",
        "desc_home": "NAVARIS BOATS izrađuje aluminijske gumenjake i plovila duljine od 4,8 do 10,5 m, ispitana na moru oko Mljeta i Lastova, sa sjedištem u Pločama. Paketi plovilo + motor s jamstvom od 3 godine i isporukom za 15 dana.",
        "desc_contact": "Obratite se tvrtki NAVARIS BOATS telefonom ili e-poštom ili posjetite naš izložbeni salon. Od ponedjeljka do petka, 9:00 – 18:00.",
        "alt_hero": "Gumenjak NAVARIS u punoj brzini na Jadranu, s hrvatskim otokom u pozadini",
        "alt_craft": "Aluminijski gumenjak NAVARIS u plovidbi",
        "alt_adriatic": "Otočna obala na otvorenom Jadranu",
        "alt_charter": "Gosti na plovilu NAVARIS na Jadranu",
        "alt_logo": hr_val("comp-mvqwav3y", "compFeatures-wPhoto-data-alt"),
        "alt": {"7.6": hr_val("comp-mvquek26", "compFeatures-wPhoto-data-alt"), "7.0": hr_val("comp-mvqu4uid", "compFeatures-wPhoto-data-alt"),
                "4.8": hr_val("comp-mvqwyi7j", "compFeatures-wPhoto-data-alt"), "8.0": hr_val("comp-mvqx44vv", "compFeatures-wPhoto-data-alt")},
    },
}


def page_title(key, lang):
    return EN_TITLES[key] if lang == "en" else hr_val(PAGES[key][2], "title")


# ---------------------------------------------------------------- icons & flags
ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>'
ICON_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>'

FLAG_UK = ('<svg class="flag" viewBox="0 0 60 30" aria-hidden="true" focusable="false">'
           '<clipPath id="uk-a"><path d="M0 0v30h60V0z"/></clipPath>'
           '<clipPath id="uk-b"><path d="M30 15h30v15zv15H0zH0V0zV0h30z"/></clipPath>'
           '<g clip-path="url(#uk-a)"><path d="M0 0v30h60V0z" fill="#012169"/>'
           '<path d="M0 0l60 30m0-30L0 30" stroke="#fff" stroke-width="6"/>'
           '<path d="M0 0l60 30m0-30L0 30" clip-path="url(#uk-b)" stroke="#C8102E" stroke-width="4"/>'
           '<path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/>'
           '<path d="M30 0v30M0 15h60" stroke="#C8102E" stroke-width="6"/></g></svg>')


def _flag_hr():
    sq = []
    for r in range(5):
        for c in range(5):
            if (r + c) % 2 == 0:
                sq.append('<rect x="%g" y="%g" width="2" height="2"/>' % (25 + 2 * c, 9 + 2 * r))
    return ('<svg class="flag" viewBox="0 0 60 30" aria-hidden="true" focusable="false">'
            '<path fill="#FF0000" d="M0 0h60v10H0z"/><path fill="#fff" d="M0 10h60v10H0z"/><path fill="#171796" d="M0 20h60v10H0z"/>'
            '<path d="M25 8.6h10v10.6a5 5 0 0 1-10 0z" fill="#fff" stroke="#FF0000" stroke-width=".5"/>'
            '<g fill="#FF0000">' + "".join(sq) + '</g>'
            '<path d="M25 8.6v-2.2l2-1 2 1 1-1.2 1 1.2 2-1 2 1v2.2z" fill="#0093DD" stroke="#171796" stroke-width=".4"/></svg>')


FLAG_HR = _flag_hr()


# ---------------------------------------------------------------- layout
def rel(from_path, to_path):
    return os.path.relpath(to_path, os.path.dirname(from_path) or ".").replace(os.sep, "/")


def lang_picker(key, lang, here):
    out = ['<nav class="lang" aria-label="%s">' % UI[lang]["lang"]]
    for i, (code, label, name, flag) in enumerate([("en", "EN", "English", FLAG_UK), ("hr", "HR", "Hrvatski", FLAG_HR)]):
        target = PAGES[key][0 if code == "en" else 1]
        cur = ' aria-current="true"' if code == lang else ""
        if i:
            out.append('<span class="sep" aria-hidden="true">|</span>')
        out.append('<a href="%s" hreflang="%s" lang="%s" title="%s"%s>%s<span>%s</span></a>'
                   % (rel(here, target), code, code, name, cur, flag, label))
    out.append("</nav>")
    return "".join(out)


def layout(key, lang, body, description=None):
    here = PAGES[key][0 if lang == "en" else 1]
    a = lambda p: rel(here, p)
    ui = UI[lang]
    nav = "".join('<a href="%s"%s>%s</a>' % (a(PAGES[k][0 if lang == "en" else 1]), ' aria-current="page"' if k == key else "", page_title(k, lang))
                  for k in ("home", "contact"))
    foot_nav = "".join('<a href="%s">%s</a>' % (a(PAGES[k][0 if lang == "en" else 1]), page_title(k, lang))
                       for k in ("home", "contact", "privacy", "accessibility"))
    other = "hr" if lang == "en" else "en"
    meta = '<meta name="description" content="%s">' % html.escape(description) if description else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page_title(key, lang))} | {html.escape(ui['site'])}</title>
{meta}
<link rel="alternate" hreflang="{other}" href="{a(PAGES[key][0 if other == 'en' else 1])}">
<link rel="icon" href="{a('assets/img/favicon.png')}" type="image/png">
<link rel="preload" href="{a('assets/fonts/jost-latin-400-normal.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{a('assets/style.css')}">
</head>
<body>
<a class="skip" href="#main">{ui['skip']}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{a(PAGES['home'][0 if lang == 'en' else 1])}"><img src="{a('assets/img/logo.png')}" alt="{html.escape(ui['alt_logo'])}" width="240" height="96"></a>
    <nav class="main-nav" aria-label="{'Main' if lang == 'en' else 'Glavni izbornik'}">{nav}</nav>
    <div class="quick">
      <a href="tel:{PHONE_TEL}" aria-label="{ui['phone']}: {PHONE_DISPLAY}" title="{ui['phone']}">{ICON_PHONE}</a>
      <a href="mailto:{EMAIL}" aria-label="{ui['mail']}: {EMAIL}" title="{ui['mail']}">{ICON_MAIL}</a>
    </div>
    {lang_picker(key, lang, here)}
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <img class="logo" src="{a('assets/img/logo.png')}" alt="" width="240" height="96">
      <p class="reach"><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a><a href="mailto:{EMAIL}">{EMAIL}</a></p>
    </div>
    <nav aria-label="{'Footer' if lang == 'en' else 'Podnožje'}">{foot_nav}</nav>
    <p class="copy">© {YEAR}. NAVARIS BOATS. {ui['rights']}</p>
  </div>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------- pages
MODELS = [  # key, name, specs, price, image, listing
    ("7.6", "comp-m9fftlob", "comp-m9fftloh1", "comp-mvquwwjd", "navaris-7-6m.jpg",
     "https://www.njuskalo.hr/gumenjaci/navaris-al760-honda-250hp-el-vinc-fridge-garmin-oglas-47100059"),
    ("7.0", "comp-m9fftlos", "comp-mvqv6wh9", "comp-mvqvd491", "navaris-7-0m.jpg",
     "https://www.njuskalo.hr/gumenjaci/navaris-700-mercury-150hp-fridge-el-vinc-hardtop-simrad-tus-oglas-50718388"),
    ("4.8", "comp-mvqwrq34", "comp-mvqwtfc3", "comp-mvqwvkbr", "navaris-4-8m.jpg",
     "https://www.njuskalo.hr/gumenjaci/navaris-480-mercury-60hp-fridge-ttop-simrad-muzika-oglas-50718277"),
    ("8.0", "comp-mvqwsjy4", "comp-mvqx1565", "comp-mvqx4x8z", "navaris-8-0m.jpg",
     "https://www.njuskalo.hr/motorni-brodovi/navaris-26-gt-verado-300hp-klima-frizider-el-vinc-full-oprema-oglas-49867866"),
]


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def home(lang):
    ui = UI[lang]
    here = PAGES["home"][0 if lang == "en" else 1]
    img = lambda n: rel(here, "assets/img/" + n)
    t = lambda cid, inline=False: T("home", cid, lang, inline)
    cards = []
    for key, name, specs, price, image, listing in MODELS:
        cards.append(f"""<article class="card">
  <img src="{img(image)}" alt="{html.escape(ui['alt'][key])}" loading="lazy" width="1280" height="720">
  <div class="card__body">
    <h3>{strip_tags(t(name, True))}</h3>
    <div class="specs">{t(specs)}</div>
    <div class="price">{linkify(t(price))}</div>
    <a class="btn" href="{listing}" target="_blank" rel="noopener">{ui['more']}</a>
  </div>
</article>""")
    contact_line = (f'<p class="contact-line"><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>'
                    f'<a href="mailto:{EMAIL}">{EMAIL}</a></p>')
    return f"""<section class="hero" style="background-image:url('{img('hero.jpg')}')" aria-label="{html.escape(ui['alt_hero'])}">
  <div class="wrap"><h1>{t('comp-mvqw9iwq1', True)}</h1></div>
</section>

<section id="models" aria-label="{ui['models']}">
  <div class="wrap"><div class="models">
{chr(10).join(cards)}
  </div></div>
</section>

<section class="section--cream">
  <div class="wrap">
    <h2 class="display center">{t('comp-mvzglzec', True)}</h2>
    <div class="lede center">{t('comp-mvzglzef')}</div>
    <div class="cols">
      <div class="panel"><h3>{t('comp-mvzglzek', True)}</h3>{lead_in(t('comp-mvzglzem'))}</div>
      <div class="panel"><h3>{t('comp-mvzglzer', True)}</h3>{lead_in(t('comp-mvzh5utf'))}</div>
    </div>
    {contact_line}
  </div>
</section>

<section>
  <div class="wrap">
    <div class="feature">
      <div class="feature__media"><img src="{img('craftsmanship.jpg')}" alt="{html.escape(ui['alt_craft'])}" loading="lazy" width="1024" height="768"></div>
      <div>
        <h2 class="display">{t('comp-mvqx9ixr', True)}</h2>
        {t('comp-mvqx796r')}
      </div>
    </div>
    <div class="feature feature--flip">
      <div class="feature__media"><img src="{img('adriatic.jpg')}" alt="{html.escape(ui['alt_adriatic'])}" loading="lazy" width="1024" height="768"></div>
      <div>
        <h2 class="display">{t('comp-mvr7gpdn', True)}</h2>
        {t('comp-mvr7gzsz')}
      </div>
    </div>
    <div class="feature">
      <div class="feature__media"><img src="{img('charter.jpg')}" alt="{html.escape(ui['alt_charter'])}" loading="lazy" width="1024" height="768"></div>
      <div>
        <h2 class="display">{t('comp-mvr7sovk', True)}</h2>
        {lead_in(t('comp-mvr7svfk'))}
      </div>
    </div>
  </div>
</section>"""


def contact(lang):
    ui = UI[lang]
    t = lambda cid, inline=False: T("contact", cid, lang, inline)
    return f"""<section class="page-head">
  <div class="wrap contact-grid">
    <div class="prose">
      <h1>{t('comp-m9ffu0u2', True)}</h1>
      <h2>{t('comp-m9ffu0ui', True)}</h2>
      {t('comp-m9ffu0ve')}
      <div class="contact-cards">
        <a href="tel:{PHONE_TEL}">{ICON_PHONE}<span><small>{ui['phone']}</small>{PHONE_DISPLAY}</span></a>
        <a href="mailto:{EMAIL}">{ICON_MAIL}<span><small>{ui['email_label']}</small>{EMAIL}</span></a>
      </div>
    </div>
    <div class="hours">
      <h2>{t('comp-m9ffu0xj', True)}</h2>
      <p class="day">{t('comp-m9ffu0y3', True)}</p>
      {t('comp-m9ffu0yn')}
    </div>
  </div>
</section>
<section></section>"""


def legal(key, lang, ids, note=None):
    t = lambda cid, inline=False: T(key, cid, lang, inline)
    parts = []
    if note:
        parts.append('<div class="note">%s</div>' % t(note))
    for cid in ids:
        parts.append(t(cid))
    return '<section class="page-head"><div class="wrap prose">%s</div></section><section></section>' % "\n".join(parts)


PRIVACY_IDS = ["comp-m9fftknz", "comp-m9fftkoj", "comp-m9fftkoq", "comp-m9fftkoz", "comp-m9fftkp2", "comp-m9fftkp5", "comp-m9fftkpc"]
ACCESS_IDS = ["comp-m9fftkvt", "comp-m9fftkvw1", "comp-m9fftkwn", "comp-m9fftkww1", "comp-m9fftkxg", "comp-m9fftkxp", "comp-m9fftkxu",
              "comp-m9fftkya", "comp-m9fftkyj", "comp-m9fftkyw", "comp-m9fftkz8", "comp-m9fftkzm", "comp-m9fftkzx"]


# ---------------------------------------------------------------- images
IMAGES = {  # output name -> (source in media/, max width)
    "hero.jpg": ("Real photo of luxury speed RIB on adriatic sea with croatian island in background_edited.jpg", 1600),
    "navaris-7-6m.jpg": ("navaris-al760-honda-250hp-el-vinc-fridge-garmin-slika-289581581_edited.jpg", 1280),
    "navaris-7-0m.jpg": ("navaris-700-mercury-150hp-fridge-el-vinc-hardtop-simrad-tus-slika-282822773.jpg", 1280),
    "navaris-4-8m.jpg": ("navaris-480-mercury-60hp-fridge-ttop-simrad-muzika-slika-282823384_edited.jpg", 1280),
    "navaris-8-0m.jpg": ("navaris-26-gt-verado-300hp-klima-frizider-el-vinc-full-oprema-slika-282822468_edited.jpg", 1280),
    "craftsmanship.jpg": ("Real photo of luxury aluminum rib.jpg", 1200),
    "adriatic.jpg": ("real image of Adriatic sea background with some island.jpg", 1200),
    "charter.jpg": ("Google Ads AI generated images/0fd7ac94-b1de-4b94-a4c1-12c9fa4b9099.jpg", 1200),
}


def trim_white(im, thresh=245):
    gray = im.convert("L").point(lambda p: 255 if p < thresh else 0)
    box = gray.getbbox()
    return im.crop(box) if box else im


def build_images():
    out = os.path.join(SITE, "assets/img")
    os.makedirs(out, exist_ok=True)
    for name, (src, maxw) in IMAGES.items():
        im = Image.open(os.path.join(ROOT, "media", src)).convert("RGB")
        if im.width > maxw:
            im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        im.save(os.path.join(out, name), "JPEG", quality=82, optimize=True, progressive=True)
    logo = trim_white(Image.open(os.path.join(ROOT, "media/NavarisBoats-Logo.png")).convert("RGBA"))
    logo = logo.resize((480, round(logo.height * 480 / logo.width)), Image.LANCZOS)
    # make the off-white background transparent so the logo also works on dark backgrounds
    keep = logo.convert("L").point(lambda p: 0 if p > 240 else 255)
    logo.putalpha(ImageChops.multiply(logo.getchannel("A"), keep))
    logo.save(os.path.join(out, "logo.png"), optimize=True)
    mark = trim_white(Image.open(os.path.join(ROOT, "media/NavarisBoats-Logo_edited.jpg")).convert("RGB"))
    side = max(mark.size)
    sq = Image.new("RGB", (side, side), (255, 255, 255))
    sq.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    sq.resize((64, 64), Image.LANCZOS).save(os.path.join(out, "favicon.png"), optimize=True)


# ---------------------------------------------------------------- main
def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote site/" + path)


def main():
    build_images()
    for lang in ("en", "hr"):
        i = 0 if lang == "en" else 1
        write(PAGES["home"][i], layout("home", lang, home(lang), UI[lang]["desc_home"]))
        write(PAGES["contact"][i], layout("contact", lang, contact(lang), UI[lang]["desc_contact"]))
        write(PAGES["privacy"][i], layout("privacy", lang, legal("privacy", lang, PRIVACY_IDS)))
        write(PAGES["accessibility"][i], layout("accessibility", lang, legal("accessibility", lang, ACCESS_IDS, note="comp-m9fftkv1")))


if __name__ == "__main__":
    sys.exit(main())
