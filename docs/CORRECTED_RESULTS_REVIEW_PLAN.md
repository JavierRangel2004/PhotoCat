# PhotoCat Corrected Results Review Plan

This document summarizes the current manual review results from:
- `output/full_audit_corrected.csv`
- `output/full_audit_corrected.txt`

It focuses on the rows marked `user_label = wrong` and the recommendations captured from the external AI-assisted review notes.

## Current Snapshot

- Total reviewed rows: `274`
- Rows marked `wrong`: `122`
- Wrong rows originally marked `auto`: `84`
- Wrong rows originally marked `review`: `33`
- Wrong rows originally marked `title-inferred`: `5`

This means the main quality issue is not just uncertain cases. A large share of the incorrect results were confident automatic assignments.

## Highest-Impact Misclassification Patterns

Top wrong-label transitions in `output/full_audit_corrected.csv`:

1. `Street Photography -> Architecture Photography`: `44`
2. `Portrait Photography -> Wedding Photography`: `23`
3. `Music Photography -> Wedding Photography`: `8`
4. `Product Photography -> Wedding Photography`: `6`
5. `Nature Photography -> Wedding Photography`: `6`
6. `Nature Photography -> Other Photography`: `6`
7. `Product Photography -> Street Photography`: `4`
8. `Street Photography -> Wedding Photography`: `3`
9. `Nature Photography -> Architecture Photography`: `3`

These patterns dominate the correction workload and should drive the next backend tuning pass.

## What The AI Review Notes Reinforce

The text review in `output/full_audit_corrected.txt` repeatedly points to the same structural problems:

- Architecture images are being pulled into `Street Photography` whenever the model sees outdoor urban context, paths, alleys, or city views.
- Wedding images are split across `Portrait`, `Music`, `Nature`, `Product`, and `Street` because the current logic is not strongly detecting wedding semantics from captions, people-group structure, clothing, or ceremony/reception context.
- Travel and landscape-style images are being forced into `Nature` or `Street` because there is no better bucket than `Other`.
- Product labels are over-triggered by food stalls, branded items, bottles, and objects even when the real image intent is documentary or street.
- The classifier often overweights global scene/background cues and underweights detected people or subject intent.
- Empty or weak object detection is leaving the system too dependent on caption text and global scene classification.

## Concrete Pattern Review

### 1. Street vs Architecture

This is the biggest problem by volume.

Typical examples:
- clock towers
- facades
- staircases
- hallways
- cityscape silhouettes
- monuments framed by foliage or gates

Observed failure mode:
- any urban outdoor scene is drifting toward `Street Photography`
- human presence is not necessary for the current model to assign `Street`

Recommended fixes:
- require stronger human/candid/public-life evidence before finalizing `Street Photography`
- boost `Architecture Photography` when captions mention:
  - tower
  - clock
  - building
  - facade
  - staircase
  - archway
  - window
  - columns
  - statue
  - monument
- use object/context rules so incidental people do not override a structure-dominant composition
- treat cityscape or skyline views as `Architecture` unless strong candid-human evidence is present

### 2. Wedding Detection

This is the second largest issue and likely the highest-value business fix.

Observed wrong sources:
- `Portrait -> Wedding`
- `Music -> Wedding`
- `Product -> Wedding`
- `Nature -> Wedding`
- `Street -> Wedding`

Typical examples:
- bride and groom portraits
- group photos
- speeches
- dancing
- rings, flowers, place settings
- reception scenes

Observed failure mode:
- the system identifies the visual sub-scene but misses the event-level category
- wedding semantics are not dominating when the caption clearly indicates bride, groom, bouquet, veil, reception, family, speech, or dance

Recommended fixes:
- aggressively boost `Wedding Photography` on captions/titles containing:
  - bride
  - groom
  - bouquet
  - veil
  - wedding
  - bridesmaid
  - groomsmen
  - reception
  - ceremony
- use combined people-count plus formal clothing cues plus event context as a wedding prior
- allow `Wedding` to override `Portrait`, `Music`, `Product`, and `Nature` when explicit wedding language exists

### 3. Nature vs Other

Several corrected rows moved from `Nature Photography` to `Other Photography`.

Typical examples:
- ships in fog
- travel landscapes with roads
- atmospheric travel scenes
- industrial or maritime shots

Observed failure mode:
- the model is overusing `Nature` for wide scenic frames even when the real subject is industrial, travel, or minimalist atmosphere

Recommended fixes:
- if boats, roads, ports, urban infrastructure, or industrial structures dominate, reduce `Nature`
- use `Other` as the fallback for travel/industrial/minimalist scenes until a dedicated travel/landscape class exists

### 4. Product vs Street

Typical examples:
- food stalls
- vendors
- people handling products
- documentary market scenes

Observed failure mode:
- branded packaging, repeated objects, and food textures trigger `Product Photography`
- candid workers and environmental context are not weighted enough

Recommended fixes:
- demote `Product` when multiple people are present and the caption implies labor, action, or a market scene
- boost `Street` when the image tells a public-life story instead of presenting a clean product hero shot

### 5. Product vs Nature / Portrait

Important specific misses:
- shark or wildlife scenes classified as `Product`
- moon classified as `Product`
- jewelry classified as `Portrait`

Recommended fixes:
- add contradiction rules:
  - `moon`, `sky`, `shark`, `bird`, `wildlife`, `ocean` should strongly oppose `Product`
  - `ring`, `necklace`, `chain`, `jewelry` should strongly oppose `Portrait` and favor `Product`

## Prioritized Backend Fix Order

1. Fix `Street -> Architecture`
2. Fix all `* -> Wedding`
3. Fix `Nature -> Other` travel/industrial edge cases
4. Fix `Product -> Street` in food/vendor/documentary scenes
5. Add contradiction rules for moon, wildlife, jewelry, and similar hard failures

## Recommended Code Review Targets

Start with:
- `src/genre_decision.py`
- `src/scene_classifier.py`
- any title/caption fallback rules
- any confidence-threshold logic that is allowing `auto` decisions for these failure patterns

Specifically review:
- rules for `Street Photography`
- rules for `Architecture Photography`
- wedding keyword and context handling
- product contradiction rules
- weighting between caption, object detection, title fallback, and raw scene confidence

## Practical Next Step

The best next implementation pass is not broad model retraining first.

Instead:
1. codify the high-volume correction patterns above into deterministic decision rules
2. rerun against this same 274-image set
3. compare how many of the `122` wrong rows disappear
4. only then decide whether taxonomy expansion or retraining is needed

## Notes On The AI Review File

`output/full_audit_corrected.txt` is useful as a qualitative review aid, not as source-of-truth labels.

Use it for:
- recurring logic themes
- identifying missing contradiction rules
- spotting where the current model overweights background or scene texture

Do not use it directly as label truth without comparing against the actual corrected CSV decisions you finalized in the UI.
