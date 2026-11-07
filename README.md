# Alertas de consumo

Productos retirados en España, buscables por marca, lote y código de barras.
Datos oficiales (AESAN; próximamente Safety Gate, Consumo y AEMPS).

## How it works

- `alertas/aesan.py` walks `https://www.aesan.gob.es/alertas/YYYY_NN` and saves one JSON per alert
  in `data/alerts/aesan/`, plus the page text in `data/raw/aesan/` for auditing.
- `alertas/build.py` turns the JSON into a static site in `_site/`.
- `.github/workflows/daily.yml` runs twice a day: tests → collect → commit data → build → deploy
  to GitHub Pages.
- `agent/` holds the rules for the AI agent that maintains the site
  (`CHARTER.md`), its current state and its backlog.

## Run locally

```bash
pip install -r requirements.txt
python -m pytest -q
python -m alertas.aesan --year 2026
SITE_URL=http://localhost:8000 python -m alertas.build
python -m http.server -d _site 8000
```

## One-time setup on GitHub

Settings → Pages → Build and deployment → Source: **GitHub Actions**.
Then Actions → "Daily update" → Run workflow.
