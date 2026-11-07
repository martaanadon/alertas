"""Static site generator: data/alerts/**/*.json -> _site/

Thin-page rule (see agent/CHARTER.md): hub pages with fewer than
MIN_INDEXABLE alerts are generated (useful to visitors) but marked noindex
and left out of the sitemap.
"""
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import taxonomy as tx

ROOT = Path(__file__).resolve().parent.parent
MIN_INDEXABLE = 3
SPANISH_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                  "septiembre", "octubre", "noviembre", "diciembre"]


def load_config():
    cfg = json.loads((ROOT / "site.json").read_text())
    cfg["base_url"] = os.environ.get("SITE_URL", cfg["base_url"]).rstrip("/")
    cfg["base_path"] = urlparse(cfg["base_url"]).path.rstrip("/")
    return cfg


def load_alerts(data_dir: Path) -> list:
    alerts = []
    for p in sorted(data_dir.glob("alerts/*/*.json")):
        a = json.loads(p.read_text())
        if not a.get("title") or not a.get("date"):
            continue  # unparsed pages are never published
        alerts.append(a)
    alerts.sort(key=lambda a: (a["date"], a["id"]), reverse=True)
    return alerts


def human_date(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} de {SPANISH_MONTHS[d.month - 1]} de {d.year}"


def build(data_dir: Path = ROOT / "data", out: Path = ROOT / "_site"):
    cfg = load_config()
    alerts = load_alerts(data_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(ROOT / "static", out / "static")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
    env.filters["human_date"] = human_date
    env.globals.update(site=cfg, now=datetime.now(timezone.utc),
                       allergen_labels={k: v[0] for k, v in tx.ALLERGENS.items()},
                       region_labels={k: v[0] for k, v in tx.REGIONS.items()},
                       supermarket_labels=tx.SUPERMARKETS)
    sitemap = []

    def url(path):
        return f"{cfg['base_path']}/{path}".replace("//", "/")

    env.globals["url"] = url

    def write(path, template, indexable=True, **ctx):
        dest = out / path / "index.html" if not path.endswith(".html") else out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        ctx.setdefault("canonical", f"{cfg['base_url']}/{path}")
        dest.write_text(env.get_template(template).render(indexable=indexable, **ctx))
        if indexable:
            sitemap.append(f"{cfg['base_url']}/{path}")

    # hubs
    hubs = {"riesgo": defaultdict(list), "alergeno": defaultdict(list), "comunidad": defaultdict(list),
            "marca": defaultdict(list), "supermercado": defaultdict(list)}
    hazard_labels = {}
    brand_labels = {}
    for a in alerts:
        hubs["riesgo"][a["hazard"]].append(a)
        hazard_labels[a["hazard"]] = a["hazard_label"]
        for s in a["allergens"]:
            hubs["alergeno"][s].append(a)
        regions = list(tx.REGIONS) if a.get("nationwide") else a.get("regions", [])
        for r in regions:
            hubs["comunidad"][r].append(a)
        for b in a.get("brands", []):
            slug = tx.slugify(b)
            hubs["marca"][slug].append(a)
            brand_labels[slug] = b
        for s in a.get("supermarkets", []):
            hubs["supermercado"][s].append(a)

    label_for = {
        "riesgo": lambda s: hazard_labels[s],
        "alergeno": lambda s: tx.ALLERGENS[s][0],
        "comunidad": lambda s: tx.REGIONS[s][0],
        "marca": lambda s: brand_labels[s],
        "supermercado": lambda s: tx.SUPERMARKETS[s],
    }
    hub_index = {}
    for kind, groups in hubs.items():
        hub_index[kind] = sorted(((s, label_for[kind](s), len(v)) for s, v in groups.items()),
                                 key=lambda x: (-x[2], x[1]))
        for slug, items in groups.items():
            write(f"{kind}/{slug}/", "hub.html", indexable=len(items) >= MIN_INDEXABLE,
                  kind=kind, slug=slug, label=label_for[kind](slug), alerts=items)

    # alert pages
    for a in alerts:
        related = [b for b in hubs["riesgo"][a["hazard"]] if b["id"] != a["id"]][:5]
        write(f"alerta/{a['id']}/", "alert.html", a=a, related=related,
              brand_slugs={b: tx.slugify(b) for b in a.get("brands", [])})

    write("", "index.html", alerts=alerts[:30], hubs=hub_index, total=len(alerts), canonical=cfg["base_url"] + "/")
    write("buscar/", "search.html")
    write("metodologia/", "page_methodology.html")
    write("aviso-legal/", "page_legal.html", indexable=False)

    # search index: small, only what the search box needs
    index = [{"id": a["id"], "t": a["title"], "d": a["date"], "h": a["hazard_label"],
              "b": a.get("brands", []),
              "p": [p.get("name", "") for p in a["products"]],
              "l": [p.get("lot", "") for p in a["products"] if p.get("lot")],
              "e": [e for p in a["products"] for e in p.get("ean", [])]} for a in alerts]
    (out / "search-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")))

    # feeds and crawl files
    items = "".join(
        f"<item><title>{escape(a['title'])}</title><link>{cfg['base_url']}/alerta/{a['id']}/</link>"
        f"<guid>{cfg['base_url']}/alerta/{a['id']}/</guid><pubDate>{a['date']}</pubDate>"
        f"<description>{escape(a.get('summary', ''))}</description></item>" for a in alerts[:50])
    (out / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{escape(cfg["name"])}</title>'
        f"<link>{cfg['base_url']}/</link><description>{escape(cfg['tagline'])}</description>{items}</channel></rss>")
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{escape(u)}</loc></url>" for u in sitemap) + "</urlset>")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {cfg['base_url']}/sitemap.xml\n")
    (out / ".nojekyll").write_text("")
    return {"alerts": len(alerts), "pages_indexable": len(sitemap)}


if __name__ == "__main__":
    print(build())
