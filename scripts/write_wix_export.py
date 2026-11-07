"""Write a Wix configuration export (JSON pulled with the Wix connector) into wix-data/.

Usage (from the repo root): python3 scripts/write_wix_export.py <export.json>

The export JSON is produced through the Wix connector (ExecuteWixAPI) and holds:
localeSettings, locales, installedApps, siteProperties(+Version), redirects,
translationSchemas, hrChecksums, enContents, mediaFolders, mediaFiles.

Besides writing the files, it checks every Croatian text in translations/hr-wix.txt
against the checksum Wix reports (FNV-1a over UTF-16) and exits non-zero on a mismatch.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_NAMES = {
    "14d84998-ae09-1abf-c6fc-3f3cace5bf19": "Wix Multilingual",
    "14bca956-e09f-f4d6-14d7-466cb3f09103": "Wix Hotels",
    "13ee94c1-b635-8505-3391-97919052c16f": "Wix Invoices",
    "1480c568-5cbd-9392-5604-1148f5faffa0": "Promote SEO",
}


def fnv(s):
    h = 0x811C9DC5
    b = s.encode("utf-16-le")
    for i in range(0, len(b), 2):
        h ^= b[i] | (b[i + 1] << 8)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "x")


def dump(rel, obj):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("wrote", rel)


def load_hr():
    hr, cur = {}, None
    for line in open(os.path.join(ROOT, "translations/hr-wix.txt"), encoding="utf-8").read().split("\n"):
        m = re.match(r"^=== (\S+) (\S+)\s*$", line)
        if m:
            cur = (m.group(1), m.group(2))
            hr[cur] = []
        elif cur:
            hr[cur].append(line)
    return {k: "\n".join(v).strip().replace("{ZWSP}", "​") for k, v in hr.items()}


def main(path):
    src = open(path, encoding="utf-8").read()
    if src.lstrip().startswith("[TRUNCATED"):
        sys.exit("export is truncated; pull it again in smaller parts")
    j = json.loads(src)
    ts = j["exportedAt"]

    # 1. verify the repo's Croatian texts against Wix
    hr = load_hr()
    wix = {(c["entityId"], k): v for c in j["hrChecksums"] for k, v in c["sums"].items()}
    mismatched = [k for k in hr if k in wix and wix[k]["fnv"] != fnv(hr[k])]
    missing = [k for k in hr if k not in wix]
    print("croatian texts identical to Wix: %d of %d" % (len(hr) - len(mismatched) - len(missing), len(hr)))
    if mismatched or missing:
        print("  different:", mismatched, "\n  missing on Wix:", missing)

    # 2. multilingual
    dump("wix-data/multilingual/settings.json", {
        "_source": "Wix connector: Locale Settings API + Locales API, pulled " + ts,
        "localeSettings": j["localeSettings"],
        "locales": j["locales"],
    })
    dump("wix-data/multilingual/translation-schemas.json", {
        "_source": "Wix connector: Translation Schema API (only the schemas this site has content for), pulled " + ts,
        "schemas": j["translationSchemas"],
    })
    dump("wix-data/multilingual/translation-content-en.json", {
        "_source": "Wix connector: Translation Content API, English (main language) items as Wix stores them, pulled " + ts,
        "_note": "These mirror the Editor content. Each item is one Wix element (entityId) on a page (parentEntityId; masterPage = shown on every page).",
        "items": sorted(j["enContents"], key=lambda c: (c.get("parentEntityId") or "", c["entityId"])),
    })
    hr_items = []
    for c in j["hrChecksums"]:
        item = {k: c[k] for k in ("entityId", "schemaId", "parentEntityId", "publishStatus", "updatedDate") if c.get(k) is not None}
        item["fields"] = {f: {"published": v["published"], "length": v["len"], "fnv1a": v["fnv"]} for f, v in c["sums"].items()}
        hr_items.append(item)
    dump("wix-data/multilingual/translation-content-hr.json", {
        "_source": "Wix connector: Translation Content API, Croatian items, pulled " + ts,
        "_note": "The Croatian texts themselves are in translations/hr-wix.txt. At export, %d of %d texts in that file were identical to Wix (FNV-1a checksum over UTF-16)." % (len(hr) - len(mismatched) - len(missing), len(hr)),
        "items": sorted(hr_items, key=lambda c: (c.get("parentEntityId") or "", c["entityId"])),
    })

    # 3. apps, media, site, seo
    apps = [dict(a, name=APP_NAMES[a["appDefId"]]) if a["appDefId"] in APP_NAMES else a for a in j["installedApps"]]
    dump("wix-data/installed-apps.json", {
        "_source": "Wix connector: Apps Installer API (Get Installed Apps), pulled " + ts,
        "_note": "Includes the platform apps every Wix site carries; the API returns ids only, names are added for the business apps.",
        "apps": sorted(apps, key=lambda a: ("name" not in a, a.get("name", ""), a["appDefId"])),
    })
    dump("wix-data/media-manager.json", {
        "_source": "Wix connector: Media Manager API (List Folders / List Files), pulled " + ts,
        "folders": [{"id": "media-root", "displayName": "(root)"}] + j["mediaFolders"],
        "files": j["mediaFiles"],
    })
    site_path = os.path.join(ROOT, "wix-data/site.json")
    site = json.load(open(site_path, encoding="utf-8"))
    site["_source"] = "Wix connector (GetSiteContext + Site Properties API v4), first pulled 2026-11-05, refreshed " + ts
    site["siteProperties"] = {"version": j["sitePropertiesVersion"], "properties": j["siteProperties"]}
    dump("wix-data/site.json", site)
    seo_path = os.path.join(ROOT, "wix-data/seo.json")
    seo = json.load(open(seo_path, encoding="utf-8"))
    seo["redirects"] = j["redirects"]
    seo["_source"] = seo["_source"].split(", pulled")[0] + ", redirects refreshed " + ts
    dump("wix-data/seo.json", seo)

    print("counts:", j["counts"])
    return 1 if (mismatched or missing) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
