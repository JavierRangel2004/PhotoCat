# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

### Python pipeline

```bash
# Activate venv first
source venv/bin/activate  # Windows: venv\Scripts\activate

# Genre-only classification (fastest)
python src/main.py --input-dir /path/to/photos --genre-only

# Full pipeline with XMP writing and file organization
python src/main.py --input-dir /path/to/photos --write-xmp --organize

# Dry-run organization (preview moves without acting)
python src/main.py --input-dir /path/to/photos --organize --dry-run

# Gradio review UI
python src/ui.py
```

### Node workspace

```bash
npm install                # from repo root (installs both workspaces)
npm run dev                # starts backend + frontend together
npm run dev:backend        # Fastify bridge only (127.0.0.1:8797)
npm run dev:desktop        # Svelte/Vite frontend only (localhost:4173)
npm run typecheck          # TypeScript checks for both workspaces
```

### Python dependencies

```bash
pip install -r requirements.txt
# Optional CUDA:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

## Architecture

PhotoCat is a hybrid Python + Node system. The hard boundary: **all ML/photo processing stays in Python; Node is only the UI and bridge layer**.

### Python layer (`src/`)

The processing pipeline flows through `src/main.py`:
1. Image loading and preprocessing (`image_analysis.py`)
2. Blur/exposure quality checks (`image_analysis.py`)
3. YOLO object detection (`object_detection.py`) — loaded via `detect_objects()`
4. OCR via Tesseract (`main.py:ocr_text()`)
5. BLIP captioning (`image_captioning.py` — `ImageCaptioner` class, lazy singleton)
6. SigLIP2 zero-shot genre classification (`scene_classifier.py` — `SceneClassifier` class, lazy singleton)
7. Evidence fusion and confidence-gated write policy (`genre_decision.py` — `make_genre_decision()`)
8. Rating, tags, title generation (`main.py`)
9. XMP sidecar writing (`metadata_writer.py`)
10. Audit CSV output and optional file organization into genre subdirectories

Key design decisions:
- Models are lazy singletons (`_get_captioner()`, `_get_scene_clf()`) to avoid loading multi-GB models in every Windows spawn worker
- `scene_classifier.py` uses a 3-prompt-per-genre ensemble averaged to produce genre scores
- `genre_decision.py` fuses SigLIP2 scores with YOLO object cues, caption keywords, and OCR text via boost/demote rules, then applies confidence thresholds (HIGH >= 0.80 auto-write, MEDIUM 0.50-0.79 needs review, LOW < 0.50 title-inferred fallback)
- Cache layer (`cache.py` — SQLite-backed `ImageCache`) skips GPU work on cache hits; disabled for multi-worker runs
- `cli.py` defines `CATEGORY_DIRS` set which `collect_images()` skips to avoid re-processing organized folders

### Node layer (`apps/`)

- `apps/backend/` — Fastify server (`@photocat/backend`) bridges frontend requests to Python via `pythonBridge.ts`
  - `pythonBridge.ts:execPythonJson()` calls `src/api_bridge.py` subcommands (load-session, export-corrected, organize-preview)
  - `pythonBridge.ts:spawnPipeline()` spawns `src/main.py` as a child process for live pipeline runs
  - `pipelineManager.ts` manages pipeline lifecycle and SSE streaming of logs to frontend
  - `reviewSession.ts` wraps review session state
- `apps/desktop/` — Svelte 5 + Vite frontend (`@photocat/desktop`)
  - Features: `features/dashboard/`, `features/inspector/`, `features/pipeline/`, `features/session/`
  - Stores: `lib/stores/app.ts`, `lib/stores/review.ts`, `lib/stores/pipeline.ts`
  - API client: `lib/api.ts`
- `shared/types/` — TypeScript types shared between backend and desktop (ReviewItem, ReviewSession, PipelineRunRequest, PipelineStatus)

### Python bridge contract (`src/api_bridge.py`)

The bridge exposes `UIState` (from `ui_state.py`) operations as JSON CLI subcommands:
- `load-session --csv-path --image-dir` — returns full session payload with items, summary, genres, statuses
- `export-corrected --csv-path --image-dir --corrections-path --output-path` — exports corrected CSV
- `organize-preview --csv-path --image-dir --corrections-path` — returns move preview

### Genre taxonomy (Phase 2)

6 primary categories + 2 fallback/special:
- Branding & Portrait, Events & Music, Street Documentary, Food & Product, Nature & Landscape, Travel & Architecture
- Other Photography (algorithmic fallback when confidence is too low)
- Wedding Photography (title-inferred fallback only, not in SigLIP2 primary classification)

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `PHOTOCAT_BACKEND_HOST` | `127.0.0.1` | Fastify host |
| `PHOTOCAT_BACKEND_PORT` | `8797` | Fastify port |
| `VITE_PHOTOCAT_API_BASE_URL` | `http://127.0.0.1:8797` | Frontend API base URL |
| `PHOTOCAT_PYTHON_CMD` | `python` | Python executable used by the bridge |

## Ruflo Workflow (Non-Negotiable for Feature Work)

This repository uses a Ruflo-first workflow for non-trivial work. "Ruflo" means the Claude Flow V3 + RuVector + agent swarm stack configured in `.mcp.json`, `.claude/`, and `.claude-flow/`.

### Rules

1. Do not start feature work in direct single-agent coding mode.
2. Do not use `claude-flow claude spawn` for implementation.
3. The top-level assistant acts as the operator and coordinator, not the primary coder.
4. All feature work goes through agents and swarm orchestration: research -> architecture -> implementation -> testing -> review -> documentation.
5. Before code changes, store the task goal, constraints, and model decision in Claude Flow memory.
6. Prefer `npx @claude-flow/cli@latest ...` over ad hoc custom wrappers.

### Execution

```bash
# 1. Validate
npx @claude-flow/cli@latest doctor --fix
npx @claude-flow/cli@latest memory init --force
npx @claude-flow/cli@latest swarm init --topology hierarchical --max-agents 7 --strategy specialized

# 2. Store task context
npx @claude-flow/cli@latest memory store --key "photocat/goal" --value "..." --namespace project

# 3. Run agent phases in order
# planner/researcher -> system-architect -> coder -> tester -> reviewer -> api-docs
```

### Required checkpoints

1. **Research** — save model choice, fallback models, and reasons in memory
2. **Architecture** — save module plan and CLI contract in memory
3. **Evaluation** — save per-class metrics before enabling automatic XMP writes

### Anti-drift guardrails

- No coding until research and architecture outputs exist
- No replacing the whole pipeline with a large VLM by default
- No writing genre metadata automatically until confidence thresholds are defined
- No silent fallback to generic labels without confidence recording
- No hard-coding `images/` as the only input path for new features

## Project Priorities

1. Local execution over cloud accuracy
2. Predictable batch throughput over flashy one-off demos
3. Confidence + reviewability over forced labels
4. Backward-compatible XMP writing
5. Reuse existing dependencies where reasonable, but replace weak model choices if they block quality
