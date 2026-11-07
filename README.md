# navarisboats.com: site export

A backup of the Wix site **NAVARIS BOATS. UNBEATABLE VALUE** (https://www.navarisboats.com). First taken on 2026-11-05; last refreshed on 2026-11-07 from live site version 140.
It was pulled with the Wix connector (site data, languages, translations, SEO, Media Manager) and from the live published site (page snapshots).

## What's in here

| Path | Contents | Source |
|---|---|---|
| `wix-data/site.json` | Site ID, plan, editor type, installed apps, business info (name, email, phone, locale, currency, time zone) | Wix Site Properties API |
| `wix-data/seo.json` | The 4 static pages with their IDs, URLs, and SEO titles and descriptions in English and Croatian; redirects (none); URL mappings (none) | Wix SEO APIs, live site |
| `wix-data/media-manager.json` | Metadata for every file and folder in the Media Manager | Wix Media Manager API |
| `media/` | The **original** of all 21 Media Manager images (8.8 MB), in their Media Manager folders. `media/index.json` maps each file to its Wix file ID and URL | static.wixstatic.com |
| `pages/html/` | Server-rendered HTML of each published page: `home`, `contact`, `english-privacy-policy`, `accessibility-statement`. The Croatian versions (from `/hr`) are in `pages/html/hr/` | live site |
| `pages/text/` | The readable text of each page, extracted to Markdown; Croatian in `pages/text/hr/` | extracted from the HTML |
| `pages/index.json` | Page list with language, title and file paths | |
| `scripts/write_wix_export.py` | Writes a configuration export pulled with the Wix connector into `wix-data/`, and checks `translations/hr-wix.txt` against Wix | |
| `pages/referenced-media.json` | Every image the pages use (all 6 are in the Media Manager) | |
| `pages/sitemap.xml`, `pages/pages-sitemap.xml`, `pages/hr_hr-sitemap.xml`, `pages/hr_hr-pages-sitemap.xml`, `pages/robots.txt` | As served by the live site. `robots.txt` points search engines to both the English and the Croatian sitemap | live site |
| `scripts/export_site.py` | Re-downloads the media and re-snapshots the pages (`python3 scripts/export_site.py .`) | |
| `translations/hr-wix.txt` | The Croatian translation of every text on the site, one block per Wix text item, with the original formatting kept. This exact file was loaded into Wix Multilingual | translated 2026-11-05 |
| `site/` | A standalone English/Croatian version of the site (plain HTML/CSS, no Wix). English pages are at the root, Croatian under `site/hr/`. Each page has a language picker at the top right (UK flag + EN, Croatian flag + HR) that switches to the same page in the other language | `scripts/build_site.py` |
| `scripts/build_site.py` | Rebuilds `site/` from the English page snapshots and `translations/hr-wix.txt` (`python3 scripts/build_site.py`, needs Pillow) | |
| `scripts/apply_hr_font.py` | Switches Croatian texts from Futura to Avenir Light where Futura can't draw Croatian letters (see below). Rewrites `translations/hr-wix.txt`; safe to run again | |
| `wix-data/multilingual/settings.json` | Multilingual settings and both languages: English (main, UK flag, `en-GB`) and Croatian (`/hr`, Croatian flag, `hr-HR`) | Wix Locales API |
| `wix-data/multilingual/translation-content-en.json` | Every English text item as Wix Multilingual stores it, keyed by Wix element and page | Wix Translation Content API |
| `wix-data/multilingual/translation-content-hr.json` | Every Croatian item on Wix with its publish state and a checksum; at export all 70 texts in `translations/hr-wix.txt` matched Wix exactly | Wix Translation Content API |
| `wix-data/multilingual/translation-schemas.json` | The Wix element types those texts belong to (text, button, image, page title, menu) | Wix Translation Schema API |
| `wix-data/installed-apps.json` | All 31 apps installed on the site, including Wix's built-in platform apps | Wix Apps Installer API |

## Croatian version

**On the Wix site.** Wix Multilingual is installed and the Croatian translation in `translations/hr-wix.txt` is loaded for every page, button, image description, page title and menu item. English is the main language with the UK flag; Croatian is added with the Croatian flag and lives under `/hr`. Wix shows the translations once the site is published from the Editor.

**Croatian letters and fonts.** Every text style on the Wix site uses Wix's `futura-lt-w01-book`, which has no ć, č, đ, Ć or Č, so browsers drew those letters in a fallback font. On the Croatian pages, running text (paragraphs, lists, boat specs, prices) and everything on the Privacy Policy and Accessibility pages now uses Avenir Light (`avenir-lt-w01_35-light1475496`). That font is already loaded on the site and covers every Croatian letter. Measured on the live site at 19px, it has the same x-height as Futura and the line comes out 0.4% wider, so text keeps the same size. Large headings without those letters stay in Futura to match the English pages. English pages are unchanged.

**Standalone site.** `site/` is self-contained (fonts, images and styles included), so it can be hosted anywhere that serves static files. To preview it locally:

```bash
cd site && python3 -m http.server 8000
```

Then open http://localhost:8000. Page names: `index.html` / `hr/index.html`, `contact.html` / `hr/kontakt.html`, `privacy-policy.html` / `hr/pravila-privatnosti.html`, `accessibility-statement.html` / `hr/izjava-o-pristupacnosti.html`.

The design is a rebuild in the site's colors (navy `#0A192E`, orange `#E33B08`) using the Jost font (SIL Open Font License, included in `site/assets/fonts/`). It isn't a pixel copy of the Wix layout.

## Settings made in the Wix Editor

These layout settings live only in the Wix Editor: Wix's API doesn't expose them, and they're drawn by Wix's scripts, so they aren't in the saved HTML either. Checked on the live site (version 137) on desktop and on simulated iPhone 13 and Pixel 7 phones:

- **Language menu, desktop:** top right of the header, EN and HR with UK and Croatian flags. Clicking switches to the same page in the other language.
- **Language menu, mobile:** inside the mobile menu, opened with the menu button at the top right of the header. Both EN and HR can be tapped and switch language.
- **Header:** set to **Freezes** on both desktop (82px tall) and mobile (74px tall), so phone, email, menu and language menu stay at the top while scrolling.
- **Search-engine language tags:** every page carries `hreflang` tags for `en-gb`, `hr-hr` and `x-default`, generated by Wix on the plain page addresses. Wix leaves them out when an address has extra query parameters.
- **Croatian SEO titles and descriptions:** entered in the Editor's Croatian view (Pages & Menu, then SEO basics on each page). Wix's API writes SEO tags only for the main language, so the English ones were set through the API and the Croatian ones by hand. Both are listed in `wix-data/seo.json`.

## What isn't here, and why

- **Editable page designs.** Wix doesn't export a site built in the Wix Editor as source code. The HTML in `pages/html/` is what visitors receive and still loads Wix's own scripts and styles, so it's a record of the content, not a site you can host elsewhere.
- **Wix Hotels data.** The Wix connector has no API that reads it.
- **Invoices and contacts.** Left out on purpose because they hold customers' personal details, and this repository is public.

## Things noticed during the export

- The **Privacy Policy** and **Accessibility Statement** pages are still Wix's template text (for example "[A / AA / AAA - select relevant option]").
- The phone number in Wix business info (`+385912205223`) is different from the one shown on the pages (`+385 99 8853 578`).
- Until 2026-11-07 no page had its own SEO title or meta description; all four used Wix's default pattern ("Page | NAVARIS BOATS. UNBEATABLE VALUE"). Each page now has its own title and description in both languages (see `wix-data/seo.json`).
