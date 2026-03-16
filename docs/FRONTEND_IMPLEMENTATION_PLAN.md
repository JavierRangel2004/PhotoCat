# PhotoCat Frontend Implementation Plan

## Summary

This document defines the full frontend implementation plan for PhotoCat's custom Node-based review interface.

Implementation status should be tracked in:
- [docs/FRONTEND_EXECUTION_CHECKLIST.md](/C:/Users/javar/GITHUB/PhotoCat/docs/FRONTEND_EXECUTION_CHECKLIST.md)

The target experience follows the provided concept board:
- premium dark interface
- crimson primary accent
- violet secondary accent
- glowing confidence and activity treatments
- minimal but powerful controls
- dense inspection workspace for local professional review

Hard boundary:
- all photo processing stays in Python
- this plan is only for the frontend, visual system, and frontend-facing interaction model

## Concept Translation

### Brand direction

The concept board establishes these non-negotiable visual traits:
- near-black primary background
- luminous crimson as the dominant action color
- soft violet as the supporting accent and border tone
- dark glass or brushed-panel surfaces instead of flat cards
- high-contrast typography with large bold headlines
- glow reserved for live states, confidence, and primary actions

### Product feeling

The product should feel:
- intelligent
- seamless
- powerful
- premium
- accurate
- local-first
- evidence-based
- contemporary
- secure
- trustworthy

This is not an admin dashboard. It should feel like a specialized creative review workstation.

## Visual System

### Color tokens

Base palette derived from the concept:

```text
Background Primary: #0A0510
Surface Primary:    #140A16
Surface Raised:     #1A0F20
Primary Accent:     #9E1B32
Secondary Accent:   #5D2A7A
Muted Text:         #A09DB0
Border:             rgba(147, 122, 173, 0.22)
Success Glow:       rgba(234, 78, 113, 0.38)
```

State rules:
- confirm/review/live activity use crimson
- passive surfaces and evidence grouping use violet-gray borders
- confidence bars glow only on active or selected states

### Typography

Based on the concept board:
- Heading font: `Montserrat`
- UI/body font: `Inter`

Hierarchy:
- hero / landing headline: large, bold, compressed spacing
- section headings: Montserrat semibold
- body and dense data: Inter
- numeric status, confidence, counters: Inter medium or semibold

### Components

The concept board implies a reusable component system:
- navigation bar
- primary buttons
- secondary buttons
- confidence bar
- genre chips/tags
- evidence card
- image tile
- floating tooltip panel
- inspector decision rail
- compact table row

These must be implemented as reusable Svelte components, not page-specific markup.

## Application Structure

### Top-level views

#### 1. Landing / App shell

Purpose:
- establish the product identity
- allow loading an existing review session
- expose pipeline actions without overwhelming the review experience

Features:
- branded top nav
- hero section matching the concept board
- quick access buttons: Run pipeline, Export CSV, Organize
- summary of current session if loaded

#### 2. Review dashboard

Purpose:
- triage large sets of images before opening the detailed inspector

Features:
- search
- filter chips
- genre/status dropdowns
- confidence threshold control
- image grid
- compact table/list mode
- review-state badges on tiles

#### 3. Inspector workspace

Purpose:
- the primary working surface for human correction

Features:
- large image canvas
- sticky right-side decision rail
- evidence column/cards
- confidence visualization
- next/prev navigation
- correction actions
- keyboard shortcut overlay

This is the most important screen in the product.

## Layout Plan

### Navigation bar

Based on the concept board:
- left: PhotoCat logo and wordmark
- center/right: Navigation, Organize, Actions
- right edge: a red primary action chip or button for the most important current task

Behavior:
- compact height
- slightly translucent dark bar
- subtle outer glow or drop shadow
- sticky on scroll

### Review dashboard layout

Desktop:
- left rail: filters and queue summary
- main: image grid and optional table section
- right utility rail: quick evidence, confidence, and context cards

Mobile or narrow:
- filters collapse into drawers
- utility rail stacks below main content

### Inspector layout

Desktop:
- center-left: large image stage
- right: stacked evidence and decision panels
- bottom or lower-left: filmstrip / quick queue

Mandatory:
- `Assigned Genre`, confirm, wrong, and action feedback are visible without vertical scrolling

## Motion Plan

### Principles

Animation must feel intentional, not decorative.

Use motion for:
- route transitions
- panel reveal
- live progress updates
- confidence score pulses
- grid-to-inspector continuity

Avoid:
- excessive bounce
- playful motion
- long durations

### Required motion behaviors

- confidence bars animate when values load or change
- grid selection animates into inspector context
- filter changes fade and reorder smoothly
- evidence cards reveal with stagger, not instant dump
- action confirmation gives a short crimson pulse or glow

## Component Implementation Plan

### Phase 1: Foundations

Build:
- theme tokens and CSS custom properties
- base layout shell
- `AppNav.svelte`
- `PrimaryButton.svelte`
- `SecondaryButton.svelte`
- `Panel.svelte`
- `Badge.svelte`
- `ConfidenceBar.svelte`
- `GenreChip.svelte`

Acceptance:
- frontend already looks aligned with the concept board before real data wiring

### Phase 2: Session loading and state

Build:
- frontend store for review session
- session loader form
- backend health state
- session summary strip
- API integration for `/api/review/load` and `/api/review/session`

Acceptance:
- load a real CSV + image directory and render summary state

### Phase 3: Review dashboard

Build:
- filter sidebar
- image grid
- compact table/list view
- status overlays
- confidence badges
- review counters

Acceptance:
- user can browse and triage the queue before opening the inspector

### Phase 4: Inspector workspace

Build:
- full image canvas
- sticky decision rail
- evidence modules
- confidence visualization block
- previous/next navigation
- correction actions wired to backend

Acceptance:
- full correction loop works without needing Gradio

### Phase 5: Keyboard-first workflow

Build:
- global shortcut manager
- next/previous keys
- confirm/wrong keys
- command palette or quick actions panel
- focus management

Acceptance:
- experienced user can review quickly without mouse-only interaction

### Phase 6: Premium polish

Build:
- glow behaviors
- hover states
- animated confidence indicators
- refined empty/loading/error states
- tooltip/floating action treatments

Acceptance:
- interface feels premium and close to the concept board rather than merely functional

## Data Integration Plan

### Backend endpoints to consume first

- `GET /api/health`
- `POST /api/review/load`
- `GET /api/review/session`
- `POST /api/review/item/genre`
- `POST /api/review/item/label`
- `POST /api/review/export`
- `GET /api/review/organize-preview`

### Frontend state model

Create stores for:
- app shell state
- loaded review session
- active item id
- filter state
- dashboard view mode
- inspector interaction state
- transient notifications

## File Plan

Suggested frontend structure:

```text
apps/desktop/src/
  App.svelte
  main.ts
  lib/
    api.ts
    theme/
      tokens.css
    stores/
      app.ts
      review.ts
    components/
      AppNav.svelte
      Panel.svelte
      Badge.svelte
      ConfidenceBar.svelte
      GenreChip.svelte
      ImageTile.svelte
      EvidenceCard.svelte
  features/
    dashboard/
    inspector/
    pipeline/
```

## Documentation Updates Required Alongside Implementation

As the frontend grows, keep these in sync:
- root [README.md](/C:/Users/javar/GITHUB/PhotoCat/README.md)
- [apps/desktop/README.md](/C:/Users/javar/GITHUB/PhotoCat/apps/desktop/README.md)
- [docs/NODE_MIGRATION_PLAN.md](/C:/Users/javar/GITHUB/PhotoCat/docs/NODE_MIGRATION_PLAN.md)
- [docs/FRONTEND_EXECUTION_CHECKLIST.md](/C:/Users/javar/GITHUB/PhotoCat/docs/FRONTEND_EXECUTION_CHECKLIST.md)

## Testing and Acceptance

### Visual acceptance

- matches the dark premium concept direction
- uses crimson and violet intentionally, not generically
- feels like a product, not a dashboard template

### Functional acceptance

- can load a review session
- can browse the queue
- can open the inspector
- can change genre
- can mark correct/wrong
- can export
- can preview organize

### Workflow acceptance

- decision controls never drop below the fold on a standard laptop viewport
- active confidence and evidence states are easy to read
- review loop is faster than the current Gradio UI

## Immediate Build Order

1. Implement theme tokens and navigation shell.
2. Replace the placeholder `App.svelte` layout with the branded app shell from the concept board.
3. Add review session loader UI wired to the backend.
4. Build the dashboard image grid and summary cards.
5. Build the inspector workspace and sticky decision rail.
6. Add animation and premium polish after the core workflow is functional.
