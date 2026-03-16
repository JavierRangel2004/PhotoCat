# PhotoCat UI Guide

Local browser-based interface for running the PhotoCat pipeline, reviewing classification results, correcting genres, and organizing photos.

```
python src/ui.py            # http://127.0.0.1:7860
python src/ui.py --browser  # auto-open browser
python src/ui.py --port 8080
```

---

## CSV Format

The UI works with audit CSVs produced by the PhotoCat pipeline. The minimum required column is `filename`. The full set of columns the UI reads:

| Column | Required | Description |
|---|---|---|
| `filename` | Yes | Image file name (e.g. `IMG_1234.jpg`) |
| `final_genre` | No | Model-assigned genre (e.g. `Street Photography`) |
| `review_status` | No | `auto`, `review`, or `title-inferred` |
| `model_1st` | No | Top-1 SigLIP prediction label |
| `model_1st_conf` | No | Top-1 confidence (0-1) |
| `model_2nd` | No | Top-2 SigLIP prediction label |
| `model_2nd_conf` | No | Top-2 confidence (0-1) |
| `rating` | No | Image quality rating (1-5) |
| `title` | No | Generated title |
| `is_blurry` | No | `yes` or `no` |
| `exposure` | No | `normal`, `under`, or `over` |
| `objects_detected` | No | Semicolon-separated YOLO detections |
| `caption` | No | BLIP-generated caption |
| `ocr_text` | No | OCR text found in image |
| `evidence_log` | No | JSON object of evidence fusion boosts |

The pipeline generates this CSV automatically. You can also create a minimal CSV manually with just `filename` and `final_genre` columns to review existing classifications.

### Sample minimal CSV

```csv
filename,final_genre,review_status,model_1st_conf
IMG_1234.jpg,Street Photography,auto,0.92
IMG_1235.jpg,Portrait Photography,review,0.61
IMG_1236.jpg,Nature Photography,title-inferred,0.38
```

---

## Workflows

### 1. Review an existing CSV (no pipeline run)

This is the simplest flow. You already have a `photocat_audit.csv` from a previous pipeline run.

1. Open the **Review Table** tab
2. Enter the **CSV Path** (e.g. `output/full_audit.csv`)
3. Enter the **Image Directory** — the folder containing the actual image files referenced by `filename` in the CSV. If left blank, defaults to the CSV's parent directory.
4. Click **Load CSV**
5. The summary shows image counts by status and genre
6. Use filters to narrow down:
   - **Filter Genre**: show only one genre
   - **Filter Status**: `review` to see images needing human check
   - **Max Confidence**: show only low-confidence images (e.g. below 0.70)
7. Click **Apply Filters**
8. Browse thumbnails in the image grid (if images are found in the directory)
9. Click a thumbnail to jump to the **Image Inspector**

### 2. Correct genres in the Inspector

Genre correction happens exclusively in the **Image Inspector** tab. This ensures you always see the full image and all evidence before making a decision.

1. Load a CSV in the Review Table tab first
2. Click a gallery thumbnail, or use the **Image Inspector** tab directly
3. Use **< Prev** / **Next >** to navigate through filtered images
4. Review the image alongside:
   - BLIP caption
   - YOLO detected objects
   - OCR text
   - SigLIP model scores
   - Evidence fusion log
   - Current review status
5. To change the genre: select from the **Assigned Genre** dropdown
6. To confirm the model was right: click **Confirm Correct** (sets `user_label = correct`)
7. To flag the model was wrong: click **Mark Wrong** (sets `user_label = wrong`)
8. Changes are held in memory and auto-saved to a temp file every 10 corrections

### 3. Export corrected CSV

After reviewing and correcting genres:

1. Go to **Review Table** tab
2. Click **Export Corrected CSV**
3. This writes `<original_name>_corrected.csv` with all original columns plus:
   - `user_genre`: your override (blank if no change)
   - `user_label`: `correct`, `wrong`, or blank
4. The autosave temp file is cleared after successful export

### 4. Preview organize

Before moving files into genre subdirectories:

1. Click **Preview Organize** in the Review Table tab
2. Review the dry-run summary showing:
   - How many images would go into each genre folder
   - How many use your corrected genre vs. the model's
3. Actual file organization is done via the CLI: `python src/main.py --input-dir <dir> --organize`

### 5. Run the full pipeline from the UI

1. Open the **Run Pipeline** tab
2. Set the **Input Directory** to the folder containing your images
3. Configure flags:
   - `--genre-only`: skip blur/exposure/OCR/captioning (faster, SigLIP only)
   - `--recursive`: include subdirectories
   - `--write-xmp`: write XMP sidecar files
   - `--organize`: move files into genre folders after classification
   - `--dry-run`: with organize, just show what would be moved
   - `--no-cache`: force full GPU reprocessing
4. Set **Min Confidence** (default 0.55) and **Workers** (keep at 1 for GPU)
5. Click **Run Pipeline**
6. Watch the live log and progress counter
7. Click **Stop** to cancel mid-run
8. After completion, go to Review Table and load the generated CSV

---

## Image Directory Setup

The UI needs to know two things:
1. **Where the CSV is** (the audit data)
2. **Where the images are** (to show thumbnails and Inspector preview)

Common setups:

| Scenario | CSV Path | Image Directory |
|---|---|---|
| Pipeline output in same dir | `F:/photos/photocat_audit.csv` | _(leave blank — auto-detects)_ |
| CSV in output/, images elsewhere | `output/full_audit.csv` | `F:/photos/lr_export` |
| Organized images | `F:/photos/photocat_audit.csv` | `F:/photos` (genre subdirs inside) |

The `filename` column in the CSV must match the actual file names in the image directory. Paths are resolved as `<image_directory>/<filename>`.

---

## Autosave and Recovery

Corrections (genre overrides and correct/wrong labels) are auto-saved to a temporary JSON file every 10 changes. Location: `%TEMP%/photocat_autosave_<csv_name>.json`

If the app closes unexpectedly, corrections are restored automatically the next time you load the same CSV.

The autosave file is cleared after a successful **Export Corrected CSV**.

---

## Genre Categories

The 10 photography genres used by PhotoCat:

1. Street Photography
2. Music Photography
3. Nature Photography
4. Portrait Photography
5. Product Photography
6. Wedding Photography
7. Architecture Photography
8. Event Photography
9. Sports Photography
10. Other Photography

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Gallery shows no images | Check that **Image Directory** points to the folder containing the actual image files, and that filenames in the CSV match |
| Filter returns 0 rows | Reset filters: set Genre and Status to "All", Max Confidence to 1.0 |
| Inspector shows no image | The file may not exist at the resolved path — check Image Directory |
| Pipeline won't start | Verify the input directory exists and contains supported image files |
| "No module named gradio" | Run `pip install gradio>=4.40.0` |
| Port already in use | Use `--port 8080` or another free port |

---

## Security

The UI runs locally on `127.0.0.1` only. It never exposes files to the network. Do not set `share=True` if you are working with private photos.
