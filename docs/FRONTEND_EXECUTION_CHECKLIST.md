# PhotoCat Frontend Execution Checklist

This checklist turns the existing frontend and migration docs into an implementation document for the current repo state.

It is based on:
- `docs/FRONTEND_IMPLEMENTATION_PLAN.md`
- `docs/NODE_MIGRATION_PLAN.md`
- `docs/UI_PLAN.md`
- `docs/UI_GUIDE.md`
- `docs/UI_UX_REFACTOR_ANALYSIS.md`
- `apps/desktop/*`
- `apps/backend/*`
- `src/api_bridge.py`
- `src/ui_state.py`

## Boundary And Current Reality

Non-negotiable boundary:
- Python remains the only processing engine.
- Node remains a bridge, UI runtime, and desktop shell layer.
- The frontend must only call the local Node API, never Python directly.

Current repo reality:
- [x] Fastify bridge scaffold exists.
- [x] Python bridge CLI exists for load session, export corrected CSV, and organize preview.
- [x] Pipeline manager exists with run, stop, status, logs, and SSE events.
- [x] Shared review and pipeline types exist in `shared/types/review.ts`.
- [x] Desktop frontend scaffold exists and can check backend health.
- [x] Electron shell scaffold exists with a desktop window and preload boundary.
- [x] Backend review routes already expose load, session, mutation, export, and organize-preview endpoints.
- [x] Frontend foundation dashboard is implemented as a checkpoint surface.
- [x] Frontend foundation inspector workspace is implemented as a checkpoint surface.
- [x] Frontend API client now covers the currently exposed backend endpoints.
- [x] Frontend stores, route-state foundation, and premium visual system foundation are implemented.
- [ ] Review correction persistence is only in backend memory for the current process.
- [ ] Asset serving still uses raw path query input instead of a safer tokenized asset contract.
- [ ] Full UI workflow for organize commit and restore is not exposed in the Node bridge.

## Decisions To Treat As Chosen Defaults

- [x] Keep Svelte + Vite + Electron for the desktop shell direction.
- [x] Keep Fastify as the local API bridge.
- [x] Keep SSE as the first live transport for pipeline logs and status.
- [x] Keep Svelte stores as the frontend state model.
- [x] Keep review filtering and sorting client-side for the MVP because `load-session` already returns the normalized item set.
- [ ] Add backend persistence for corrections and recovery before calling the frontend "usable".
- [ ] Replace raw image path queries with a tokenized or item-id-based asset contract before broad UI use.

## Design System And Visual Direction

- [x] Replace the current light editorial placeholder in `apps/desktop/src/App.svelte` with the documented dark premium direction.
- [x] Add `apps/desktop/src/lib/theme/tokens.css` with color, spacing, radius, shadow, and motion tokens.
- [x] Use the documented near-black, crimson, and violet palette consistently across shell, panels, states, and actions.
- [ ] Load and apply the intended typography hierarchy for hero, section titles, dense metadata, and counters.
- [x] Define state colors for idle, loading, running, success, warning, error, correct, wrong, and review-required.
- [ ] Define glow usage rules so glow only appears on primary actions, live pipeline state, and active confidence states.
- [x] Define responsive breakpoints for desktop-first review workstations and narrow fallback layouts.
- [x] Standardize surface treatments so the app uses glass or brushed dark panels instead of flat cards.
- [x] Define empty, loading, and error state visuals so the product still looks deliberate when data is missing.

## Frontend Component Foundations

- [x] Create reusable components for `AppNav`, `PrimaryButton`, `SecondaryButton`, `Panel`, `Badge`, `ConfidenceBar`, `GenreChip`, `StatusPill`, and `Toast`.
- [x] Create reusable review components for `ImageTile`, `QueueSummaryCard`, `FilterSidebar`, `EvidenceCard`, `DecisionRail`, `Filmstrip`, and `LogConsole`.
- [ ] Create shared layout components for the landing shell, dashboard shell, inspector shell, and pipeline shell.
- [ ] Add a keyboard shortcut overlay or command surface component.
- [ ] Add component states for hover, selected, focused, disabled, loading, optimistic-update, and error.

## Frontend App Structure

- [x] Expand `apps/desktop/src/` to the documented `lib/`, `features/`, and `stores/` structure.
- [x] Split the app into clear top-level views: landing/app shell, review dashboard, inspector workspace, and pipeline control view.
- [x] Add a view-state or route-state model so the user can switch views without losing the active session.
- [x] Keep the inspector as the primary work surface, not the pipeline screen.
- [x] Preserve the current active item when moving between dashboard and inspector.
- [ ] Preserve filter state, sort state, and current queue position across view changes.

## Frontend State And Data Model

- [x] Create a typed frontend API module that covers every currently exposed backend endpoint.
- [x] Create Svelte stores for app shell state, backend health, pipeline state, review session, filter state, active item, view mode, and notifications.
- [x] Create derived selectors for visible queue, review-only queue, low-confidence queue, and corrected-item counts.
- [ ] Track unsaved correction state in the UI even if autosave exists in the backend.
- [x] Add optimistic update handling for genre and label changes with rollback on request failure.
- [ ] Add reconnect or reload handling for backend restarts so the UI can recover cleanly.
- [x] Add a session hydration path that re-requests the current backend session on app load.
- [ ] Decide and document whether large-session filtering remains purely client-side or moves to backend pagination later.

## Backend Bridge Gaps To Close

- [x] Expand `apps/desktop/src/lib/api.ts` to include `pipelineRun`, `pipelineStop`, `pipelineStatus`, `pipelineLogs`, `pipelineEvents`, `session`, `setGenre`, `setLabel`, `exportCorrected`, `organizePreview`, and `assetUrl`.
- [ ] Normalize all backend error responses into a stable JSON shape instead of relying on generic HTTP status messages only.
- [ ] Return richer success payloads for export and organize preview, including output paths and summary details the UI can display directly.
- [ ] Add correction persistence beyond process memory so backend restarts do not erase review work.
- [ ] Add a backend recovery endpoint or session resume behavior if correction persistence is implemented.
- [ ] Replace `/api/assets/image?path=...` with a safer contract based on item id, token, or validated relative asset id.
- [ ] Add safe support for thumbnails if the dashboard will show large queues.
- [ ] Revisit allowed asset roots so they can safely include the active image directory, derived thumbnail cache, and any review-session temp outputs.
- [ ] Decide whether `/api/review/filters` and `/api/review/select` are still needed after the client-side filtering decision; implement only if queue size or persistence requires server authority.
- [ ] Add a dedicated organize commit endpoint if the goal is to complete file moves from the new UI rather than only preview them.
- [ ] Add a restore endpoint if the UI is expected to own the full organize and undo workflow.

## Python Bridge And Shared Contract Work

- [x] Keep `src/api_bridge.py` as the single Python CLI contract used by Node for review actions.
- [x] Expand the Python bridge only when a UI workflow cannot be expressed with the current commands.
- [ ] Add versioning or compatibility checks for the session payload shape so CSV schema drift fails clearly.
- [ ] Ensure the Python bridge returns consistent keys for summary, items, errors, export output path, and organize preview data.
- [x] Confirm the Python bridge keeps `user_genre` and `user_label` semantics aligned with the current Gradio workflow.
- [ ] Decide whether organize commit should be exposed through `api_bridge.py`, through `src/main.py`, or through a separate Python command wrapper.

## Workflow: Run Pipeline

- [x] Build a pipeline form in the frontend that maps exactly to `PipelineRunRequest`.
- [ ] Validate input directory, csv output path, min confidence, workers, and extensions before submit.
- [ ] Show a clear warning when `workers > 1` changes cache behavior.
- [ ] Disable conflicting actions while a pipeline run is active.
- [x] Subscribe to `/api/pipeline/events` and render live logs and live status in the UI.
- [x] Parse and display progress, current counts, state, and terminal error state.
- [x] Implement stop behavior with clear `running`, `stopping`, `done`, and `error` UI states.
- [ ] After a successful run, surface the generated CSV path and offer a direct transition into review loading.
- [ ] Decide whether the backend should auto-load the generated CSV into the active review session after completion.

## Workflow: Load CSV And Open Review Session

- [x] Build a session loader that captures CSV path and image directory.
- [ ] Add file and folder pickers through Electron when desktop packaging is in scope.
- [ ] Validate that the CSV exists, the image directory exists, and the returned session contains items.
- [x] Load and render summary counts, available genres, available statuses, and the normalized item list.
- [x] Hydrate the dashboard and inspector from the same session store.
- [x] Show a useful empty state when the CSV is valid but no images resolve.
- [x] Handle missing files, broken CSV schema, invalid paths, and Python bridge failures explicitly.

## Workflow: Review Dashboard And Evaluation Queue

- [x] Build the dashboard with queue summary, filter rail, search, confidence threshold, and view mode controls.
- [ ] Default the first review mode toward the highest-value queue, such as `review` or low-confidence items.
- [x] Implement gallery/grid view with status overlays, confidence, corrected state, and quick-open behavior.
- [ ] Implement compact table/list view with sortable columns and quick navigation into the inspector.
- [x] Keep the active item synchronized between grid, list, and inspector.
- [x] Surface counters for total, visible, corrected, auto, review, and title-inferred items.
- [ ] Add quick evaluation slices such as low confidence, missing image file, overridden genre, and marked wrong.
- [ ] Add a search path for filename and possibly caption or OCR text if needed for review work.

## Workflow: Inspect Single Image

- [x] Build the large image stage with proper fit, zoom strategy, and missing-image fallback.
- [x] Keep the decision rail visible without vertical scroll on standard laptop heights.
- [x] Show filename, resolved path, review status, effective genre, confidence, and correction state together.
- [ ] Show caption, detected objects, OCR text, SigLIP scores, and evidence in a structured reading order.
- [x] Make `Assigned Genre`, `Confirm`, and `Mark Wrong` the highest-priority controls in the inspector.
- [x] Add next and previous navigation that follows the current filtered queue.
- [ ] Show queue position and remaining review count.
- [ ] Add quick-return navigation from inspector back to the queue with context preserved.
- [ ] Add keyboard shortcuts for next, previous, confirm, mark wrong, and search focus.
- [ ] Prevent focus traps so keyboard review works even after interacting with controls.

## Workflow: Correction Actions

- [x] Wire genre changes to `POST /api/review/item/genre`.
- [x] Wire correct and wrong labeling to `POST /api/review/item/label`.
- [x] Update the frontend session store optimistically and reconcile with backend responses.
- [x] Recompute derived queue stats after each correction.
- [x] Surface transient success and failure feedback without interrupting review flow.
- [x] Preserve corrections if the user changes filters, view mode, or active item.
- [ ] Add a dirty-state warning before the user leaves the active session if persistence is not guaranteed.

## Workflow: Export Corrected CSV

- [x] Add an export action reachable from both dashboard and inspector contexts.
- [ ] Show what the export writes: original CSV plus `user_genre` and `user_label` semantics.
- [ ] Display the output path returned by the backend.
- [ ] Clear dirty-state warnings only after export success or durable autosave confirmation.
- [x] Add explicit error handling for export failures and filesystem permission issues.

## Workflow: Organize Preview And Organize Commit

- [x] Keep organize preview available from the review workflow, not buried in a secondary screen.
- [ ] Render organize preview as structured UI, not raw text only.
- [ ] Show counts by destination genre and counts using user overrides.
- [ ] Require preview review before any real organize action is enabled.
- [ ] If actual organize-from-UI is required, add a backend endpoint for organize commit that uses corrected state safely.
- [ ] If organize commit is added, require confirmation messaging before file moves happen.
- [ ] If organize commit is added, return or persist a move manifest for auditing and restore.
- [ ] If restore-from-UI is required, expose Python restore behavior through the backend and add a dedicated restore workflow.

## Workflow: Asset Loading And Image Checks

- [x] Create a single frontend helper for asset URLs instead of assembling paths in view components.
- [ ] Add missing-image detection and a visible badge in queue and inspector views.
- [ ] Support common review image formats already handled by the backend.
- [ ] Decide whether to add thumbnail generation in the backend for large queues.
- [ ] Lazy-load gallery assets and avoid loading full-size images in bulk lists.
- [ ] Avoid exposing arbitrary filesystem paths to the browser layer once the asset contract is tightened.

## Workflow: Evaluation And Review Productivity

- [ ] Surface review efficiency metrics such as corrected count, wrong count, reviewed count, and remaining review items.
- [ ] Add quick filters for low confidence, title-inferred, corrected, and missing-image rows.
- [ ] Make it easy to inspect the evidence behind a weak classification without opening secondary dialogs for every action.
- [ ] Add confidence visualization that emphasizes uncertainty rather than just showing a raw number.
- [ ] Measure whether the new review loop is faster than the current Gradio flow on real sessions.
- [ ] Decide whether future evaluation views should include dataset export or correction analytics beyond the review queue.

## Persistence, Recovery, And Session Safety

- [ ] Decide where the durable correction state lives in the Node path: JSON, SQLite, or another lightweight local store.
- [ ] Persist corrections often enough that backend restarts do not lose review work.
- [ ] Restore active session state, filters, and active item if the app is reopened during an unfinished review.
- [ ] Show last-saved status in the UI if durable persistence is added.
- [ ] Keep autosave and export semantics aligned with the existing Python UI expectations.

## Performance And Scalability

- [ ] Keep dashboard rendering responsive with large item sets.
- [ ] Virtualize or paginate the queue if real sessions become too heavy for full-grid rendering.
- [ ] Avoid recomputing expensive derived data on every keystroke.
- [ ] Add thumbnail caching if full image loading slows the queue.
- [ ] Keep SSE subscriptions and log buffers bounded so long runs do not degrade the UI.

## Accessibility And Interaction Quality

- [ ] Ensure all primary actions are reachable by keyboard.
- [ ] Make focus styles visible against the dark theme.
- [ ] Ensure text contrast remains readable for dense evidence panels.
- [ ] Support standard laptop widths without hiding the decision rail below the fold.
- [ ] Prevent accidental destructive actions by requiring clear confirmation for stop, organize, and restore flows.

## Testing And Acceptance

### Backend And Bridge

- [ ] Test pipeline run, stop, status, logs, and SSE events from the Node bridge.
- [ ] Test review session loading against a real CSV and real image directory.
- [ ] Test genre and label changes end to end through Node into the Python-backed session model.
- [ ] Test corrected CSV export with real review changes.
- [ ] Test organize preview with and without corrections applied.
- [ ] Test asset access restrictions so files outside allowed roots cannot be served.

### Frontend

- [ ] Test backend unavailable state on initial load.
- [ ] Test loading, error, and empty states for every top-level view.
- [ ] Test queue filters, sorting, and active-item synchronization.
- [ ] Test keyboard shortcuts during real review flows.
- [ ] Test optimistic updates and rollback paths when requests fail.
- [ ] Test inspector layout on standard laptop viewport heights.
- [ ] Test large-session performance with real queues.

### Acceptance Scenarios

- [ ] Run the pipeline from the UI and watch live progress until completion.
- [ ] Load the resulting CSV and image directory into a review session.
- [ ] Filter to review-needed items and inspect the queue.
- [ ] Open an image, inspect evidence, and change its genre.
- [ ] Mark items correct and wrong without losing queue context.
- [ ] Export a corrected CSV successfully.
- [ ] Preview organize results with user corrections applied.
- [ ] If organize commit is implemented, complete the preview-confirm-organize loop safely.

## Recommended Build Order

- [ ] 1. Finish design tokens, layout shell, and reusable primitives first.
- [ ] 2. Expand the frontend API client and Svelte stores to cover the full existing backend surface.
- [ ] 3. Build session loading and dashboard queue state before the inspector polish.
- [ ] 4. Build the inspector and correction loop next, including keyboard workflow.
- [ ] 5. Build pipeline control and live log streaming once review state is stable.
- [ ] 6. Close backend persistence and asset-contract gaps before calling the UI production-ready.
- [ ] 7. Add organize commit and restore only when the preview and correction loop are already reliable.

## Definition Of Done

The Node frontend can be treated as the real PhotoCat UI when all of these are true:
- [ ] The user can run the pipeline from the new UI.
- [ ] The user can load a CSV and image directory into a review session from the new UI.
- [ ] The user can filter, evaluate, inspect, and correct images without losing state.
- [ ] The user can export corrected CSV output from the new UI.
- [ ] The user can preview organize results from the new UI.
- [ ] If the product requires it, the user can safely commit organize and restore actions from the new UI.
- [ ] The review workflow is at least as reliable as the current Python/Gradio flow.
- [ ] The frontend visually matches the documented premium concept direction instead of the current scaffold.
