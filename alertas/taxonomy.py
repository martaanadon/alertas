"""Classification helpers: hazards, allergens, regions, supermarkets.

Everything here works on the official text only. Nothing is inferred beyond
keyword matches against what the authority published.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "sin-nombre"


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


# The 14 allergens of EU Regulation 1169/2011, with the words AESAN uses.
ALLERGENS = {
    "gluten": ("Gluten", ["gluten", "trigo", "cebada", "centeno", "avena", "espelta"]),
    "leche": ("Leche y lactosa", ["leche", "lactosa", "proteina lactea", "proteinas lacteas"]),
    "huevo": ("Huevo", ["huevo"]),
    "cacahuete": ("Cacahuete", ["cacahuete"]),
    "frutos-de-cascara": ("Frutos de cáscara", ["frutos de cascara", "almendra", "avellana", "nuez", "nueces",
                                                "anacardo", "pistacho", "pecana", "macadamia"]),
    "soja": ("Soja", ["soja"]),
    "apio": ("Apio", ["apio"]),
    "mostaza": ("Mostaza", ["mostaza"]),
    "sesamo": ("Sésamo", ["sesamo"]),
    "sulfitos": ("Sulfitos", ["sulfito", "dioxido de azufre"]),
    "altramuces": ("Altramuces", ["altramuz", "altramuces"]),
    "moluscos": ("Moluscos", ["molusco"]),
    "crustaceos": ("Crustáceos", ["crustaceo", "gamba", "langostino"]),
    "pescado": ("Pescado", ["pescado"]),
}

HAZARDS = [
    # (slug, label, keywords) -- first match wins, order matters
    ("listeria", "Listeria", ["listeria"]),
    ("salmonella", "Salmonella", ["salmonella"]),
    ("e-coli", "E. coli", ["escherichia", "e. coli", "stec"]),
    ("alergenos", "Alérgenos no declarados", ["alergia", "alergico", "no declarad", "intolerancia", "celiac"]),
    ("cuerpos-extranos", "Cuerpos extraños", ["cuerpo extrano", "cuerpos extranos", "fragmento", "plastico",
                                              "metal", "vidrio", "cristal", "astilla", "piedra"]),
    ("complementos", "Complementos con sustancias no autorizadas", ["complemento alimenticio", "sildenafilo",
                                                                    "tadalafilo", "sibutramina", "no autorizad"]),
    ("micotoxinas", "Micotoxinas y toxinas", ["aflatoxina", "ocratoxina", "micotoxina", "histamina",
                                             "toxina", "botul"]),
    ("quimicos", "Contaminantes químicos", ["oxido de etileno", "plaguicida", "mercurio", "plomo",
                                           "cadmio", "residuo"]),
]
OTHER_HAZARD = ("otros", "Otros riesgos")

REGIONS = {
    "andalucia": ("Andalucía", ["andalucia"]),
    "aragon": ("Aragón", ["aragon"]),
    "asturias": ("Asturias", ["asturias"]),
    "baleares": ("Illes Balears", ["baleares", "balears"]),
    "canarias": ("Canarias", ["canarias"]),
    "cantabria": ("Cantabria", ["cantabria"]),
    "castilla-la-mancha": ("Castilla-La Mancha", ["castilla-la mancha", "castilla la mancha"]),
    "castilla-y-leon": ("Castilla y León", ["castilla y leon"]),
    "cataluna": ("Cataluña", ["cataluna", "catalunya"]),
    "comunidad-valenciana": ("Comunitat Valenciana", ["valenciana", "comunidad valenciana"]),
    "extremadura": ("Extremadura", ["extremadura"]),
    "galicia": ("Galicia", ["galicia"]),
    "madrid": ("Comunidad de Madrid", ["madrid"]),
    "murcia": ("Región de Murcia", ["murcia"]),
    "navarra": ("Navarra", ["navarra"]),
    "pais-vasco": ("País Vasco", ["pais vasco", "euskadi"]),
    "la-rioja": ("La Rioja", ["la rioja"]),
    "ceuta": ("Ceuta", ["ceuta"]),
    "melilla": ("Melilla", ["melilla"]),
}
NATIONWIDE_MARKERS = ["todo el territorio nacional", "todas las comunidades", "toda espana", "a nivel nacional"]

SUPERMARKETS = {
    "mercadona": "Mercadona", "lidl": "Lidl", "aldi": "Aldi", "carrefour": "Carrefour", "dia": "Dia",
    "eroski": "Eroski", "alcampo": "Alcampo", "consum": "Consum", "ahorramas": "Ahorramas",
    "el-corte-ingles": "El Corte Inglés", "hipercor": "Hipercor", "supercor": "Supercor", "gadis": "Gadis",
    "bonpreu": "Bonpreu", "caprabo": "Caprabo", "froiz": "Froiz", "family-cash": "Family Cash",
    "costco": "Costco", "iceland": "Iceland", "coviran": "Covirán", "masymas": "masymas", "bm": "BM",
}


def _has(text_n: str, word: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text_n) is not None


def classify_hazard(title: str, summary: str = "") -> tuple:
    t = _norm(title + " " + summary)
    for slug, label, kws in HAZARDS:
        if any(k in t for k in kws):
            return slug, label
    return OTHER_HAZARD


def detect_allergens(title: str, summary: str = "") -> list:
    """Only fires when the alert is about undeclared allergens / allergy warnings."""
    t = _norm(title + " " + summary)
    if not any(k in t for k in ["alergia", "alergico", "no declarad", "intolerancia", "celiac"]):
        return []
    found = []
    for slug, (_label, kws) in ALLERGENS.items():
        if any(_has(t, k) for k in kws):
            found.append(slug)
    return found


def detect_regions(text: str) -> tuple:
    """Returns (region_slugs, nationwide_flag)."""
    t = _norm(text)
    nationwide = any(m in t for m in NATIONWIDE_MARKERS)
    found = [slug for slug, (_l, kws) in REGIONS.items() if any(_has(t, k) for k in kws)]
    return found, nationwide


def detect_supermarkets(text: str) -> list:
    t = _norm(text)
    found = []
    for slug, label in SUPERMARKETS.items():
        word = _norm(label)
        # "Dia" and "BM" are ambiguous words: require a capitalised match in the original text
        if slug in ("dia", "bm"):
            if re.search(r"(?<![\wÁÉÍÓÚáéíóúñ])" + re.escape(label) + r"(?![\wÁÉÍÓÚáéíóúñ])", text):
                found.append(slug)
        elif _has(t, word):
            found.append(slug)
    return found
