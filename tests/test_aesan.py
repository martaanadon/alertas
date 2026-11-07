from pathlib import Path

from alertas.aesan import parse_alert
from alertas import taxonomy as tx

FIX = Path(__file__).parent / "fixtures"


def load(name, url):
    return parse_alert((FIX / name).read_text(encoding="utf-8"), url)


def test_listeria_alert():
    a = load("aesan_2026_80.html", "https://www.aesan.gob.es/alertas/2026_80")
    assert a["id"] == "aesan-2026-80"
    assert a["ref"] == "ES2026/665"
    assert a["date"] == "2026-11-04"
    assert a["hazard"] == "listeria"
    assert a["allergens"] == []
    assert a["category"].startswith("Alertas alimentarias")
    assert len(a["products"]) == 1
    p = a["products"][0]
    assert p["name"] == "Jamón cocido"
    assert p["brand"] == "URKABE"
    assert p["lot"] == "61027"
    assert p["expiry"] == "26/11/2026"
    assert p["weight"] == "175 g"
    assert set(a["regions"]) == {"castilla-y-leon", "madrid", "navarra", "pais-vasco"}
    assert not a["nationwide"]
    assert a["images"] and a["images"][0].startswith("https://www.aesan.gob.es/dam/")
    assert any(r.startswith("No consumir") for r in a["recommendations"])
    assert "AESAN" in a["summary"]


def test_multi_product_allergen_alert():
    a = load("aesan_multi_allergen.html", "https://www.aesan.gob.es/alertas/2026_45")
    assert a["date"] == "2026-06-03"
    assert a["hazard"] == "alergenos"
    assert a["allergens"] == ["frutos-de-cascara"]
    assert len(a["products"]) == 2
    assert a["products"][0]["ean"] == ["8435257023144"]
    assert "ean" not in a["products"][1]          # "No disponible" is not a code
    assert a["products"][0]["lot"].endswith("3006BK")
    assert a["brands"] == ["Hacendado"]
    assert a["nationwide"]
    assert set(a["supermarkets"]) == {"mercadona", "lidl"}


def test_dia_needs_capital():
    assert tx.detect_supermarkets("vendido en Dia y en Mercadona") == ["mercadona", "dia"]
    assert tx.detect_supermarkets("durante el día de hoy") == []


def test_slugify():
    assert tx.slugify("Castilla y León") == "castilla-y-leon"
    assert tx.slugify("URKABE") == "urkabe"
