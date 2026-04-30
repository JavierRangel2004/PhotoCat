# PhotoCat

**PhotoCat** is a local-first photo categorization tool for reviewing, correcting, and organizing image libraries with AI assistance.

The project now runs as a hybrid system:
- **Python processing engine** for classification, evidence extraction, CSV generation, organize preview, XMP writing, and file operations
- **Node workspace** for the new custom review interface and local desktop/app-shell migration

Hard boundary:
- **all photo processing stays in Python**
- **Node does not replace the ML pipeline**
- **Node is only the UI, local bridge, and desktop shell direction**

## Current Status

What is working now:
- Python pipeline CLI works
- Python bridge CLI works
- Node workspace installs
- Fastify backend bridge runs on `127.0.0.1:8797`
- Svelte/Vite frontend scaffold runs on `localhost:4173`
- browser-to-backend communication works

What is still in progress:
- the new frontend is still a scaffold, not the final review product
- Gradio still exists as the current Python UI
- the premium concept-board-driven frontend is planned but not fully implemented yet

## Architecture

### Python layer

Python remains the source of truth for:
- genre classification
- image evidence extraction
- audit CSV generation
- corrected CSV export behavior
- organize preview behavior
- XMP sidecar writing
- file moves and restore operations

Main Python entrypoints:
- [src/main.py](/C:/Users/javar/GITHUB/PhotoCat/src/main.py)
- [src/api_bridge.py](/C:/Users/javar/GITHUB/PhotoCat/src/api_bridge.py)
- [src/ui.py](/C:/Users/javar/GITHUB/PhotoCat/src/ui.py)

### Node layer

The Node workspace is the migration foundation for the new frontend:
- [apps/backend](/C:/Users/javar/GITHUB/PhotoCat/apps/backend) = local Fastify bridge over Python
- [apps/desktop](/C:/Users/javar/GITHUB/PhotoCat/apps/desktop) = Svelte/Vite desktop frontend scaffold
- [shared/types](/C:/Users/javar/GITHUB/PhotoCat/shared/types) = shared review/session types

Current runtime split:
- Python executes processing
- backend bridge translates frontend requests into Python commands
- Svelte frontend renders the review experience

## Features

- **Genre Classification**: SigLIP2-based genre classification with evidence fusion from YOLO and BLIP
- **Audit CSV Reports**: reviewable CSV output with confidences and review status
- **Confidence-Gated Decisions**: automatic vs review vs title-inferred write policy
- **XMP Metadata Writing**: sidecar metadata compatible with Lightroom and similar tools
- **Automatic File Organization**: organize photos into genre folders after review
- **Local Review Workflow**: Gradio UI today, custom Node frontend migration in progress
- **Local-Only Processing**: no cloud APIs required for the core pipeline

## Quick Start

### Prerequisites

- Python 3.8+
- Node 20.19+ or 22.12+
- Git
- Optional NVIDIA GPU with CUDA
- Optional Tesseract OCR

### Python installation

```bash
git clone https://github.com/JavierRangel2004/PhotoCat.git
cd PhotoCat
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Optional CUDA install:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### Node workspace installation

From the repo root:

```bash
npm install
```

## Usage

### Python pipeline

Dry run:

```bash
python src/main.py --input-dir /path/to/photos
```

Classify and organize:

```bash
python src/main.py --input-dir /path/to/photos --organize
```

Genre-only mode:

```bash
python src/main.py --input-dir /path/to/photos --genre-only --organize
```

Full pipeline with XMP writing:

```bash
python src/main.py --input-dir /path/to/photos --write-xmp --organize
```

### Python bridge

Check the bridge:

```bash
python src/api_bridge.py --help
```

### Current Gradio UI

The existing Python review UI still lives here:

```bash
python src/ui.py
python src/ui.py --browser
```

### Node backend bridge

```bash
npm run dev:backend
```

This starts the Fastify bridge on `127.0.0.1:8797`.

### Node frontend scaffold

```bash
npm run dev:desktop
```

This starts the Svelte/Vite frontend scaffold on `http://localhost:4173`.

## Workspace Scripts

From the repo root:

```bash
npm run dev
npm run dev:backend
npm run dev:desktop
npm run typecheck
```

Notes:
- `npm run dev` starts the backend and frontend together
- `npm run dev:backend` and `npm run dev:desktop` still work independently
- the combined dev command prefers backend `127.0.0.1:8797` and frontend `127.0.0.1:4173`
- if either preferred port is already in use, the launcher picks the next free port automatically

## Configuration

### Python

Python behavior is still controlled by the CLI flags documented in [src/cli.py](/C:/Users/javar/GITHUB/PhotoCat/src/cli.py).

Important flags:
- `--input-dir`
- `--recursive`
- `--extensions`
- `--write-xmp`
- `--genre-only`
- `--organize`
- `--csv`
- `--min-confidence`
- `--workers`
- `--dry-run`
- `--no-cache`

### Backend bridge environment variables

The Node backend uses these optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `PHOTOCAT_BACKEND_HOST` | `127.0.0.1` | Fastify host |
| `PHOTOCAT_BACKEND_PORT` | `8797` | Fastify port |
| `VITE_PHOTOCAT_API_BASE_URL` | `http://127.0.0.1:8797` | Frontend API base URL |
| `PHOTOCAT_PYTHON_CMD` | `python` | Python executable used by the bridge |

The bridge script path is currently [src/api_bridge.py](/C:/Users/javar/GITHUB/PhotoCat/src/api_bridge.py).

## Project Structure

```text
PhotoCat/
  apps/
    backend/           # Fastify bridge over Python
    desktop/           # Svelte/Vite frontend scaffold
  docs/
    ARCHITECTURE.md    # System architecture and roadmap
    TAXONOMY.md        # Photography category definitions
  shared/
    types/             # Shared Node types
  src/
    api_bridge.py      # Python JSON bridge for Node
    main.py            # Processing pipeline
    ui.py              # Current Gradio UI
    ui_state.py        # Review state logic reused by bridge
```

## Documentation

- [Architecture & Implementation Roadmap](docs/ARCHITECTURE.md) - System architecture and development roadmap.
- [Taxonomy Strategy](docs/TAXONOMY.md) - Detailed guide to the 6-category photography taxonomy.
- [UI/UX Guidelines](apps/desktop/docs/UI_UX_GUIDELINES.md) - Design rules and checklist for the Svelte desktop frontend.

## Work Allocation

If you are choosing where to work:
- processing, metadata, and classification logic: Python
- backend bridge and API normalization: `apps/backend`
- premium review interface and desktop shell: `apps/desktop`

## License

This project is licensed under the [MIT License](LICENSE).
