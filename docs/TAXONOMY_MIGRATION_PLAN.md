# PhotoCat Taxonomy Migration Plan
**From: 5-category commercial taxonomy → 6-category JRMGraphy taxonomy + "Other" fallback**
**Date: 2026-03-16 | Branch: claude/photocat-taxonomy-analysis-XTF2r**

---

## 1. Why This Change

The current 5-category taxonomy (`Street`, `Music`, `Nature`, `Portrait`, `Product`) was built for generic classification. After auditing 274 real images from the JRMGraphy catalog, two problems are clear:

### Problem 1 — Category pollution
Street Photography (34.7% of catalog, the biggest bucket) absorbs ~43 architectural/cityscape images that don't belong there. The model has no Architecture/Travel category to route them to, so it defaults to Street. This inflates Street and hides your actual street documentary work.

### Problem 2 — Commercial misalignment
The old labels are archival ("what type of photo is this") not commercial ("what service does this represent"). Clients don't hire a "Portrait photographer" — they hire someone for branding sessions, chef shoots, artist portraits. The taxonomy needs to match how you sell your work.

---

## 2. New Taxonomy (6 primary + 1 fallback)

| New Name | Replaces | Commercial meaning | Portfolio use |
|---|---|---|---|
| `Branding & Portrait` | Portrait Photography | Personal branding, chefs, artists, professionals | PRIMARY commercial offering |
| `Events & Music` | Music Photography | Concert coverage, cultural events, showcases | SECONDARY commercial offering |
| `Street Documentary` | Street Photography | Candid urban moments, real life, market scenes | Supporting / editorial |
| `Food & Product` | Product Photography | Food documentary + commercial still-lifes | Specialist service offering |
| `Nature & Landscape` | Nature Photography | Landscapes, wildlife, nature | AUTORAL line / prints |
| `Travel & Architecture` | (new — split from Street) | Cityscapes, landmarks, travel, architecture | AUTORAL line / editorial |
| `Other Photography` | Other Photography | Doesn't fit any above category with confidence | Strict fallback — never forced |

**Kept as title-fallback only (not primary SigLIP2 class):**
- `Wedding Photography` — only fires on explicit wedding semantic keywords

---

## 3. File-by-File Change Inventory

### 3.1 `src/scene_classifier.py` — SigLIP2 prompts

**What changes:** Replace `GENRE_PROMPTS` dict with 6 new categories + 3 refined prompts each.

**Why prompt quality matters:** SigLIP2 uses contrastive text embeddings. Each prompt is a candidate description the image is scored against. Better prompts = tighter softmax separation = fewer ambiguous scores near the Other gate threshold.

**New prompts design principle:**
- Each prompt specifies WHAT is the main subject (person, building, food, nature)
- Each prompt avoids overlap with adjacent categories
- Each category has one "commercial intent" prompt, one "compositional" prompt, one "context" prompt

```python
GENRE_PROMPTS = {
    "Branding & Portrait": [
        "a portrait or personal branding photograph of a person as the main subject",
        "documentary portrait of a person working, creating, or practicing their craft",
        "close-up or environmental portrait of a creative professional or individual",
    ],
    "Events & Music": [
        "a concert or live music performance photograph with stage lighting",
        "event photography at a cultural gathering, festival, or live show",
        "documentary photograph of a music performance or cultural event",
    ],
    "Street Documentary": [
        "candid street photography of people going about daily life in a public place",
        "documentary photograph of spontaneous real-life moments on a city street or market",
        "unposed photograph of real people in an urban public space or alleyway",
    ],
    "Food & Product": [
        "a food or product photograph showing a meal, dish, or commercial object as the main subject",
        "documentary or commercial photograph focused on food preparation or a product",
        "still-life or editorial food photography with food or objects as the main subject",
    ],
    "Nature & Landscape": [
        "a nature photograph of wildlife, plants, forests, mountains, or natural scenery",
        "landscape photography of a natural outdoor environment without human structures",
        "outdoor nature photograph of animals, flora, geological formations, or ocean",
    ],
    "Travel & Architecture": [
        "an architectural or travel photograph of a building, landmark, or urban structure",
        "cityscape or travel photography featuring monuments, plazas, or historic buildings",
        "photograph of architectural details, facades, skylines, or historic landmarks",
    ],
}
```

---

### 3.2 `src/genre_decision.py` — Evidence fusion engine

**What changes:**
1. All score dict keys renamed to new category names
2. `Travel & Architecture` promoted from a post-hoc score shift to a PRIMARY scored category with its own boosts
3. New `_OTHER_SCORE_GATE` and `_OTHER_MARGIN_GATE` to enforce the fallback
4. `_TITLE_CATEGORY_RULES` updated with new names
5. `Wedding Photography` removed from primary loop (title-fallback only)
6. New `_BRANDING_KEYWORDS` set for Branding & Portrait positive evidence

**Key algorithm additions:**

#### Travel & Architecture as primary (replaces the old shift-only approach)
```python
# Before (old): Architecture was only a demotion of Street
# After (new): Travel & Architecture gets DIRECT positive boosts
_TRAVEL_ARCHITECTURE_OBJECTS = {
    "clock",  # clock towers
}
_TRAVEL_ARCHITECTURE_KEYWORDS = {
    "tower", "clock tower", "clock", "building", "facade", "façade",
    "staircase", "stairs", "archway", "window", "columns", "column",
    "statue", "monument", "hallway", "corridor", "cityscape", "skyline",
    "cathedral", "church", "castle", "bridge", "landmark", "spire",
    "plaza", "square", "gate", "gates", "bell tower",
    # Travel terms now included as primary evidence
    "travel", "city view", "rooftop", "panorama", "aerial",
}
```

#### Other Photography gate
```python
# Applied AFTER all scoring and normalization, BEFORE write policy
_OTHER_SCORE_GATE = 0.30   # if top-1 < this → Other
_OTHER_MARGIN_GATE = 0.10  # if margin < this AND top-1 < 0.50 → Other

if confidence < _OTHER_SCORE_GATE:
    genre = "Other Photography"
    review_status = "review"
    evidence_log["other_gate"] = {"reason": "score_too_low", "max_score": confidence}
elif margin < _OTHER_MARGIN_GATE and confidence < 0.50:
    genre = "Other Photography"
    review_status = "review"
    evidence_log["other_gate"] = {"reason": "margin_too_narrow", "margin": margin}
```

**Why these thresholds:**
- With 5 categories, a clearly-typed image scores 0.75-0.95. With 6 categories, minimum expected for a clear image is ~0.65+.
- Score < 0.30 means all 6 categories scored roughly equally (≈ 0.16 each). No category fits.
- Margin < 0.10 at < 0.50 confidence means the top-2 are nearly tied and neither is confident. Better to leave it as "Other" than guess wrong.

**Cases that WILL be "Other Photography":**
- Fireworks/pyrotechnics (not street, not event, not architecture)
- Industrial ships in fog (not nature, not travel)
- Abstract fine-art minimalist shots
- Aerial/drone city views that aren't architectural detail shots
- Beach couple lifestyle (not portrait, not street, not nature)

#### Branding & Portrait disambiguation from Street Documentary
Key tension: a vendor in a market with a person = Street or Branding?
Rule: if the person is clearly the **subject** (close-up, named, professional context) → Branding & Portrait. If the person is **incidental** to the scene → Street Documentary.

```python
_BRANDING_KEYWORDS = {
    "chef", "barista", "artist", "photographer", "musician",
    "entrepreneur", "creative", "professional", "craftsman", "artisan",
    "tailor", "tattooist", "trainer", "performer", "designer",
    "working", "crafting", "creating", "branding",
}
# Applied as: if BRANDING_KEYWORDS hit + person detected → Branding & Portrait boost
```

---

### 3.3 `src/cli.py` — CATEGORY_DIRS

```python
CATEGORY_DIRS = {
    "Branding & Portrait",
    "Events & Music",
    "Street Documentary",
    "Food & Product",
    "Nature & Landscape",
    "Travel & Architecture",
    "Other Photography",
    "Wedding Photography",   # kept for backward compat + title-fallback
    "Architecture Photography",  # keep old name so recursive scans skip existing folders
    "Music Photography",         # keep old names for backward compat
    "Portrait Photography",
    "Product Photography",
    "Street Photography",
    "Nature Photography",
}
```
**Note:** Old category names are kept in CATEGORY_DIRS so that `collect_images()` skips already-organized folders from previous pipeline runs. This is a one-way backward-compat shim.

---

### 3.4 `src/ui_state.py` — GENRE_CATEGORIES

```python
GENRE_CATEGORIES = [
    "Branding & Portrait",
    "Events & Music",
    "Street Documentary",
    "Food & Product",
    "Nature & Landscape",
    "Travel & Architecture",
    "Other Photography",
    "Wedding Photography",
]
```

---

### 3.5 `src/cache.py` — CACHE_SCHEMA_VERSION bump

```python
CACHE_SCHEMA_VERSION = "2"  # was "1"
```

**Why:** The cache stores `siglip_result["top_k"]` which contains genre label strings. After the GENRE_PROMPTS change, cached top_k entries have old label names. Bumping the version forces all existing cache entries to be treated as misses — the next pipeline run will re-classify with new prompts.

**Impact:** All images processed before this change need one full re-run. This is expected and correct behavior.

---

### 3.6 `tests/test_genre_decision.py` — updated tests

**What changes:**
- `ALL_GENRES` list updated to new 6 categories
- All assertion strings updated
- New tests added for:
  - `test_travel_cityscape_classified_correctly` — clock tower caption → Travel & Architecture
  - `test_other_gate_fires_on_ambiguous_image` — evenly distributed scores → Other Photography
  - `test_branding_portrait_chef_session` — chef + branding keywords → Branding & Portrait
  - `test_events_music_concert_photo` — stage + microphone → Events & Music
  - `test_street_documentary_market_scene` — vendor + people → Street Documentary

---

## 4. Other Photography — Complete Fallback Design

The "Other Photography" category serves as a **quality gate**, not a dump bucket.

### When an image becomes "Other Photography"

| Trigger | Condition | Evidence key |
|---|---|---|
| Score gate | top-1 score < 0.30 after normalization | `other_gate: score_too_low` |
| Margin gate | margin < 0.10 AND top-1 < 0.50 | `other_gate: margin_too_narrow` |
| Title fallback | title/caption keywords match travel/industrial set | `other_boost` (existing) |
| Low-confidence fallback | confidence < MEDIUM_THRESHOLD, no keywords, no caption | `model_top1_fallback` stays as "Other" |

### When an image should NOT become "Other Photography"

- High-confidence images (> 0.80) in any category — these are clear fits
- Images with strong object or keyword evidence — evidence boosts will push score above gate
- Images with people present — person detection as primary subject → Branding or Street Documentary; as secondary → any category is fine

### How "Other Photography" is surfaced in the UI

- `review_status` is always set to `"review"` (never "auto") for Other Photography
- The UI filter panel allows filtering by genre = "Other Photography"
- These images are prime candidates for manual genre correction
- In `--organize` mode, Other Photography images go into an `Other Photography/` subfolder

---

## 5. Impact on Existing Data

### Existing `full_audit_corrected.csv`
- Old genre names still display correctly — `ui_state.py` and `api_bridge.py` pass through whatever strings are in the CSV
- No migration of existing CSV needed
- A re-run of the pipeline will produce a new CSV with new category names

### Existing `.photocat_cache/`
- Cache version bumped to "2" → all entries treated as misses on next run
- Old cache directory can be deleted: `rm -rf <input-dir>/.photocat_cache`

### Existing `XMP sidecars`
- XMP files already written contain old genre names in `Iptc4xmpExt:Genre`
- If you want to update them, re-run with `--write-xmp`

---

## 6. Category Mapping (Old → New)

| Old name | New name | Notes |
|---|---|---|
| Portrait Photography | Branding & Portrait | Broader scope: branding + documentary portrait |
| Music Photography | Events & Music | Broader scope: all live events + concerts |
| Street Photography | Street Documentary | Narrower scope: only human-centric candid urban |
| Product Photography | Food & Product | Split awareness: food documentary + commercial still-lifes |
| Nature Photography | Nature & Landscape | Same scope, clearer name |
| (none) | Travel & Architecture | NEW — extracted from Street Photography contamination |
| Other Photography | Other Photography | Stricter gate — now algorithmically enforced |
| Architecture Photography | merged into Travel & Architecture | No longer separate |
| Wedding Photography | Wedding Photography | Title-fallback only, not in SigLIP2 primary |

---

## 7. Implementation Sequence

Execute in this order (each step depends on the previous):

1. `src/scene_classifier.py` — new GENRE_PROMPTS (defines the 6 output label strings)
2. `src/genre_decision.py` — rename keys + Other gate + Travel primary + branding signals
3. `src/cli.py` — CATEGORY_DIRS (backward-compat names included)
4. `src/ui_state.py` — GENRE_CATEGORIES
5. `src/cache.py` — version bump
6. `tests/test_genre_decision.py` — updated + new test cases
7. Run tests: `python -m pytest tests/`
8. Smoke test: run pipeline on 5–10 test images

---

## 8. Acceptance Criteria

Before considering this migration complete:

- [ ] `python -m pytest tests/` passes all tests (0 failures)
- [ ] Running pipeline on `output/` test images produces categories from new taxonomy only
- [ ] "Travel & Architecture" appears in results for clock tower / cityscape images
- [ ] "Other Photography" appears for fireworks / industrial / abstract shots
- [ ] "Street Documentary" does NOT appear for pure architectural images
- [ ] Cache version "2" is active — old cache entries are treated as misses
- [ ] UI genre filter dropdown shows new category names

---

*This plan reflects the commercial strategy from `docs/CATEGORY_STRATEGY_FINAL.md` and `gptNicheFinal.md`.*
