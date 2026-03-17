# PhotoCat Architecture & Implementation Roadmap

PhotoCat is a local-first photo categorization tool designed to process, classify, and organize photography portfolios. It operates on a hybrid architecture, keeping heavy machine learning models in Python while providing a modern desktop experience via a Node/Svelte frontend.

## 1. System Architecture

The application is split into three primary layers:

### A. Python Processing Engine (`src/`)
The source of truth for all ML inference, data extraction, and file operations.
- **`scene_classifier.py`**: Runs SigLIP2 zero-shot classification using prompt ensembles.
- **`object_detection.py`**: Uses YOLOv8 for detecting specific objects (e.g., stage, microphone).
- **`image_captioning.py`**: Uses BLIP to generate descriptive captions of the scene.
- **`genre_decision.py`**: Fuses evidence from SigLIP, YOLO, BLIP, OCR, and rules to make the final genre decision.
- **`metadata_writer.py`**: Writes standard XMP sidecar files compatible with Lightroom.
- **`main.py` & `cli.py`**: Core pipeline orchestration and command-line interface.
- **`api_bridge.py`**: Exposes Python capabilities via JSON/CLI interfaces for the Node backend.

### B. Node Backend Bridge (`apps/backend/`)
A lightweight Fastify API that acts as a translation layer. It **does not** run ML models or processing algorithms.
- Exposes local HTTP endpoints (`/api/pipeline/*`, `/api/review/*`).
- Manages Python subprocesses for pipeline execution.
- Reads CSV outputs and serves normalized JSON to the frontend.
- Serves local images securely.

### C. Desktop Frontend (`apps/desktop/`)
A Svelte + Vite application packaged with Electron.
- Delivers a premium, keyboard-first review workspace.
- Manages client-side state, filtering, and queue navigation.
- Consumes the local Fastify backend bridge.

## 2. Implementation Roadmap

### Phase 1: Core Pipeline & Taxonomy (Completed)
- 10-category taxonomy implemented.
- SigLIP2 + YOLO + BLIP fusion working.
- CLI, CSV audit, and XMP writing implemented.

### Phase 2: Caching & Fast Iteration (Completed)
- `src/cache.py` caches deterministic model outputs (YOLO, BLIP, SigLIP) in SQLite.
- Enables near-instant re-runs when tweaking `genre_decision.py` rules.

### Phase 3: Frontend Migration (In Progress)
- **Goal:** Replace the legacy Gradio UI (`src/ui.py`) with the new Svelte Desktop app.
- **Status:** Node backend bridge is running. Svelte frontend scaffold is complete with basic dark theme, navigation, and API wiring.
- **Remaining Work:** Finish the inspector views, keyboard shortcuts, image grid, and correction workflows. Pack via Electron.

### Phase 4: Batch GPU Processing (Planned)
- Implement `--batch-size` for YOLO, BLIP, and SigLIP to speed up first-run throughput on large datasets.

### Phase 5: Classification Quality Improvements (Ongoing)
- Continuously refine `genre_decision.py` based on edge cases (e.g., distinguishing architecture from street photography, handling specialized lighting like concerts vs fireworks).
