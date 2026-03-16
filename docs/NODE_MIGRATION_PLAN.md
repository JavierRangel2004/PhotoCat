# PhotoCat Node Migration Plan

## Summary

This document defines the migration plan for replacing the current Gradio UI with a Node-based frontend while keeping the existing Python processing pipeline intact.

Recommended target:
- desktop-first app shell using Electron
- frontend built with Svelte + Vite
- local backend bridge built in Node with Fastify
- existing Python pipeline kept as the source of truth for classification, CSV generation, organize preview, and XMP operations

This is not a full rewrite of PhotoCat. It is a frontend and local app-shell migration only.

Hard boundary:
- all photo processing stays in Python
- Node does not classify images
- Node does not replace metadata writing logic
- Node does not replace organize logic
- Node only handles UI, local orchestration, and frontend-facing APIs

The purpose of the migration is to unlock:
- a fully custom review experience
- better visual design control
- richer keyboard-first workflows
- stronger client-side state management
- more refined interaction design than Gradio can realistically support

## Migration Boundary

### What moves to Node

- the user interface
- local desktop shell behavior
- frontend state management
- keyboard and navigation workflows
- live log streaming to the UI
- local API endpoints that translate frontend actions into Python commands
- review-session persistence and autosave

### What stays in Python

- image analysis
- genre classification
- evidence extraction
- audit CSV generation
- corrected CSV export logic if kept in Python
- organize preview calculation
- XMP writing
- file moves and restore operations

### What Node is not allowed to own

- model inference
- genre decision policy
- image-processing algorithms
- XMP business logic
- organize business logic

## Target Architecture

### Final stack

- Electron: desktop shell, native file dialogs, local packaging
- Svelte + Vite: main UI framework and dev server
- Fastify: local API layer inside the Node runtime
- Python: existing ML pipeline and file-processing engine
- SQLite or JSON session store: local persistence for review sessions and corrections

### Why this stack

Electron is the correct shell because PhotoCat behaves like a local review workstation, not a public website.

Svelte is the correct frontend because:
- it supports highly custom UI work with less boilerplate than React
- it is well suited to image-heavy interfaces
- it aligns conceptually with Gradio's own custom frontend tooling, which already points toward Svelte

Fastify is the correct API layer because:
- it is lightweight
- it is fast enough for a local app
- it keeps the Python process isolated from frontend concerns
- it acts as a bridge, not a replacement, for the Python engine

Python should remain unchanged as much as possible because:
- the classification and metadata code already exists
- the migration problem is UI/UX, not model orchestration logic
- replacing Python and Gradio at the same time would create unnecessary product risk

## Repository Direction

Target repo structure after migration:

```text
PhotoCat/
  apps/
    desktop/
      electron/
      src/
    backend/
      src/
  python/
    src/
  shared/
    types/
  docs/
    NODE_MIGRATION_PLAN.md
```

Practical mapping from the current repo:
- move current Python code from `src/` to `python/src/`
- create `apps/desktop` for the Svelte frontend and Electron entrypoints
- create `apps/backend` for the Node local API
- create `shared/types` for canonical request/response and review-state schemas

If a large physical move is undesirable at first, phase 1 can keep Python in the current `src/` directory and add the Node app beside it.

## System Responsibilities

### Python layer responsibilities

Python remains responsible for all processing:
- running the classification pipeline
- generating the audit CSV
- loading and interpreting image evidence
- generating organize previews
- writing XMP
- moving or restoring files

Python should expose these capabilities through a thin CLI or service wrapper rather than Gradio callbacks.

### Node backend responsibilities

Node becomes responsible for:
- launching and monitoring Python subprocesses
- exposing a stable local HTTP API
- serving normalized review session data to the frontend
- persisting UI state and corrections
- resolving image paths and thumbnails
- managing autosave and recovery

Node must not duplicate Python processing logic. It only translates frontend requests into Python operations and returns normalized results.

### Frontend responsibilities

The Svelte frontend becomes responsible for:
- all layout and interaction design
- review queue navigation
- gallery, grid, and inspector views
- keyboard shortcuts
- optimistic UI state
- filtering, sorting, and queue management
- correction workflows

## Required API Contract

The frontend must not talk directly to Python. It should only use the local Node API.

The Node API is a translation layer over Python capabilities, not an independent processing backend.

### Core endpoints

`POST /api/pipeline/run`
- starts a pipeline run
- payload:
```json
{
  "inputDir": "string",
  "csvOutput": "string | null",
  "recursive": true,
  "writeXmp": false,
  "genreOnly": false,
  "noCache": false,
  "organize": false,
  "dryRun": false,
  "minConfidence": 0.55,
  "workers": 1,
  "extensions": ".jpg,.jpeg,.png"
}
```

`POST /api/pipeline/stop`
- stops the active run

`GET /api/pipeline/status`
- returns current pipeline state, progress, and last known counters

`GET /api/pipeline/logs`
- returns streamed or buffered logs
- implementation should use SSE or WebSocket for live updates

`POST /api/review/load`
- loads a CSV and image directory into a review session
- payload:
```json
{
  "csvPath": "string",
  "imageDir": "string"
}
```

`GET /api/review/session`
- returns summary, filters, visible queue, and current active item

`POST /api/review/filters`
- updates filter and sort state

`POST /api/review/select`
- jumps to an item by row id or gallery id

`POST /api/review/item/genre`
- sets `user_genre`

`POST /api/review/item/label`
- sets `user_label`

`POST /api/review/export`
- exports corrected CSV

`GET /api/review/organize-preview`
- returns the organize preview with user corrections applied

`GET /api/assets/image`
- serves the image file by normalized tokenized path, not arbitrary raw path exposure

## Data Model

The Node layer should normalize the Python CSV into a stable frontend shape.

### Review item

```ts
type ReviewItem = {
  id: string
  filename: string
  imagePath: string
  finalGenre: string
  effectiveGenre: string
  userGenre: string
  userLabel: "" | "correct" | "wrong"
  reviewStatus: "auto" | "review" | "title-inferred" | "skipped"
  rating: string
  isBlurry: string
  exposure: string
  caption: string
  objects: string
  ocrText: string
  siglipScores: string[]
  evidence: string | Record<string, unknown>
  modelFirstConf: number | null
  modelSecondConf: number | null
}
```

### Session state

```ts
type ReviewSession = {
  csvPath: string
  imageDir: string
  total: number
  visible: number
  corrected: number
  activeId: string | null
  filters: {
    genre: string
    status: string
    maxConfidence: number
    sortBy: string
    sortDirection: "asc" | "desc"
  }
}
```

## UI Migration Target

The new app should replace the current three-tab Gradio structure with a real desktop review workflow.

### Primary views

#### 1. Review Workspace

Default landing surface after loading a session.

Contains:
- left sidebar for filters, queue mode, and summary
- central image canvas
- right inspector rail with always-visible decision controls
- bottom filmstrip or queue strip for fast review movement

Mandatory design requirement:
- genre decision controls must remain visible without vertical scroll on standard laptop viewports

#### 2. Queue View

Dedicated grid/table mode for bulk triage.

Contains:
- searchable table
- gallery tiles with confidence and status overlays
- corrected-state badges
- multi-select actions reserved for future versions

#### 3. Pipeline Control View

Secondary operational view for launching runs and reading logs.

This view must not dominate the product. The app's primary identity is review and correction.

## Interaction Design Requirements

These are mandatory for the migration.

### Keyboard-first review

Add shortcuts:
- `Left` or `A`: previous image
- `Right` or `D`: next image
- `1-9` or quick keys: assign configured genres if enabled later
- `Enter`: confirm correct
- `W`: mark wrong
- `/`: focus search

### Stable review loop

A user must be able to:
1. open a review session
2. inspect the current image
3. change or confirm the genre
4. move to the next item
5. export corrections

without tab-hopping or vertical scrolling for the decision controls.

### Visual design standard

The frontend must not look like an admin dashboard template.

Design direction:
- editorial photography influence
- strong typography
- restrained warm neutral palette
- clear visual hierarchy
- minimal chrome
- motion only where it improves orientation

## Migration Phases

### Phase 1: Extract backend boundaries

Goal:
- separate UI concerns from Python concerns without moving processing out of Python

Work:
- freeze Gradio UI work except critical fixes
- define the canonical review-item schema
- wrap current Python operations in stable CLI commands or service functions
- document the command contract and outputs

Deliverable:
- Python can be driven without Gradio assumptions
- Python remains the single processing engine

### Phase 2: Build Node backend

Goal:
- create a stable local API in front of Python without reimplementing processing logic

Work:
- scaffold Fastify service
- implement Python process manager
- implement review session loader
- normalize CSV rows into a stable JSON contract
- add autosave persistence for `user_genre` and `user_label`
- expose image asset serving with safe path resolution

Deliverable:
- frontend can drive the product without touching Python internals
- Python still owns all processing behavior

### Phase 3: Build Svelte review shell

Goal:
- replace Gradio with a production-quality review workspace while keeping Python as the engine

Work:
- build app shell, sidebar, queue, inspector, and pipeline views
- build image canvas with right-side action rail
- implement gallery and queue modes
- implement keyboard navigation
- implement review state stores
- wire live pipeline logs via SSE or WebSocket

Deliverable:
- feature-complete UI parity plus improved design
- no migration of processing logic into Node

### Phase 4: Electron desktop packaging

Goal:
- package the app as a coherent local desktop tool

Work:
- wire Electron main process to Node backend
- configure native file dialogs
- handle local app startup orchestration
- package Python runtime expectations or detect external Python installation
- define cross-platform packaging strategy

Deliverable:
- local installable app with desktop-grade UX

### Phase 5: Gradio retirement

Goal:
- remove the old UI after parity is reached

Work:
- verify all required workflows exist in Node app
- migrate documentation
- archive or remove Gradio-specific code
- keep Python backend intact

Deliverable:
- Node frontend is the default UI

## Non-Negotiable Compatibility Rules

- Do not rewrite the classification logic during the UI migration.
- Do not reimplement any processing logic in Node during the UI migration.
- Do not change the CSV semantics without a compatibility layer.
- Preserve `user_genre` and `user_label` behavior.
- Preserve organize preview semantics.
- Preserve the ability to operate locally with private photo libraries.
- Preserve Windows-first viability because the current repo clearly targets local Windows use as well.
- Preserve Python as the only source of truth for processing decisions.

## Risks

### Risk 1: Double rewrite

If backend logic is changed while the UI is migrating, the project will absorb too much instability at once.

Mitigation:
- keep Python as-is initially
- change interface boundaries before changing behavior

### Risk 2: Packaging complexity

Electron plus Python can become brittle across machines.

Mitigation:
- first ship the Node app in developer mode
- delay full packaging until the API and UI stabilize

### Risk 3: Asset performance

Large photo sets can make the UI sluggish if thumbnails and image decoding are naive.

Mitigation:
- add thumbnail generation or caching in the Node layer
- lazy-load queue assets
- avoid rendering full-size images in bulk lists

### Risk 4: Schema drift

Python CSV columns may evolve and break the frontend.

Mitigation:
- normalize CSV into a versioned API contract
- reject unsupported session shapes with clear errors

## Testing Plan

### Backend tests

- pipeline run starts and stops correctly
- review session loads from real CSV samples
- filter/sort behavior matches current Python UI behavior
- corrections persist and export correctly
- organize preview reflects user overrides
- path resolution never escapes allowed roots

### Frontend tests

- inspector controls are above the fold on standard laptop breakpoints
- keyboard shortcuts work without stealing focus unexpectedly
- gallery and queue selection keep the active review item in sync
- correction state updates optimistically and survives refresh
- loading a large queue does not lock the UI

### Acceptance scenarios

- load an existing CSV, review 20 images, export corrected CSV
- run pipeline, watch logs, open resulting review session
- apply filters, navigate with keyboard, confirm and correct genres, preview organize

## Implementation Defaults

These defaults should be treated as chosen decisions, not open questions.

- Framework: Svelte + Vite
- Desktop shell: Electron
- Local API: Fastify
- Realtime transport: SSE first, WebSocket only if needed later
- State management: Svelte stores
- Persistence: lightweight local JSON or SQLite, chosen by implementation convenience
- Python integration: subprocess boundary first, not embedded interpreter integration
- Initial migration scope: UI platform only, no ML rewrite

## Immediate Next Steps

1. Create `apps/desktop` and `apps/backend`.
2. Define the shared JSON schemas for review session, review item, pipeline status, and corrections.
3. Extract Python UI-independent command wrappers for run, stop, load review session, export corrected CSV, and organize preview.
4. Implement the Fastify review-session loader against existing CSV outputs.
5. Build the review workspace first, not the pipeline screen.

## Final Recommendation

Move to Node only as a frontend/platform migration, not as a backend rewrite.

The correct execution path is:
- keep Python for all image intelligence and file operations
- build a local Node API in front of it as a bridge layer only
- build a custom Svelte desktop UI on top
- retire Gradio only after feature parity and review-speed gains are proven
