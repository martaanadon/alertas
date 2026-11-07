# Backlog (ordered)

1. **Verify parser on real pages.** Inspect `data/raw/aesan/*.txt` from the first run. Fix
   field extraction where it misses lots, EANs or multi-product alerts. Replace synthetic
   fixtures with 5 real pages (one per hazard type).
2. **Backfill 2025** (`workflow_dispatch` with `years: 2025`) once the parser is verified.
3. **Safety Gate parser.** Write it against the saved weekly export in `data/raw/safetygate/`.
   Publish only alerts relevant to Spain (notified by Spain or with Spanish follow-up).
   Owner approval needed before going live.
4. **Christmas toy guide** ("Juguetes retirados en 2026"), built from Safety Gate + Consumo data.
   Target: live before 1 December. Owner approval needed (editorial page).
5. **Consumo national alerts** (non-food, ~200 published per year).
6. **AEMPS** (medicines, cosmetics, medical devices).
7. **Link amendments** to their original alert and show a change log on the page.
8. **Domain + Search Console + privacy-friendly analytics.** Owner decision.
9. **Email alerts** by allergen / brand / supermarket. Owner decision (personal data).
