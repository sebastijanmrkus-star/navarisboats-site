"""Switch the Croatian Wix texts from Futura to Avenir Light where Futura can't draw Croatian letters.

Usage (from the repo root): python3 scripts/apply_hr_font.py

Wix's Futura (futura-lt-w01-book) has no glyphs for ć, č, đ, Ć and Č, so browsers draw
those letters in a fallback font. Avenir Light (avenir-lt-w01_35-light1475496) is already
loaded on the site, covers every Croatian letter, and at the same pixel size has the same
x-height as Futura (measured on the live site: 9px at 19px, line width within 0.4%).

Rule:
- paragraphs and lists (running text, boat specs, prices): Avenir Light
- headings: stay in Futura unless they contain a letter Futura lacks
- Privacy Policy (j0r08) and Accessibility Statement (gwvg1): Avenir Light throughout,
  because several of their headings need it

Rewrites translations/hr-wix.txt in place. Running it twice changes nothing.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PATH = os.path.join(ROOT, "translations/hr-wix.txt")
RICH = "compFeatures-wRichText-data-styledText-text"
FONT = "avenir-lt-w01_35-light1475496,sans-serif"
SPAN = '<span style="font-family:%s;">' % FONT
MISSING_IN_FUTURA = set("ćčđĆČ")

# which Wix page each text component sits on (legal pages get Avenir throughout)
LEGAL_PREFIXES = ("comp-m9fftkn", "comp-m9fftko", "comp-m9fftkp",            # privacy policy
                  "comp-m9fftkv", "comp-m9fftkw", "comp-m9fftkx", "comp-m9fftky", "comp-m9fftkz")  # accessibility

BLOCK = re.compile(r"(<(p|h[1-6])\b[^>]*>)(.*?)(</\2>)", re.S)


def needs_avenir(entity, html):
    text = re.sub(r"<[^>]+>", "", html)
    is_heading = not re.search(r"<(p|ul|ol)\b", html)
    return entity.startswith(LEGAL_PREFIXES) or not is_heading or bool(MISSING_IN_FUTURA & set(text))


def wrap(html):
    def repl(m):
        open_tag, _, inner, close_tag = m.groups()
        if FONT in inner:
            return m.group(0)
        return open_tag + SPAN + inner + "</span>" + close_tag
    return BLOCK.sub(repl, html)


def main():
    src = open(PATH, encoding="utf-8").read()
    parts = re.split(r"(?m)^(=== \S+ \S+\s*)$", src)
    out, changed = [parts[0]], 0
    for header, body in zip(parts[1::2], parts[2::2]):
        entity, field = header.split()[1:3]
        if field == RICH and needs_avenir(entity, body):
            new = wrap(body)
            changed += new != body
            body = new
        out += [header, body]
    with open(PATH, "w", encoding="utf-8") as fh:
        fh.write("".join(out))
    print("texts switched to Avenir Light:", changed)


if __name__ == "__main__":
    main()
