# State

_Updated: 2026-11-05_

## Live

- AESAN food alerts: collector, parser (tests on fixtures), alert pages, hubs, search, RSS, sitemap.
- Hosting: GitHub Pages at https://martaanadon.github.io/alertas/ (temporary until a domain is chosen).
- Updates: twice a day via `.github/workflows/daily.yml`.

## Known gaps

- Parser fixtures are reconstructed from page text, not real AESAN HTML. After the first real run,
  replace them with saved real pages from `data/raw/aesan/` and re-check field extraction.
- AESAN "ampliaciones" (amendments): we re-fetch the latest 10 alerts each run. Amendments
  published at separate URLs are not yet linked to their original alert.
- Safety Gate: raw download only. No parser yet.
- No analytics and no Search Console yet (needs a domain/verification by the owner).

## Experiments

_None yet._
