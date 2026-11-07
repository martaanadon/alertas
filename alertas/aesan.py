"""Collector and parser for AESAN food alerts.

AESAN publishes each alert at https://www.aesan.gob.es/alertas/YYYY_NN with NN
sequential. We walk the sequence for the current year until several numbers in
a row return 404, so we never depend on the listing page layout.
"""
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import taxonomy as tx

BASE = "https://www.aesan.gob.es/alertas/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; alertas-consumo-bot/0.1; open-data reuse)"}
MONTHS = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
          "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}

FIELD_PATTERNS = [
    ("name", r"nombre del producto"),
    ("brand", r"(?:nombre de )?marca"),
    ("packaging", r"(?:aspecto del producto|envase|presentaci[oó]n)"),
    ("lot_expiry", r"(?:fecha de caducidad\s*/\s*lote|lotes? y fechas?[^:]*)"),
    ("lot", r"(?:n[uú]mero de lote|lotes?)"),
    ("expiry", r"(?:fecha de caducidad|fecha de consumo preferente|consumo preferente)"),
    ("weight", r"(?:peso de unidad|peso neto|peso)"),
    ("temperature", r"temperatura"),
    ("ean", r"(?:ean|c[oó]digo de barras|gtin)"),
]
FIELD_RE = re.compile(
    r"^\s*(?P<label>" + "|".join(f"(?P<{k}>{p})" for k, p in FIELD_PATTERNS) + r")\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------- parsing

def _blocks(soup: BeautifulSoup) -> list:
    """Text blocks from the main content, one per paragraph / list item / heading."""
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "form"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    out = []
    for el in root.find_all(["h1", "h2", "h3", "p", "li", "dt", "dd", "td"]):
        if el.find(["p", "li"]):  # avoid double-counting containers
            continue
        txt = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if txt:
            out.append(txt)
    return out


def _parse_date(text: str):
    m = re.search(r"Fecha:\s*(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m:
        d, mo, y = map(int, m.groups())
        return date(y, mo, d).isoformat()
    m = re.search(r"Fecha:\s*(\d{1,2})\s+([A-Za-zé]+)\s+(\d{4})", text)
    if m and m.group(2).lower() in MONTHS:
        return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
    return None


def _parse_products(blocks: list) -> list:
    products, cur = [], {}
    for b in blocks:
        m = FIELD_RE.match(b)
        if not m:
            continue
        key = next(k for k, _ in FIELD_PATTERNS if m.group(k))
        value = m.group("value").strip().rstrip(".")
        if key == "name" and cur.get("name"):
            products.append(cur)
            cur = {}
        if key == "ean":
            codes = re.findall(r"\b\d{8,14}\b", value)
            if not codes:
                continue
            cur.setdefault("ean", []).extend(codes)
            continue
        if key == "lot_expiry":
            cur["lot"] = value
            continue
        if key in cur and key != "name":
            cur[key] = cur[key] + "; " + value
        else:
            cur[key] = value
    if cur:
        products.append(cur)
    return products


def parse_alert(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    h1 = soup.find("h1")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if "/dam/" in src and re.search(r"\.(png|jpe?g|webp)", src, re.I):
            images.append(urljoin(url, src))
    for a in soup.find_all("a", href=True):
        if "/dam/" in a["href"] and re.search(r"\.(png|jpe?g|webp)$", a["href"], re.I):
            images.append(urljoin(url, a["href"]))

    blocks = _blocks(soup)
    full = "\n".join(blocks)

    title = h1.get_text(" ", strip=True) if h1 else ""
    if "Ref" not in title:
        title = next((b for b in blocks if re.search(r"\(Ref\.?\s*ES\d{4}/\d+\)", b)), title or page_title)
    title = re.sub(r"^(Seguridad Alimentaria/.*/)", "", title).strip()

    ref = re.search(r"Ref\.?\s*(ES\d{4}/\d+)", title + " " + full)
    cat = re.search(r"Categor[ií]a:\s*(.+)", full)
    summary = next((b for b in blocks if len(b) > 80 and ("AESAN" in b or "Agencia" in b)
                    and not b.startswith("Categor")), "")
    summary = re.sub(r"^Resumen:\s*", "", summary)
    dist = " ".join(b for b in blocks if re.search(r"distribu|comunidades aut", b, re.I))
    recs = [b for b in blocks if re.match(r"^(No consumir|Si se ha consumido|Se recomienda|Las embarazadas|"
                                          r"Extremar|Devolver|Abstenerse)", b)]

    hazard_slug, hazard_label = tx.classify_hazard(title, summary)
    regions, nationwide = tx.detect_regions(dist)
    products = _parse_products(blocks)
    brands = sorted({p["brand"].strip() for p in products if p.get("brand")})

    return {
        "source": "aesan",
        "id": "aesan-" + url.rstrip("/").rsplit("/", 1)[-1].replace("_", "-"),
        "url": url,
        "ref": ref.group(1) if ref else None,
        "title": title,
        "date": _parse_date(full),
        "category": cat.group(1).strip() if cat else None,
        "summary": summary,
        "hazard": hazard_slug,
        "hazard_label": hazard_label,
        "allergens": tx.detect_allergens(title, summary),
        "products": products,
        "brands": brands,
        "distribution": dist,
        "regions": regions,
        "nationwide": nationwide,
        "supermarkets": tx.detect_supermarkets(full),
        "recommendations": recs,
        "images": list(dict.fromkeys(images)),
    }


# ---------------------------------------------------------------- collecting

def fetch(session, url):
    r = session.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.text


def collect(year: int, out_dir: Path, raw_dir: Path, refresh_last: int = 10,
            max_misses: int = 6, delay: float = 1.0) -> dict:
    """Walk YYYY_1, YYYY_2 ... ; re-fetch the newest `refresh_last` to catch amendments."""
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(int(p.stem.split("_")[1]) for p in out_dir.glob(f"{year}_*.json"))
    refresh_from = max(existing[-refresh_last:], default=1) if existing else 1
    session = requests.Session()
    stats = {"new": 0, "updated": 0, "unchanged": 0, "errors": []}
    n, misses = 1, 0
    while misses < max_misses:
        key = f"{year}_{n}"
        path = out_dir / f"{key}.json"
        if path.exists() and n < refresh_from:
            n += 1
            misses = 0
            continue
        url = BASE + key
        try:
            html = fetch(session, url)
        except Exception as e:  # network errors are recorded, not fatal
            stats["errors"].append(f"{key}: {e}")
            html = None
        time.sleep(delay)
        if html is None:
            misses += 1
            n += 1
            continue
        misses = 0
        alert = parse_alert(html, url)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if path.exists():
            old = json.loads(path.read_text())
            comparable = {k: v for k, v in old.items() if k not in ("first_seen", "last_checked", "history")}
            if comparable == alert:
                old["last_checked"] = now
                path.write_text(json.dumps(old, ensure_ascii=False, indent=2))
                stats["unchanged"] += 1
                n += 1
                continue
            alert["first_seen"] = old.get("first_seen", now)
            alert["history"] = old.get("history", []) + [{"changed": now}]
            stats["updated"] += 1
        else:
            alert["first_seen"] = now
            alert["history"] = []
            stats["new"] += 1
        alert["last_checked"] = now
        path.write_text(json.dumps(alert, ensure_ascii=False, indent=2))
        (raw_dir / f"{key}.txt").write_text("\n".join(_blocks(BeautifulSoup(html, "html.parser"))))
        n += 1
    return stats


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, action="append")
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    years = args.year or [date.today().year]
    for y in years:
        s = collect(y, Path(args.data) / "alerts" / "aesan", Path(args.data) / "raw" / "aesan")
        print(f"AESAN {y}: {s['new']} new, {s['updated']} updated, {s['unchanged']} unchanged, "
              f"{len(s['errors'])} errors")
        for e in s["errors"][:10]:
            print("  ", e)
