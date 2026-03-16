# PhotoCat Implementation Roadmap

Centralized plan combining the two `.cursor/plans/` proposals with current implementation status and audit findings.

**Source plans:**
- `.cursor/plans/parallel_gpu_batch_processing_37a95d02.plan.md` — Batch GPU inference
- `.cursor/plans/cache_repetitive_image_results_1e46f6af.plan.md` — Result caching for re-runs

**Goal:** Export Lightroom-selected photos, run PhotoCat, and get them sorted into portfolio-ready category directories with minimal errors.

---

## Current Implementation Status

### What IS implemented (Phase 1 — taxonomy + core pipeline)

| Module | Status | Notes |
|--------|--------|-------|
| `src/cli.py` | Done | `--input-dir`, `--recursive`, `--extensions`, `--write-xmp`, `--genre-only`, `--min-confidence`, `--workers`, `--organize`, `--csv` |
| `src/scene_classifier.py` | Done | SigLIP2 zero-shot with 3-prompt ensemble per genre, model loaded once |
| `src/genre_decision.py` | Done | Evidence fusion (YOLO+BLIP+SigLIP2+OCR), boost/demote rules, margin gating, title-fallback, 10 taxonomy categories |
| `src/object_detection.py` | Done | YOLO loaded once at module level (fixed per-call bottleneck) |
| `src/main.py` | Done | Sequential pipeline, CSV audit, `--organize` moves files into genre dirs |
| `src/metadata_writer.py` | Done | XMP sidecar writing with genre tag and review status |
| `src/image_captioning.py` | Done | BLIP captioning |
| `src/device.py` | Done | CUDA/MPS/CPU auto-detection |
| `src/restore.py` | Done | Moves photos back from genre subdirs to root; `--dry-run` preview |

### What is NOT implemented

| Feature | Plan Reference | Status |
|---------|---------------|--------|
| `--batch-size` CLI arg | Batch GPU plan | Not started |
| `detect_objects_batch()` | Batch GPU plan | Not started |
| `caption_images_batch()` | Batch GPU plan | Not started |
| `classify_scene_batch()` | Batch GPU plan | Not started |
| Batch orchestration in `main.py` | Batch GPU plan | Not started |
| `src/cache.py` (SQLite cache) | Cache plan | **Done** ✓ |
| `--no-cache` / `--cache-dir` CLI args | Cache plan | **Done** ✓ |
| Cache-aware pipeline in `main.py` | Cache plan | **Done** ✓ |

---

## Phase 2: Result Caching — COMPLETE ✓

**Implemented:** `src/cache.py` (new), `src/cli.py` (`--no-cache`, `--cache-dir`), `src/main.py` (cache init, hit/miss logic, stats reporting).

**How it works:**
- On first run: full GPU pipeline executes, results written to `{input_dir}/.photocat_cache/cache.db`
- On re-run: cache hit skips load + all models, only `make_genre_decision()` re-executes (< 1ms per image)
- Invalidation: file mtime or size changes → miss. `CACHE_SCHEMA_VERSION` bump → all entries invalid.
- Multi-worker: cache is disabled automatically with a warning when `--workers > 1`
- CLI: `--no-cache` forces full reprocess; `--cache-dir PATH` moves DB location

**Status reported at end of run:** `Cache: N hits, M misses`

---

## Phase 2: Result Caching (Priority: HIGH)

**Why first:** Re-runs after tuning `genre_decision.py` currently reprocess all images through GPU. This is the biggest time waste when iterating on classification quality. Caching deterministic model outputs (YOLO, BLIP, SigLIP, blur, exposure, OCR, rating, tags, title) and only recomputing `make_genre_decision()` makes re-runs near-instant.

### 2.1 New module: `src/cache.py`

- SQLite DB at `{input_dir}/.photocat_cache/cache.db`
- Table: `path` (TEXT PK), `mtime` (REAL), `size` (INT), `cache_version` (TEXT), `payload` (TEXT/JSON)
- API: `get(path, mtime, size) -> dict | None`, `set(path, mtime, size, payload)`
- `CACHE_SCHEMA_VERSION = "1"` — bump when fields or models change

### 2.2 Cache payload (per image)

```json
{
  "objects_detected": ["person", "car"],
  "caption": "Two people on a street.",
  "siglip_result": {
    "genre_label": "Street Photography",
    "confidence": 0.85,
    "top_k": [["Street Photography", 0.85], ...],
    "supporting_evidence": { ... }
  },
  "ocr_result": "",
  "is_blurry": false,
  "exposure": "normal",
  "rating": 4,
  "tags": ["person", "car", "street"],
  "title": "Two people on a street."
}
```

For `--genre-only`: payload is `{"siglip_result": {...}}` only.

### 2.3 CLI changes

- Add `--no-cache` flag (force full reprocess)
- Add `--cache-dir PATH` (default: `{input_dir}/.photocat_cache`)

### 2.4 Pipeline integration

- Before processing: stat file, check cache. On hit → load payload, run only `make_genre_decision()`, return result.
- After full pipeline (cache miss): write cache entry.
- Cache invalidation: mtime + size + cache_version mismatch = miss.

### 2.5 File changes

| File | Change |
|------|--------|
| New: `src/cache.py` | SQLite backend |
| `src/cli.py` | `--no-cache`, `--cache-dir` |
| `src/main.py` | Cache check before GPU, cache write after GPU |

---

## Phase 3: Batch GPU Processing (Priority: MEDIUM)

**Why second:** Only matters for first-run performance on large exports (500+ images). Caching eliminates re-run cost, so batch processing is an optimization for initial processing only.

### 3.1 CLI

- Add `--batch-size INT` (default 1). Values > 1 enable batched inference. Recommend 4-16 for 8GB VRAM.

### 3.2 Batch APIs

| Module | New method | Notes |
|--------|-----------|-------|
| `src/object_detection.py` | `detect_objects_batch(images, conf)` | YOLO accepts list of images natively |
| `src/image_captioning.py` | `caption_images_batch(images)` | BLIP batch with sequential fallback on OOM |
| `src/scene_classifier.py` | `classify_scene_batch(images)` | HF pipeline accepts multiple images |

### 3.3 Main pipeline batch loop

- Chunk `image_files` into batches of `batch_size`
- Per chunk: load + preprocess all → GPU batch (YOLO → BLIP → SigLIP) → per-image CPU steps → result tuples
- Failed loads: skip in GPU batch, produce skipped result
- OOM: retry chunk with halved batch size or fall back to sequential
- Cache-aware: resolve cache per image first, only uncached images go into batch

### 3.4 Constraints

- Single GPU only, single process (`workers=1` for GPU)
- `batch_size=1` or CPU = existing sequential behavior (backward compatible)
- `--genre-only` + batch = only SigLIP batched

### 3.5 File changes

| File | Change |
|------|--------|
| `src/cli.py` | `--batch-size` |
| `src/object_detection.py` | `detect_objects_batch()` |
| `src/image_captioning.py` | `caption_images_batch()` |
| `src/scene_classifier.py` | `classify_scene_batch()` |
| `src/main.py` | `run_batch_pipeline()`, chunk logic, cache+batch integration |

---

## Phase 4: Classification Quality Improvements — IN PROGRESS

### Changes made

| Change | File | Result |
|--------|------|--------|
| Lowered `MEDIUM_THRESHOLD` 0.55 → 0.50 | `genre_decision.py` | Fewer images fall to title-inferred |
| Model top-1 fallback when no caption/title | `genre_decision.py` | 28 "Other Photography" → real genre with "review" |

**Before:** 165 auto / ~50 review / 28 "Other Photography" / ~31 title-inferred
**After:** 165 auto / 109 review / **0 "Other Photography"**

All 28 previously-"Other" images now have a model-backed genre assignment with `review` status (human check before `--organize`).

---

## Phase 4: Classification Quality Improvements (Priority: HIGH — after Phase 2)

Based on the V2 audit analysis below, these are the concrete accuracy improvements needed before trusting `--organize` for portfolio use.

### 4.1 Known misclassification patterns (from V2 audit)

| Problem | Examples | Root cause | Fix |
|---------|----------|-----------|-----|
| Moon/sky → Product Photography | test2024-158 | SigLIP2 sees isolated round object | Add nature caption check for "moon", "sky", "star" in Product→Nature contradiction |
| Shark/marine life → Product Photography | test2024-059 | Black background triggers "studio shot" | Strengthen `_NATURE_CAPTION_WORDS` check, add "shark" to nature objects |
| Architecture buildings → split Street/Nature ~50/50 | test2024-003,008,028,037-040,050 | SigLIP2 can't distinguish architecture from street | Add "Architecture Photography" as primary SigLIP2 genre (not just title-fallback) |
| Wedding photos → scattered categories | test2024-084,219-261 | Wedding not a primary category | Consider adding "Wedding Photography" as primary or improving title-fallback coverage |
| Cosplay/costume portraits → Music Photography | test2024-121-135 | Stage-like setting confuses Music prompts | Add costume/cosplay keywords to Portrait boosts |
| Jewelry/rings → Portrait Photography | test2024-180-182 | SigLIP2 sees dark background as portrait | Add "ring", "necklace", "chain", "jewelry" to Product object/keyword sets |
| Low-confidence title-inferred → "Other Photography" | test2024-187,200,222,264,266,273 | No title keyword match | Expand `_TITLE_CATEGORY_RULES` or add broader fallback patterns |
| Fireworks → Music Photography | test2024-157 | Stage lighting similarity | Add "firework" to Event Photography title-fallback |

### 4.2 Taxonomy expansion candidates

Current primary (SigLIP2): Street, Music, Nature, Portrait, Product (5 genres)

Title-fallback only: Wedding, Architecture, Event, Sports, Other

**Recommended for promotion to primary SigLIP2 genres:**
- Architecture Photography — high confusion between Street/Nature for building-dominant scenes
- Event Photography — costume/festival/parade images don't fit Music or Portrait

**Keep as title-fallback only:**
- Wedding Photography — too similar to Portrait for zero-shot discrimination
- Sports Photography — too few examples in current dataset

### 4.3 Color/mood signal improvements

Currently `detect_mood()` and `extract_top_colors()` produce tags but are NOT used in genre decision. Adding color signals could help:
- Dark/dramatic + stage lighting = Music boost
- Bright/natural + green dominant = Nature boost
- White/clean background = Product boost
- Warm tones + outdoor = Portrait/Nature disambiguation

### 4.4 Confidence calibration

Current thresholds from V2 audit:
- Too many images at exactly 0.50xx confidence → title-inferred fallback
- The 0.55 MEDIUM threshold catches genuine ambiguity but also catches images where SigLIP2 is simply uncertain between two valid options

**Proposed:** Lower MEDIUM_THRESHOLD from 0.55 to 0.50 only if the top-1 vs top-2 margin > 0.10 (the model has a clear preference even at low absolute confidence).

---

## V2 Audit Results (274 test images — `output/photocat_auditV2.csv`)

### Status distribution

| Status | Count | % |
|--------|-------|---|
| auto | ~170 | 62% |
| review | ~50 | 18% |
| title-inferred | ~54 | 20% |

### Genre distribution (final assigned genre)

| Genre | Count | Notes |
|-------|-------|-------|
| Street Photography | ~95 | Dominant — many building/architecture images routed here |
| Portrait Photography | ~65 | Includes wedding portraits, cosplay |
| Product Photography | ~55 | Includes beverage cans, rings, also some marine life errors |
| Nature Photography | ~30 | Correct for landscapes, wildlife |
| Music Photography | ~18 | Correct for concerts, some wedding dancing errors |
| Architecture Photography | ~8 | All via title-inferred fallback |
| Wedding Photography | ~2 | Only via title-inferred when "bride"/"groom" in title |
| Event Photography | ~2 | Cosplay/costume via title-inferred |
| Other Photography | ~7 | Catch-all when no title keywords match |
| Sports Photography | ~1 | Rare |

### Key error patterns

1. **Product Photography over-captures marine life**: Shark (059), seahorse-area images where dark/isolated backgrounds trigger product prompts. Fix: strengthen nature caption contradiction check.

2. **Architecture split**: 8+ buildings with clock towers split ~50/50 between Street and Nature, falling to title-inferred "Architecture Photography". Fix: add Architecture as primary genre.

3. **Wedding scatter**: 40+ wedding images spread across Portrait (majority), Nature (outdoor ceremony), Product (table settings), Music (dancing/reception). This is expected given wedding isn't primary, but some misclassifications hurt (e.g., wedding dinner → Product).

4. **Low-confidence title-inferred → "Other"**: 7 images where both model confidence and title keywords fail. These need manual review or expanded keyword sets.

5. **Moon → Product**: test2024-158 confidently (0.9964) classified as Product. The isolated bright circle on dark background matches product studio aesthetics. Need explicit moon/celestial contradiction rule.

### Genre review dataset accuracy (362 labeled images — `output/genre_review.csv`)

This uses the OLD taxonomy (Concert/Portraits instead of Music/Portrait). Approximate per-class:

| True label | Total | Correct | Accuracy | Main confusion |
|-----------|-------|---------|----------|----------------|
| Street Photography | 40 | ~35 | ~87% | → Portrait (person-heavy scenes) |
| Concert Photography | 96 | ~93 | ~97% | Near-perfect |
| Nature Photography | 58 | ~47 | ~81% | → Portrait (people in nature) |
| Portraits Photography | 110 | ~92 | ~84% | → Product, Concert, Street |
| Product Photography | 58 | ~48 | ~83% | → Street (outdoor product shots), Nature |

**Overall weighted accuracy: ~88%**
**Target for portfolio use: 93%+** (reduce manual sorting to < 10% of images)

---

## Execution Order

```
Phase 2: Cache (fast re-runs)          ← DO FIRST — enables rapid iteration
   ↓
Phase 4: Quality tuning                ← iterate on genre_decision.py with cached re-runs
   ↓
Phase 3: Batch GPU                     ← optimize first-run throughput
```

### Workflow for Lightroom exports

After all phases:

```bash
# 1. Export selected photos from Lightroom to a directory
# 2. First run (full GPU processing + cache write)
python src/main.py --input-dir "D:/LR_Export/2024" --recursive --genre-only --csv output/audit.csv

# 3. Review audit.csv, tune genre_decision.py if needed
# 4. Re-run (cache hit — only genre recomputed, near-instant)
python src/main.py --input-dir "D:/LR_Export/2024" --recursive --genre-only --csv output/audit.csv

# 5. When satisfied, organize into portfolio directories
python src/main.py --input-dir "D:/LR_Export/2024" --recursive --genre-only --organize

# 6. Copy genre directories to portfolio website
```

---

## Testing checklist

- [x] Cache: first run creates `.photocat_cache/cache.db`; second run is < 5s for 274 images
- [x] Cache: changing `genre_decision.py` constants produces different genre results on cache hit
- [x] Cache: `--no-cache` forces full reprocess
- [x] Cache: modifying an image file (touch/replace) causes cache miss for that image only
- [ ] Batch: `--batch-size 1` matches sequential behavior exactly
- [ ] Batch: `--batch-size 8` on GPU produces same results, lower total time
- [ ] Quality: moon/celestial → Nature Photography, not Product
- [ ] Quality: marine life on dark background → Nature Photography, not Product
- [ ] Quality: overall accuracy on genre_review.csv reaches 93%+
- [ ] Organize: `--organize` creates correct directories, moves files + XMP sidecars
- [ ] Organize: re-running on organized dirs skips category subdirectories
