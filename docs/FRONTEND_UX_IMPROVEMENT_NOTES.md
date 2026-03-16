# PhotoCat Frontend UX Improvement Notes

This document records the inspector-focused UI and UX fixes implemented after reviewing the frontend checkpoint screenshots.

## Problems Observed

- The genre dropdown was unreadable in the dark theme because the text and option backgrounds were too close in value.
- The inspector showed duplicate action controls because `DecisionRail` rendered one action set and `InspectorView` rendered another.
- The original action phrasing made the review intent ambiguous.
- Changing the genre did not clearly express that the original model decision should now be treated as wrong.
- Previous and next navigation looked like generic secondary buttons instead of primary queue movement controls.
- The inspector did not present the item identity and queue context strongly enough.

## Implemented Fixes

### Dropdown readability

- Added global dark-theme styling for `select` and `option` elements in `apps/desktop/src/lib/theme/tokens.css`.
- Improved the inspector select styling with a dedicated wrapper, stronger contrast, and a custom caret treatment.
- Added a clear first option that explicitly means "use the model genre".

### Action model cleanup

- Removed the duplicated confirm and wrong button row from `DecisionRail`.
- Kept the mutation controls in one place inside `InspectorView`.
- Changed the primary action phrasing from generic confirmation language to `Keep Model Genre`.
- Changed the override action to `Apply Override` or `Clear Override` depending on the current selection.

### Override semantics

- Updated the review store so that applying a different genre automatically:
  - stores a user override
  - marks the model decision as `wrong`
- Updated the model approval flow so that `Keep Model Genre`:
  - clears any active override
  - marks the item as `correct`

### Navigation UX

- Replaced the previous simple buttons with a dedicated navigation card.
- Added stronger hierarchy for previous and next controls.
- Added filename previews for adjacent items.
- Added queue position context in the decision rail and navigator.

### Inspector information hierarchy

- Added file identity and queue facts to the decision rail.
- Added a resolved path block for debugging and confidence while reviewing local files.
- Kept confidence, genre state, and review status grouped together.

## Files Updated

- `apps/desktop/src/lib/theme/tokens.css`
- `apps/desktop/src/lib/stores/review.ts`
- `apps/desktop/src/lib/components/DecisionRail.svelte`
- `apps/desktop/src/features/inspector/InspectorView.svelte`

## Resulting UX Direction

The inspector now follows a cleaner review model:

1. Identify the current file and queue position.
2. Review the current model genre and confidence.
3. Either keep the model decision or apply an override.
4. Move through the queue with clearer adjacent-item navigation.

This is a better match for the product goal than having multiple overlapping button groups with unclear semantics.

## Remaining High-Value Improvements

- Replace the native select with a fully custom accessible combobox if the browser-level dropdown still feels inconsistent on Windows.
- Add inline mutation-state feedback near the control card, not only toasts.
- Show explicit `remaining review items` in the navigation area.
- Add keyboard shortcuts for:
  - previous
  - next
  - approve model
  - focus override selector
- Add a compact table/list queue mode for faster batch triage.
- Add a stronger difference between:
  - model genre
  - current effective genre
  - user override
- Add persistent save status and unsaved change indicators once backend persistence exists.
- Replace the current raw-path image asset contract with a safer tokenized backend route.
