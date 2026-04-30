# PhotoCat UI/UX Guidelines & Implementation Strategy

## 1. Design Philosophy
The PhotoCat desktop client is built to be a high-performance **review workspace**, not just a generic dashboard. The UI focuses on speed, clarity, and enabling the user to quickly triage and correct ML categorizations.

### Key Principles
- **Decision First:** The primary action (confirming or changing a genre) must always be visible "above the fold." Users should never have to scroll past metadata to reach the "Approve" button.
- **Editorial Aesthetic:** Restrained color palette. Deep near-black backgrounds (`rgba(24, 12, 30, 0.95)`), soft glows, with crimson and violet accents. 
- **Bento Box Layout:** Distinct, card-like grids that logically group information (e.g., Image Preview, Action Panel, Evidence Accordions).
- **Keyboard-First Navigation:** Triage should be doable entirely via keyboard (Arrow keys for prev/next, Enter to confirm, shortcuts for specific genres).

## 2. Component System (Svelte)

### Core Primitives
- **Panels & Cards:** `<Panel>` and `<EvidenceCard>` components are used to structure the Bento Box layout.
- **Typography:** Uses fluid typography (`clamp()`) for responsive scaling without harsh breakpoints.
- **Buttons & Interactivity:** Primary, Secondary, and Ghost buttons with distinct focus states (`:focus-visible`) for accessibility.
- **Feedback:** Micro-interactions (hover transitions, lazy-load skeletons, blur-up images) ensure the app feels responsive.

### Specialized Components
- **Combobox:** A custom, keyboard-accessible select component for quickly choosing genres without breaking flow.
- **ImageTile:** Lazy-loaded grid item for the queue/gallery view. Uses `IntersectionObserver` for fade-in and `srcset` for performance.
- **InspectorView:** The heart of the app. It houses the selected image, its ML evidence, and the decision controls.

## 3. Frontend Architecture Rules

### State Management
- **Source of Truth:** The backend JSON (derived from the Python CSV) is the source of truth.
- **Stores:** Svelte stores (`app.ts`, `pipeline.ts`, `review.ts`) manage transient state, active filters, and the currently selected image in the inspector.
- **Optimistic Updates:** When a user corrects a genre, the local Svelte store updates immediately, while the change is queued to be persisted via the Node bridge.

### Accessibility (A11y)
- Strict adherence to `:focus-visible` outlines (`2px solid var(--pc-primary)`).
- Proper ARIA labels (`aria-label`, `aria-expanded`, `role="combobox"`) for complex interactive elements.
- Semantic HTML throughout the layout.

## 4. Implementation Checklist (Current Status)

- [x] Svelte + Vite App Shell setup.
- [x] Node (Fastify) Backend Bridge wiring.
- [x] Global Design Tokens (Dark mode, Math-based spacing).
- [x] Base Layouts (Dashboard, Queue, Inspector).
- [x] Inspector redesign to move "Action" above the fold.
- [ ] Implement robust keyboard shortcut system.
- [ ] Complete Electron packaging and native dialog integration.
- [ ] Advanced queue sorting and virtualized list rendering for large datasets.
