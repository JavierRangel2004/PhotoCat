# Corrected CSV To Organize Flow Plan

## Objective

Implement a reliable workflow where PhotoCat can:

1. export a full Lightroom set into one working directory
2. run the pipeline without `--organize`
3. generate an audit CSV
4. support manual review in Inspector
5. export a corrected CSV
6. organize files strictly from that corrected CSV
7. map the corrected result into Photo Portfolio-ready category directories

This document focuses on the implementation gaps between the current code and that target flow.

## Evaluated Current State

Based on `gpurun17_03_0949.txt`, `gpurun17_03_0949.csv`, `gpurun17_03_0949_corrected.csv`, and the current Python/Node code:

- The pipeline can already:
  - process a Lightroom export directory
  - write an audit CSV
  - optionally organize immediately
- The review flow can already:
  - load a CSV and image directory
  - apply `user_genre` and `user_label`
  - export a corrected CSV
  - show a text-only organize preview
- The system cannot yet:
  - organize from the corrected CSV
  - use input paths as the organizing source of truth
  - produce Photo Portfolio category slugs directly
  - commit real organize actions from the review flow

## Current Code Constraints

### 1. Organize happens only during the live pipeline run

`src/main.py` writes the audit CSV and then, if `--organize` is set, moves files using the in-memory `genre_result["genre"]`.

Problem:

- this ignores later human corrections unless the organize happened after a second full rerun

### 2. CSV rows only store `filename`

The audit CSV stores `filename`, not the original file path.

Problems:

- duplicate filenames from different folders will collide
- corrected organize cannot safely locate the right source file
- review corrections are keyed by filename only

### 3. Corrected export does not materialize the final organizing decision

The corrected CSV currently keeps:

- `final_genre`
- `user_genre`
- `user_label`

But it does not write:

- `effective_genre`
- `portfolio_category`
- `dest_relpath`

Problem:

- the future organize step still has to infer the real destination instead of reading it directly

### 4. Organize preview is only a count summary

Current preview only counts folders by effective genre.

Problems:

- no per-file preview
- no path preview
- no collision detection
- no missing-file detection
- no manifest for restore

### 5. There is no organize commit endpoint or command for the review flow

The review layer currently exposes:

- load session
- set item genre
- set item label
- export corrected CSV
- organize preview

Problem:

- there is no `organize-from-corrected` execution path

## Target Workflow

This should become the official workflow.

### Phase A. Export from Lightroom

Input:

- one Lightroom export directory containing all selected photos

Requirement:

- keep exported files in a flat or known structure until review is complete
- do not run `--organize` here

### Phase B. Run pipeline without organize

Command behavior:

- run PhotoCat on the Lightroom export
- write a full audit CSV
- include enough path metadata to support later organize

Required output:

- `audit.csv` or equivalent
- each row must represent one exact source file

### Phase C. Manual review in Inspector

Inspector should support:

- approve predicted row
- mark row wrong
- set corrected `user_genre`
- set `portfolio_category` when needed
- exclude row from export if needed

Important:

- review is not only about fixing the genre
- review must also lock the portfolio export decision for ambiguous categories

### Phase D. Export corrected CSV

Corrected CSV becomes the organizing contract.

Required columns:

- `source_path`
- `relative_input_path`
- `filename`
- `final_genre`
- `user_genre`
- `effective_genre`
- `user_label`
- `portfolio_category`
- `portfolio_group`
- `export_include`
- `dest_relpath`

### Phase E. Preview organize from corrected CSV

The system should read the corrected CSV and return:

- per-file source path
- per-file destination path
- portfolio category
- file count per category
- missing files
- duplicate filename collisions
- destination conflicts
- manifest summary

### Phase F. Commit organize from corrected CSV

Commit step should:

- move files according to `dest_relpath`
- move matching XMP sidecars when present
- write a move manifest
- support dry run and real run

### Phase G. Photo Portfolio-ready output

Final output root should match the portfolio repo contract **exactly**. This means no forced or invented categories:

- `/photos/portraits/...`
- `/photos/concert/...`
- `/photos/city/...`
- `/photos/nature/...`
- `/photos/product/...`
- `/photos/travel-cityscape/...`

**Crucially:** Add a path for skipped/excluded files so they do not pollute the final portfolio staging site but are kept for reference:
- `/excluded/<review_genre>/...` (or strictly omit them based on `export_include=False`).

If the workflow also needs `photos.json` generation later, that should be a separate export stage, not mixed into raw organizing.

## Required Implementation Plan

## Step 1. Make audit rows path-safe

Files affected:

- `src/main.py`
- `src/ui_state.py`
- `src/api_bridge.py`
- `apps/backend/src/services/reviewSession.ts`

Required changes:

- add `source_path` to the audit CSV
- add `relative_input_path` to the audit CSV
- use a stable row key based on path, not just basename
- stop keying corrections by `filename` alone

Reason:

- this is the foundation for reliable corrected organize

## Step 2. Materialize corrected organizing columns

Files affected:

- `src/ui_state.py`
- `src/api_bridge.py`
- `shared/types/review.ts`
- frontend review stores and inspector UI

Required changes:

- write `effective_genre` into the corrected CSV
- add `portfolio_category`
- add `export_include`
- derive `portfolio_group`
- compute `dest_relpath`

Recommendation:

- `effective_genre = user_genre if present else final_genre`
- `portfolio_group` derived from `portfolio_category`
- `export_include = True if portfolio_category != 'exclude' else False`
- `dest_relpath = photos/<portfolio_category>/<filename>` (if `export_include` is true)
- (Optional) `dest_relpath = excluded/<effective_genre>/<filename>` (if `export_include` is false, to park files safely without losing them)

## Step 3. Add explicit portfolio mapping logic

Files affected:

- new Python helper module, for example `src/portfolio_mapping.py`
- inspector UI
- corrected export path

Required behavior:

- map safe one-to-one categories automatically
- force explicit review for ambiguous mappings

Recommended rules:

- `Events & Music -> concert`
- `Food & Product -> product`
- `Nature & Landscape -> nature`
- require manual or secondary mapping for:
  - `Branding & Portrait`
  - `Street Documentary`
  - `Travel & Architecture`
  - `Wedding Photography`
  - `Other Photography`

## Step 4. Build preview-from-corrected command

Files affected:

- `src/api_bridge.py`
- possibly a new Python service module such as `src/organize_from_csv.py`
- backend review route/service

New command suggested:

- `organize-from-csv-preview`

Inputs:

- corrected CSV path
- image root
- output root
- mapping profile, for example `photo-portfolio`

Output:

- structured JSON, not plain text

Minimum JSON payload:

- `moves`
- `missing`
- `conflicts`
- `countsByCategory`
- `manifestPathPreview`

## Step 5. Build commit-from-corrected command

Files affected:

- same modules as preview
- backend route layer

New command suggested:

- `organize-from-csv-commit`

Behavior:

- read corrected CSV only
- do not re-run classification
- move files by manifest
- move XMP sidecars
- write manifest JSON or CSV
- return summary payload

## Step 6. Add restore support

If file moves are being committed from review, restore is not optional.

Required behavior:

- every move writes to a manifest
- restore command replays the manifest in reverse

Recommended deliverables:

- `organize_manifest.json`
- `restore-from-manifest` command

## Step 7. Close review-flow UX gaps

Frontend/backend requirements:

- preview must be structured, not a plain summary string
- review UI must show destination category before commit
- actual organize button must remain disabled until:
  - corrected CSV exists
  - preview succeeds
  - no unresolved conflicts remain

## Step 8. Improve the classifier based on corrections

This flow should not only organize correctly. It should also learn from repeated error patterns.

Priority classifier work:

- improve wedding recall
- reduce `Food & Product` overreach
- refine `Travel & Architecture` vs `Nature & Landscape`
- keep `Other Photography` as review-only

## Recommended Command Model

### Existing run

Use the pipeline like this:

```bash
python src/main.py --input-dir <lr_export_dir> --csv <audit_csv>
```

Do not use:

```bash
python src/main.py --input-dir <lr_export_dir> --organize
```

until the corrected-CSV organize path exists.

### New organize flow

Recommended new command family:

```bash
python src/api_bridge.py organize-from-csv-preview --csv-path <corrected_csv> --image-dir <lr_export_dir> --output-dir <portfolio_ready_root> --mapping-profile photo-portfolio
```

```bash
python src/api_bridge.py organize-from-csv-commit --csv-path <corrected_csv> --image-dir <lr_export_dir> --output-dir <portfolio_ready_root> --mapping-profile photo-portfolio
```

## Acceptance Criteria

The flow is complete only when all of the following are true:

- Pipeline can run without organize and produce a path-safe audit CSV.
- Inspector can save corrections plus portfolio mapping decisions.
- Corrected CSV contains a materialized organizing contract.
- Preview shows exact source and destination paths.
- Commit organizes strictly from corrected CSV, not from fresh inference.
- Output directories match Photo Portfolio category slugs.
- A manifest exists for restore.
- Duplicate filenames no longer break review or organize.

## Recommended Delivery Order

1. Path-safe CSV contract.
2. Corrected CSV materialization with `effective_genre`.
3. Portfolio category mapping field and inspector support.
4. Structured preview from corrected CSV.
5. Commit organize from corrected CSV.
6. Manifest restore.
7. Taxonomy tuning using repeated review corrections.

This order keeps the implementation aligned with the real workflow: review first, organize second, portfolio export third.
