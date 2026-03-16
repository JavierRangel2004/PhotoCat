# PhotoCat UI Plan

A desktop GUI that wraps the existing pipeline, making it easy to run, review, and correct classification results before committing any file moves.

---

## Goals

1. Select input directory and configure run flags visually.
2. Trigger pipeline runs and watch live progress.
3. Browse the audit CSV output — filtered, sorted, grouped by genre.
4. Inspect each image with its full metrics (path, rating, blur, exposure, YOLO objects, BLIP caption, OCR, SigLIP scores, evidence log).
5. Override the assigned genre per-image, then export a corrected CSV or commit `--organize`.
6. Feed corrections back into a labeled dataset for future classifier improvement.

---

## Technology Choice

**Gradio** (Python, local server, browser UI)

| Option | Why Gradio wins |
|---|---|
| Gradio | Zero JS, pure Python, ships as `pip install gradio`, file browser component, image viewer, dataframe editor, runs locally on `localhost:7860` |
| Tkinter | No image grid, painful layout, hard to iterate |
| PyQt6 | Heavyweight, compiled, harder to ship |
| Streamlit | Good but no editable dataframe cells without extra hacks |
| Electron | Requires Node, too large for this scope |

Gradio 4.x has:
- `gr.FileExplorer` — directory picker
- `gr.Image` — image viewer
- `gr.Dataframe` — editable table (user can type corrected genre inline)
- `gr.CheckboxGroup` / `gr.Dropdown` — flag selectors
- `gr.Textbox(lines=10)` — live log streaming via `gr.update`
- `gr.Gallery` — image strip with captions

---

## Screen Layout (3 Tabs)

```
┌─────────────────────────────────────────────────────────────┐
│  PhotoCat                                    [Run] [Restore] │
├──────────┬──────────┬───────────────────────────────────────┤
│  Tab 1   │  Tab 2   │  Tab 3                                │
│  Run     │  Review  │  Image Inspector                      │
└──────────┴──────────┴───────────────────────────────────────┘
```

---

## Tab 1 — Run Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  Input Directory    [Browse…]  /path/to/photos              │
│  CSV Output         [Browse…]  output/audit.csv             │
│                                                             │
│  ┌── Pipeline Flags ──────────────────────────────────────┐ │
│  │ [ ] --recursive        [ ] --write-xmp                 │ │
│  │ [ ] --genre-only       [ ] --no-cache                  │ │
│  │ [ ] --organize         [ ] --dry-run                   │ │
│  │                                                         │ │
│  │ Min confidence  [0.55 ▼]   Workers [1 ▼]               │ │
│  │ Extensions      [.jpg,.jpeg,.png,.tiff,.webp,.cr2,.dng] │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [▶ Run Pipeline]          [⏹ Stop]                        │
│                                                             │
│  ┌── Live Log ────────────────────────────────────────────┐ │
│  │ [1/274] Processing test2024-001.jpg                    │ │
│  │   Genre: Nature Photography (conf=0.77, status=review) │ │
│  │ ...                                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Progress: ████████░░░░ 142/274   Cache: 141 hits, 1 miss  │
└─────────────────────────────────────────────────────────────┘
```

### Fields

| Field | Component | Notes |
|---|---|---|
| Input directory | `gr.Textbox` + folder button | Validated on change |
| CSV output path | `gr.Textbox` | Default: `<input_dir>/photocat_audit.csv` |
| Pipeline flags | `gr.CheckboxGroup` | Maps to CLI flags |
| Min confidence | `gr.Slider(0.3, 0.95)` | Maps to `--min-confidence` |
| Workers | `gr.Dropdown([1,2,4])` | Warning shown if > 1 (disables cache) |
| Extensions | `gr.Textbox` | Comma-separated |
| Run/Stop | `gr.Button` | Run calls subprocess, Stop sends SIGTERM |
| Live log | `gr.Textbox(lines=20)` | Streamed via `subprocess.Popen` generator |
| Progress bar | `gr.Progress` / `gr.HTML` | Parsed from log lines `[N/M]` |

---

## Tab 2 — Review Table

```
┌─────────────────────────────────────────────────────────────┐
│  CSV:  output/audit.csv          [Load CSV]  [Load Images]  │
│                                                             │
│  Filter: Genre [All ▼]   Status [All ▼]   Conf < [0.80 ▼]  │
│  Sort by: [Confidence ▼] [↓ Desc]                          │
│                                                             │
│  ┌─ Summary ────────────────────────────────────────────┐  │
│  │ 274 images  |  183 auto  |  79 review  |  12 inferred │  │
│  │ Street 95 · Portrait 59 · Product 56 · Nature 34 ...  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Image Grid (filtered) ───────────────────────────────┐  │
│  │ [thumb] [thumb] [thumb] [thumb] [thumb] [thumb] ...   │  │
│  │  auto    review  review  auto    review  auto          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ Editable Table ──────────────────────────────────────┐  │
│  │ # │ File          │ Status   │ Genre (editable) │ Conf │  │
│  │ 1 │ test001.jpg   │ auto     │ Street Photog…   │ 0.82 │  │
│  │ 2 │ test003.jpg   │ review   │ [Street ▼]       │ 0.52 │  │
│  │ 3 │ test040.jpg   │ inferred │ [Architect… ▼]   │ 0.45 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  [✓ Export Corrected CSV]   [▶ Organize (corrected)]       │
│  [Mark Selected → Correct]  [Mark Selected → Wrong]        │
└─────────────────────────────────────────────────────────────┘
```

### Features

| Feature | Detail |
|---|---|
| Load CSV | Reads `full_audit.csv`, populates table and gallery |
| Filter by genre | Dropdown of all genres found in CSV |
| Filter by status | `auto` / `review` / `title-inferred` |
| Filter by confidence | Slider — show only rows below threshold |
| Image grid | `gr.Gallery` of thumbnails (click opens Inspector) |
| Editable genre column | `gr.Dataframe(col_count=...)` with genre dropdown per row |
| Mark correct/wrong | Checkbox selection + bulk-mark button, stored in `user_label` column |
| Export corrected CSV | Writes `full_audit_corrected.csv` with `user_genre` and `user_label` columns |
| Organize (corrected) | Calls `_organize_into_dirs` with corrected genre map instead of model genre |

---

## Tab 3 — Image Inspector

```
┌────────────────────────────────────────┬────────────────────┐
│                                        │ File               │
│                                        │ /full/path/to/img  │
│                                        ├────────────────────┤
│         [Image Preview]                │ Rating      ★★★☆☆  │
│         1600×1067 px                   │ Blur        no     │
│                                        │ Exposure    normal │
│                                        ├────────────────────┤
│                                        │ BLIP Caption       │
│                                        │ "A clock tower     │
│                                        │  in the city..."   │
│                                        ├────────────────────┤
│                                        │ YOLO Objects       │
│                                        │ potted plant       │
│                                        ├────────────────────┤
│                                        │ OCR Text           │
│                                        │ (none)             │
│                                        ├────────────────────┤
│                                        │ SigLIP Scores      │
│                                        │ Street     0.518   │
│                                        │ Nature     0.480   │
│                                        │ Portrait   0.002   │
│                                        ├────────────────────┤
│                                        │ Evidence Log       │
│                                        │ nature_boost: 0.12 │
│                                        │ street_boost: 0.12 │
│                                        ├────────────────────┤
│                                        │ Assigned Genre     │
│                                        │ [Street Photog ▼]  │
│                                        │                    │
│                                        │ [✓ Confirm]        │
│                                        │ [✗ Mark Wrong]     │
│ [← Prev]  3 / 12 (review filter)  [→ Next]                 │
└────────────────────────────────────────┴────────────────────┘
```

### Fields shown per image

| Field | Source |
|---|---|
| Full path | `img_path` from CSV |
| Dimensions | Read from file at load time |
| Rating | `rating` column |
| Blur | `is_blurry` column |
| Exposure | `exposure` column |
| BLIP Caption | `caption` column |
| YOLO Objects | `objects_detected` column (semicolon-separated) |
| OCR Text | `ocr_text` column |
| SigLIP scores | Parsed from `model_1st`, `model_1st_conf`, `model_2nd`, `model_2nd_conf` |
| Evidence log | `evidence_log` column (JSON → formatted key: value list) |
| Assigned Genre | Editable `gr.Dropdown` of all 10 taxonomy categories |
| Confirm / Wrong | Sets `user_genre` / `user_label` in the in-memory dataframe |
| Prev / Next | Navigates within current filter set (review-only, genre-filtered, etc.) |

---

## Data Flow

```
pipeline run
    └─→ output/full_audit.csv
            └─→ Tab 2: load into DataFrame (in memory)
                    ├─→ Tab 3: inspector reads single row by index
                    │        └─→ user edits genre → writes back to in-memory DataFrame
                    └─→ Tab 2: Export corrected CSV
                                    └─→ output/full_audit_corrected.csv
                                            └─→ _organize_into_dirs() with corrected genres
```

Corrections are held in two new columns appended to the in-memory DataFrame:

| Column | Type | Values |
|---|---|---|
| `user_genre` | str | One of 10 taxonomy labels, or `""` (no override) |
| `user_label` | str | `"correct"` / `"wrong"` / `""` |

The corrected CSV preserves all original columns and appends these two. This file can later be used to build a labeled training dataset for classifier improvement.

---

## Implementation Phases

### Phase A — Scaffold (no pipeline integration)
- `src/ui.py` entry point: `python src/ui.py`
- 3-tab Gradio layout, all components wired up
- CSV load → DataFrame display
- Image inspector navigation from static CSV
- Corrected CSV export

**Deliverable:** Fully functional review/correction UI from any existing audit CSV.

### Phase B — Pipeline integration
- Tab 1 "Run" streams subprocess output line-by-line via `subprocess.Popen`
- Progress bar parsed from `[N/M]` tokens in log
- On completion: auto-load the generated CSV into Tab 2
- Stop button sends `process.terminate()`

**Deliverable:** Full end-to-end run-and-review loop from the UI.

### Phase C — Organize from UI
- "Organize (corrected)" button in Tab 2
- Applies `user_genre` overrides where set, falls back to `final_genre`
- Shows dry-run preview before actual move
- Calls restore logic if re-organizing after a previous run

**Deliverable:** No CLI needed for the full workflow.

### Phase D — Dataset export (future)
- "Export training data" button
- Copies images labeled `"correct"` to `datasets/genre/train/<genre>/`
- Ready for fine-tuning a lightweight classifier on top of SigLIP2 embeddings

---

## File Structure

```
src/
  ui.py              ← Gradio app entry point
  ui_state.py        ← In-memory DataFrame state, genre correction helpers
  ui_runner.py       ← Subprocess runner, log stream generator
```

No changes to existing pipeline modules. The UI is a pure wrapper.

---

## Dependencies

```
gradio>=4.40.0       # pip install gradio
Pillow               # already required by pipeline
```

No additional GPU or model dependencies. The UI only reads CSV and image files; all heavy inference stays in the existing pipeline.

---

## Launch Command

```bash
python src/ui.py
# → Gradio running on http://127.0.0.1:7860
```

Or with auto-launch:

```bash
python src/ui.py --browser
```

---

## Open Questions / Decisions Needed

| Question | Options | Recommendation |
|---|---|---|
| Image loading performance | Thumbnails on demand vs. preload all | Load on demand; cache last 20 thumbs |
| Genre dropdown per table row | Editable cell vs. separate dropdown | Separate dropdown in Inspector (cleaner) |
| Persist corrections across sessions | Write to CSV on every change vs. export only | Export only (simpler, explicit) |
| Auto-load CSV after run | Yes / No | Yes, on run completion |
| Dark mode | Default Gradio theme / custom | Default OK for now |
