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

## What isn't here, and why

- **Editable page designs.** Wix doesn't export a site built in the Wix Editor as source code. The HTML in `pages/html/` is what visitors receive and still loads Wix's own scripts and styles, so it's a record of the content, not a site you can host elsewhere.
- **Wix Hotels data.** The Wix connector has no API that reads it.
- **Invoices and contacts.** Left out on purpose because they hold customers' personal details, and this repository is public.

## Things noticed during the export

- The **Privacy Policy** and **Accessibility Statement** pages are still Wix's template text (for example "[A / AA / AAA - select relevant option]").
- The phone number in Wix business info (`+385912205223`) is different from the one shown on the pages (`+385 99 8853 578`).
- No page has its own SEO title or description. All four use Wix's default pattern ("Page | NAVARIS BOATS. UNBEATABLE VALUE"), and none has a meta description.
