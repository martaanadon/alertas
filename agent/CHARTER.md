# Agent charter

This file is the operating contract for any AI agent working on this repository.
Read it, `STATE.md` and `BACKLOG.md` before doing anything.

## Objective

Become the most useful place in Spain to answer "is this product recalled, and what do I do?".
Success metric: **non-brand Google clicks to alert, brand, allergen and search pages**, with
engagement as a guardrail. Raw page count is not a goal.

## Hard rules (never break)

1. **Official data only.** Product names, brands, lots, dates, barcodes and distribution come
   from the official source, unchanged. Never invent, infer or "complete" a field.
2. **Every alert page links to its official source** and shows the source's publication date.
3. **No opinions about brands, companies or products.** Factual reproduction only.
4. **Never publish what failed to parse.** Alerts without title and date are not built. If a
   parser change breaks tests, nothing publishes (the workflow runs tests first).
5. **Thin-page rule.** Hub pages (brand, region, allergen, hazard, supermarket) with fewer than 3
   alerts are `noindex` and out of the sitemap. Do not lower this threshold without approval.
6. **No health advice beyond the source.** "What to do" text either quotes the source's
   recommendations or uses the generic, approved wording in `templates/alert.html`.
7. **Images** only from the official source, always credited.
8. **No personal data** is collected. Email alerts need explicit approval first (see below).

## Approval policy

| Change | Approval |
|---|---|
| New data collected by existing collectors, rebuilds | Automatic (daily workflow) |
| Parser fixes with a new or updated test | PR, auto-merge allowed if all tests pass |
| SEO fixes: titles, descriptions, internal links, sitemap | PR, auto-merge allowed if tests pass |
| New page template or new hub type | **Owner approves PR** |
| New data source going live (Safety Gate, Consumo, AEMPS) | **Owner approves PR** |
| Any editorial text (guides, explainers) | **Owner approves PR** |
| Email alerts, analytics, cookies, monetization, domain | **Owner approves PR + one-paragraph memo** |
| Deleting pages, redirects, changing URLs | **Owner approves, always** |

## Working loop

1. Read `STATE.md`. Pick one item from `BACKLOG.md` or one Search Console opportunity.
2. Make the change on a branch with tests. Open a PR describing: hypothesis, change, metric,
   date to measure (at least 3 weeks out).
3. Log it in `STATE.md` under "Experiments".
4. Never run more than one experiment per page type at a time, so results can be attributed.
