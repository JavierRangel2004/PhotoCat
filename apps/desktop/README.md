# PhotoCat Desktop Frontend

This package is the frontend scaffold for PhotoCat's custom desktop review experience.

It exists to replace the current Gradio UI with a more capable review workspace while keeping all processing in Python.

## Responsibility

This package is responsible for:
- custom layout and visual design
- queue, gallery, and inspector UX
- keyboard-first review interactions
- frontend state and navigation
- consuming the local backend bridge API

This package is **not** responsible for:
- running models
- deciding genres
- writing XMP
- organizing files

Those stay in Python and are exposed through the backend bridge.

## Stack

- Svelte
- Vite
- Electron scaffold

Current runtime status:
- frontend dev server works
- backend health check works
- foundation checkpoint UI is implemented
- real production review/session UX is still in progress

## Scripts

From the repo root:

```bash
npm run dev:desktop
```

From this package directory:

```bash
npm run dev
npm run build
npm run preview
npm run typecheck
```

## Backend Dependency

This app expects the local backend bridge to be running at:

- `http://127.0.0.1:8797`

The current frontend API helper is:
- [src/lib/api.ts](/C:/Users/javar/GITHUB/PhotoCat/apps/desktop/src/lib/api.ts)

The frontend API helper reads `VITE_PHOTOCAT_API_BASE_URL` and falls back to `http://127.0.0.1:8797`.
When you use the root `npm run dev` command, that value is injected automatically and follows the selected backend port.

## Electron

Electron entry files live here:
- [electron/main.ts](/C:/Users/javar/GITHUB/PhotoCat/apps/desktop/electron/main.ts)
- [electron/preload.ts](/C:/Users/javar/GITHUB/PhotoCat/apps/desktop/electron/preload.ts)

The current package is still primarily a frontend scaffold. Packaging and full desktop orchestration are not complete yet.

## Current Status

The current page is a migration shell, not the final review product.

What exists now:
- dark theme token system and reusable UI primitives
- backend health check and expanded frontend API layer
- app shell, session loader, dashboard, inspector, pipeline, and organize preview surfaces
- review item selection, basic mutation wiring, and optimistic session updates
- architecture boundary messaging

What still needs to be built:
- deeper filter/sidebar behavior
- compact table/list view
- keyboard shortcut system
- richer evidence and queue workflows
- safer asset contract and persistence
- production-ready review ergonomics
- premium polish, motion, and final visual refinement

## Design Direction

The target visual direction is defined by the current concept board:
- deep near-black background
- crimson primary accent
- violet secondary accent
- bright glowing confidence indicators
- premium editorial hero typography
- dense but elegant review workspace

Reference implementation plan:
- [Frontend Implementation Plan](/C:/Users/javar/GITHUB/PhotoCat/docs/FRONTEND_IMPLEMENTATION_PLAN.md)
- [Frontend Execution Checklist](/C:/Users/javar/GITHUB/PhotoCat/docs/FRONTEND_EXECUTION_CHECKLIST.md)

## Rule

If a feature needs processing logic, add it to Python first and expose it through the backend bridge. Do not move processing logic into the frontend.
