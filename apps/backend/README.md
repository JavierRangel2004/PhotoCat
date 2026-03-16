# PhotoCat Backend Bridge

This package is the local Node backend for the PhotoCat frontend migration.

It is a **bridge layer**, not a processing backend.

## Responsibility

This package is responsible for:
- exposing a local HTTP API for the future desktop/frontend UI
- starting and stopping the Python pipeline
- loading review sessions through Python
- exporting corrected CSVs through Python
- requesting organize previews through Python
- serving image assets from allowed review roots

This package is **not** responsible for:
- classification
- image analysis
- evidence logic
- XMP writing logic
- organize logic

Those all remain in Python.

## Entry Point

- [src/index.ts](/C:/Users/javar/GITHUB/PhotoCat/apps/backend/src/index.ts)

## Scripts

From the repo root:

```bash
npm run dev:backend
```

From this package directory:

```bash
npm run dev
npm run start
npm run typecheck
```

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `PHOTOCAT_BACKEND_HOST` | `127.0.0.1` | Host for Fastify |
| `PHOTOCAT_BACKEND_PORT` | `8787` | Port for Fastify |
| `PHOTOCAT_PYTHON_CMD` | `python` | Python executable used to call the bridge and pipeline |

## Python Boundary

The backend currently calls:
- [src/api_bridge.py](/C:/Users/javar/GITHUB/PhotoCat/src/api_bridge.py) for review session load, corrected export, and organize preview
- [src/main.py](/C:/Users/javar/GITHUB/PhotoCat/src/main.py) for pipeline runs

If you change Python behavior, prefer extending the Python bridge or CLI contract rather than reimplementing logic in Node.

## API Surface

Current routes include:
- `/api/health`
- `/api/pipeline/run`
- `/api/pipeline/stop`
- `/api/pipeline/status`
- `/api/pipeline/logs`
- `/api/pipeline/events`
- `/api/review/load`
- `/api/review/session`
- `/api/review/item/genre`
- `/api/review/item/label`
- `/api/review/export`
- `/api/review/organize-preview`
- `/api/assets/image`

## Notes

- This package is scaffolded and not fully validated end to end yet.
- It assumes the Python environment is already installed and usable on the local machine.
- It should stay thin; business logic belongs in Python unless the logic is purely UI/API orchestration.
- Track bridge and frontend migration status in [docs/FRONTEND_EXECUTION_CHECKLIST.md](/C:/Users/javar/GITHUB/PhotoCat/docs/FRONTEND_EXECUTION_CHECKLIST.md).
