# Implementation Checklist

This checklist consolidates the work defined in:

- `docs/TAXONOMY_PORTFOLIO_ALIGNMENT_PLAN.md`
- `docs/CORRECTED_CSV_ORGANIZE_FLOW_PLAN.md`

It separates the taxonomy work that should happen now from the corrected-CSV organize work that should follow.

## Phase 1 — Taxonomy And Mapping Policy

- [x] Lock the two-layer contract: `review_genre` in PhotoCat vs `portfolio_category` in Photo Portfolio.
- [x] Define safe automatic mappings:
  - `Events & Music -> concert`
  - `Food & Product -> product`
  - `Nature & Landscape -> nature`
- [x] Define ambiguous genres that need manual or secondary mapping:
  - `Branding & Portrait`
  - `Street Documentary`
  - `Travel & Architecture`
  - `Wedding Photography`
  - `Other Photography`
- [x] Document that `Wedding Photography` and `Other Photography` should not be blindly forced into portfolio output.
- [x] Document `portfolio_group` derivation from `portfolio_category`.

## Phase 2 — Taxonomy Improvements In Code

- [x] Start implementation of wedding recall improvements in `src/genre_decision.py`.
- [x] Start implementation of contextual `Food & Product` demotions for audio-production/event scenes.
- [x] Reduce keyword substring leakage in classifier text matching.
- [x] Add focused classifier tests for the first-wave taxonomy changes.
- [ ] Compare the rerun in `output/gpurun17_03_1247` against `output/gpurun17_03_0949` and quantify correction deltas.
  - Raw review load dropped from `81` to `76` items.
  - `Wedding Photography` increased from `16` to `20` predictions and still needs a focused false-positive audit.
- [ ] Review new false positives introduced by stronger wedding-context rules.
- [x] Add more targeted rules for:
  - wedding reception detail vs product confusion
  - couple/event frames without explicit wedding text
  - Food & Product vs Branding & Portrait service/work scenes

## Phase 3 — Corrected CSV Contract

- [x] Make audit rows path-safe:
  - `source_path`
  - `relative_input_path`
  - stable path-based row id
- [x] Stop keying corrections by `filename` alone.
- [x] Materialize corrected organizing columns:
  - `effective_genre`
  - `portfolio_category`
  - `portfolio_group`
  - `export_include`
  - `dest_relpath`

## Phase 4 — Organize From Corrected CSV

- [x] Add a `photo-portfolio` mapping helper/profile.
- [x] Implement structured `organize-from-csv-preview`.
- [x] Implement real `organize-from-csv-commit`.
- [x] Move XMP sidecars together with their source image.
- [x] Write a manifest for every organize commit.
- [x] Add restore-from-manifest support.

## Phase 5 — Review UX And Validation

- [x] Show exact destination category/path in review UI before commit.
- [x] Keep organize disabled until corrected CSV export and successful preview.
- [x] Show missing files and conflicts in structured preview UI.
- [x] Validate output against the Photo Portfolio directory contract:
  - `/photos/portraits`
  - `/photos/concert`
  - `/photos/city`
  - `/photos/nature`
  - `/photos/product`
  - `/photos/travel-cityscape`
  - `/excluded/<effective_genre>`

## Exit Criteria

- [x] Corrected CSV is the only source of truth for organize.
- [x] Organize preview is path-safe and per-file.
- [x] Organize commit is manifest-backed and restorable.
- [ ] Taxonomy changes reduce manual corrections on the next evaluation run.
