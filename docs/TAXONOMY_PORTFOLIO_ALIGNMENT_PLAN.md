# Taxonomy And Portfolio Alignment Plan

## Purpose

This document evaluates the `gpurun17_03_0949` review set and defines how PhotoCat should improve categorization so the final organized output is usable by the Photo Portfolio repo at `C:\Users\javar\GITHUB\Photo-Portfolio\src`.

The key constraint is that PhotoCat and Photo Portfolio do not use the same taxonomy:

- PhotoCat review taxonomy is currently:
  - `Branding & Portrait`
  - `Events & Music`
  - `Street Documentary`
  - `Food & Product`
  - `Nature & Landscape`
  - `Travel & Architecture`
  - `Other Photography`
  - `Wedding Photography`
- Photo Portfolio raw categories are currently:
  - `portraits`
  - `concert`
  - `city`
  - `nature`
  - `product`
  - `travel-cityscape`

Because of that mismatch, the correct solution is not "organize directly by final genre". The correct solution is a two-layer contract:

1. PhotoCat predicts and reviews with its working taxonomy.
2. A second mapping step converts the corrected review result into the exact portfolio category slug and directory structure expected by Photo Portfolio.

## Evaluated Result Set

Artifacts reviewed:

- `gpurun17_03_0949.txt`
- `gpurun17_03_0949.csv`
- `gpurun17_03_0949_corrected.csv`

Observed totals:

- Total rows: `274`
- Rows with `user_label=wrong`: `57`
- Rows with `user_label=correct`: `126`
- Rows without label: `91`
- Wrong rows originally marked `auto`: `27`
- Wrong rows originally marked `review`: `28`
- Wrong rows originally marked `title-inferred`: `2`

Immediate implication:

- A large part of the problem is not only low-confidence review rows.
- The system is making materially wrong confident decisions.
- Organize must therefore follow the corrected CSV, not the live pipeline result in memory.

## Main Error Patterns From Manual Review

Top corrected transitions:

- `Branding & Portrait -> Wedding Photography`: `13`
- `Events & Music -> Wedding Photography`: `8`
- `Food & Product -> Branding & Portrait`: `6`
- `Food & Product -> Street Documentary`: `4`
- `Nature & Landscape -> Travel & Architecture`: `3`

Net category shifts after correction:

- `Wedding Photography`: `16 -> 43`
- `Food & Product`: `61 -> 49`
- `Branding & Portrait`: `42 -> 34`
- `Events & Music`: `22 -> 17`
- `Other Photography`: `5 -> 1`

Interpretation:

### 1. Wedding is the biggest recall failure

The model is already able to identify explicit wedding cues when titles include `bride`, `groom`, `veil`, or similar language. The main failure is that many wedding frames without explicit text are still routed into:

- `Branding & Portrait`
- `Events & Music`
- `Other Photography`
- `Nature & Landscape`

This means the current wedding logic is too dependent on explicit semantics and not strong enough on context combinations such as:

- couples in formalwear
- family groups in coordinated dress
- speeches, confetti, bouquet, celebration tables
- wedding party structure
- reception atmosphere without stage/music evidence

### 2. Food & Product is overloaded

`Food & Product` is catching:

- true product images
- restaurant or market documentary scenes
- beverage-in-context editorial shots
- some people-centered branding images
- some wedding detail/reception frames

This category currently mixes object-centered commercial stills with contextual scenes that should route elsewhere.

### 3. Travel/architecture vs nature is still a boundary case

The run shows improved architecture routing, but there is still ambiguity between:

- scenic architecture
- city travel atmosphere
- natural landscape with minor structures
- beach/coastal frames that may be better as travel mood than pure nature

### 4. Other Photography is not stable

`Other Photography` is acting as a temporary ambiguity bucket, not a portfolio-usable class.

That is acceptable inside the review system, but it should not survive into final portfolio export without a human mapping decision.

## Photo Portfolio Target Contract

The portfolio repo expects a raw category slug that matches both data and filesystem structure:

- Directory/web path pattern: `/photos/<category>/<filename>`
- Grouping:
  - `branding` -> `portraits`, `product`
  - `events` -> `concert`
  - `author-archive` -> `nature`, `city`, `travel-cityscape`

Current category counts in `src/data/photos.json`:

- `portraits`: `110`
- `concert`: `96`
- `nature`: `58`
- `product`: `58`
- `city`: `39`
- `travel-cityscape`: defined in code but not yet present in current data

## Recommended Taxonomy Strategy

### Keep two different taxonomies on purpose

PhotoCat should keep its review taxonomy because it is useful for model reasoning and inspection. But the export target for Photo Portfolio must be explicit and separate.

Recommended model:

- `review_genre`
  - PhotoCat working label after correction
- `portfolio_category`
  - exact Photo Portfolio slug
- `portfolio_group`
  - derived from `portfolio_category`

Do not assume `review_genre == portfolio_category`.

## Recommended Mapping Contract

### Safe automatic mappings

These can map automatically after manual review confirms the row is correct:

| PhotoCat effective genre | Portfolio category | Notes |
|---|---|---|
| `Events & Music` | `concert` | Strong one-to-one mapping |
| `Food & Product` | `product` | Only when clearly object/food/commercial still or branding detail |
| `Nature & Landscape` | `nature` | Safe when scene is clearly nature-first |

### Mappings that need a second decision layer (Risk of Oversaturation)

These should not be blindly mapped. Forcing these genres into portfolio categories creates noise and dilutes the quality of the final staging site:

| PhotoCat effective genre | Possible portfolio category | Why manual/secondary mapping is needed |
|---|---|---|
| `Branding & Portrait` | `portraits` or `exclude` | Some images are straight portraiture, others are more conceptual/editorial. **Do not force** generic branding. |
| `Street Documentary` | `city` or `exclude` | Some are urban documentary, others are more experimental. Avoid forcing noisy street scenes into `city`. |
| `Travel & Architecture` | `city`, `travel-cityscape` or `exclude` | Architecture-heavy city frames differ from scenic travel atmosphere. If neither fits perfectly, default to `exclude`. |
| `Wedding Photography` | `exclude` (default) or `portraits` | Portfolio repo has no wedding category. **Do not force** wedding shots into portraits unless they are exceptionally strong standalone portraits. |
| `Other Photography` | `exclude` (default) | This bucket is too ambiguous for automatic export. Defaulting to `exclude` prevents random images from saturating portfolio categories. |

### Critical recommendation for Noise Reduction & Exclusion

To maintain the high visual standard of the Photo Portfolio, **exclusion must be a first-class mapping option, not an afterthought.**

1. **Default to Exclude for Missing Genres:** `Wedding Photography` and `Other Photography` should default to `exclude` from portfolio export. Do not auto-map them to `portraits`.
2. **Strict Curation:** Do not use portfolio categories as a dump for ambiguous `Branding & Portrait` or `Street Documentary` shots.
3. **If in doubt, leave it out:** The portfolio benefits more from a tight, coherent selection than from maximizing the total image count.

If needed later, a dedicated portfolio category can be added in the portfolio repo, but that is a business/product decision, not just a PhotoCat classifier decision.

## Recommended New CSV Columns

To support this contract, the corrected CSV should eventually materialize:

- `source_path`
- `relative_input_path`
- `final_genre`
- `user_genre`
- `effective_genre`
- `user_label`
- `portfolio_category`
- `portfolio_group`
- `export_include`
- `dest_relpath`

Minimum requirement:

- `effective_genre` must be written explicitly
- `portfolio_category` must be written explicitly
- `dest_relpath` must be computed from `portfolio_category`

## Categorization Improvement Priorities

### Priority 1. Improve wedding recall

Implementation direction:

- strengthen context-based wedding routing, not only title keyword routing
- add evidence for:
  - formal group portraits
  - suits and dresses in paired/couple/group compositions
  - reception tables, toast, speeches, confetti
  - bouquet, veil, rings, family group structure
- demote `Branding & Portrait` and `Events & Music` more aggressively when wedding context is strong

Expected benefit:

- biggest reduction in manual corrections from this dataset

### Priority 2. Split clean product from contextual documentary/product scenes

Implementation direction:

- keep `Food & Product` for true product/food/still-life work
- route contextual service/market/work scenes toward:
  - `Branding & Portrait`
  - `Street Documentary`
  - `Wedding Photography`
  - `Events & Music`

Expected benefit:

- less category pollution
- better portfolio mapping into `product` vs `portraits`/`city`

### Priority 3. Tighten travel vs nature vs city distinctions

Implementation direction:

- use scene intent:
  - natural landscape first -> `Nature & Landscape`
  - urban structure / monument / facade -> `Travel & Architecture`
  - public-life human activity -> `Street Documentary`
- add export mapping rule:
  - `Travel & Architecture` -> `city` for structure-dominant urban work
  - `Travel & Architecture` -> `travel-cityscape` for scenic travel mood

### Priority 4. Treat Other as a review-only bucket

Implementation direction:

- keep `Other Photography` inside review
- never auto-export `Other Photography` into Photo Portfolio without explicit `portfolio_category`

## Final Recommendation

The correct long-term model is:

1. PhotoCat predicts a review genre.
2. Human review confirms or corrects it.
3. A second portfolio mapping decision creates the exact export category slug.
4. Organize uses the corrected CSV as the only source of truth.

That is the only approach that will let PhotoCat stay useful as a classifier while still producing output that matches the Photo Portfolio repo almost completely.
