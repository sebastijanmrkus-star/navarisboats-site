# navarisboats.com: site export

A backup of the Wix site **NAVARIS BOATS. UNBEATABLE VALUE** (https://www.navarisboats.com), taken on 2026-11-05.
It was pulled with the Wix connector (site data, SEO, Media Manager) and from the live published site (page snapshots).

## What's in here

| Path | Contents | Source |
|---|---|---|
| `wix-data/site.json` | Site ID, plan, editor type, installed apps, business info (name, email, phone, locale, currency, time zone) | Wix Site Properties API |
| `wix-data/seo.json` | The 4 static pages with their IDs, URLs and SEO titles; redirects (none); URL mappings (none) | Wix SEO APIs |
| `wix-data/media-manager.json` | Metadata for every file and folder in the Media Manager | Wix Media Manager API |
| `media/` | The **original** of all 21 Media Manager images (8.8 MB), in their Media Manager folders. `media/index.json` maps each file to its Wix file ID and URL | static.wixstatic.com |
| `pages/html/` | Server-rendered HTML of each published page: `home`, `contact`, `english-privacy-policy`, `accessibility-statement` | live site |
| `pages/text/` | The readable text of each page, extracted to Markdown | extracted from the HTML |
| `pages/index.json` | Page list with title and file paths | |
| `pages/referenced-media.json` | Every image the pages use (all 6 are in the Media Manager) | |
| `pages/sitemap.xml`, `pages/pages-sitemap.xml`, `pages/robots.txt` | As served by the live site | live site |
| `scripts/export_site.py` | Re-downloads the media and re-snapshots the pages (`python3 scripts/export_site.py .`) | |
| `translations/hr-wix.txt` | The Croatian translation of every text on the site, one block per Wix text item, with the original formatting kept. This exact file was loaded into Wix Multilingual | translated 2026-11-05 |
| `site/` | A standalone English/Croatian version of the site (plain HTML/CSS, no Wix). English pages are at the root, Croatian under `site/hr/`. Each page has a language picker at the top right (UK flag + EN, Croatian flag + HR) that switches to the same page in the other language | `scripts/build_site.py` |
| `scripts/build_site.py` | Rebuilds `site/` from the English page snapshots and `translations/hr-wix.txt` (`python3 scripts/build_site.py`, needs Pillow) | |

## Croatian version

**On the Wix site.** Wix Multilingual is installed and the Croatian translation in `translations/hr-wix.txt` is loaded for every page, button, image description, page title and menu item. English is the main language with the UK flag; Croatian is added with the Croatian flag and lives under `/hr`. Wix shows the translations once the site is published from the Editor.

**Standalone site.** `site/` is self-contained (fonts, images and styles included), so it can be hosted anywhere that serves static files. To preview it locally:

```bash
cd site && python3 -m http.server 8000
```

Then open http://localhost:8000. Page names: `index.html` / `hr/index.html`, `contact.html` / `hr/kontakt.html`, `privacy-policy.html` / `hr/pravila-privatnosti.html`, `accessibility-statement.html` / `hr/izjava-o-pristupacnosti.html`.

The design is a rebuild in the site's colors (navy `#0A192E`, orange `#E33B08`) using the Jost font (SIL Open Font License, included in `site/assets/fonts/`). It isn't a pixel copy of the Wix layout.

## What isn't here, and why

- **Editable page designs.** Wix doesn't export a site built in the Wix Editor as source code. The HTML in `pages/html/` is what visitors receive and still loads Wix's own scripts and styles, so it's a record of the content, not a site you can host elsewhere.
- **Wix Hotels data.** The Wix connector has no API that reads it.
- **Invoices and contacts.** Left out on purpose because they hold customers' personal details, and this repository is public.

## Things noticed during the export

- The **Privacy Policy** and **Accessibility Statement** pages are still Wix's template text (for example "[A / AA / AAA - select relevant option]").
- The phone number in Wix business info (`+385912205223`) is different from the one shown on the pages (`+385 99 8853 578`).
- No page has its own SEO title or description. All four use Wix's default pattern ("Page | NAVARIS BOATS. UNBEATABLE VALUE"), and none has a meta description.
