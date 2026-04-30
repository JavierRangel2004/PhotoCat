<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { desktopApi } from "../../lib/api";
  import DecisionRail from "../../lib/components/DecisionRail.svelte";
  import Filmstrip from "../../lib/components/Filmstrip.svelte";
  import Combobox from "../../lib/components/Combobox.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import { joinOutputPath, PORTFOLIO_CATEGORY_OPTIONS } from "../../lib/review/portfolioMapping";
  import {
    activeItem,
    approveModelDecision,
    organizeFlow,
    selectItem,
    session,
    setGenre,
    setLabel,
    setPortfolioCategory,
    visibleItems,
  } from "../../lib/stores/review";

  let selectedGenre = "";
  let selectedPortfolioCategory = "";
  let activeIndex = -1;

  $: organizeOutputRoot =
    $organizeFlow.preview?.resolved_output_dir?.trim() || $organizeFlow.outputDir.trim();

  // ── Flash feedback state ──────────────────────────────────
  let genreFlash = false;
  let categoryFlash = false;

  $: if ($activeItem) {
    selectedGenre = $activeItem.userGenre || $activeItem.finalGenre;
    selectedPortfolioCategory = $activeItem.userPortfolioCategory || $activeItem.portfolioCategory || "exclude";
  }

  $: imageUrl = $activeItem?.imagePath ? desktopApi.assetUrl($activeItem.imagePath) : "";
  $: activeIndex = $activeItem ? $visibleItems.findIndex((item) => item.id === $activeItem.id) : -1;
  $: previousItem = activeIndex > 0 ? $visibleItems[activeIndex - 1] : null;
  $: nextItem = activeIndex >= 0 && activeIndex < $visibleItems.length - 1 ? $visibleItems[activeIndex + 1] : null;

  // ── Computed state for override buttons ───────────────────
  $: hasGenreOverride = Boolean($activeItem?.userGenre);
  $: genreChanged = $activeItem ? selectedGenre !== ($activeItem.userGenre || $activeItem.finalGenre) : false;
  $: currentAutoCategory = $activeItem?.portfolioCategory || "exclude";
  $: categoryChanged = $activeItem
    ? selectedPortfolioCategory !== ($activeItem.userPortfolioCategory || currentAutoCategory)
    : false;

  function move(delta: number) {
    if (!$activeItem || !$visibleItems.length) return;
    const index = $visibleItems.findIndex((item) => item.id === $activeItem.id);
    const next = $visibleItems[index + delta];
    if (next) selectItem(next.id);
  }

  function triggerFlash(type: "genre" | "category") {
    if (type === "genre") {
      genreFlash = true;
      setTimeout(() => (genreFlash = false), 600);
    } else {
      categoryFlash = true;
      setTimeout(() => (categoryFlash = false), 600);
    }
  }

  function applySelectedGenre() {
    if (!$activeItem) return;
    if (!genreChanged) return; // Only apply if something actually changed
    setGenre($activeItem.id, selectedGenre);
    triggerFlash("genre");
  }

  function applyPortfolioCategory() {
    if (!$activeItem) return;
    if (!categoryChanged) return; // Only apply if something actually changed
    const autoResolved = $activeItem.portfolioCategory || "exclude";
    const isRedundant = selectedPortfolioCategory === autoResolved && !$activeItem.userPortfolioCategory;
    setPortfolioCategory($activeItem.id, isRedundant ? "" : selectedPortfolioCategory);
    triggerFlash("category");
  }

  function applyBothOverrides() {
    if (!$activeItem) return;
    if (genreChanged) {
      setGenre($activeItem.id, selectedGenre);
      triggerFlash("genre");
    }
    if (categoryChanged) {
      const autoResolved = $activeItem.portfolioCategory || "exclude";
      const isRedundant = selectedPortfolioCategory === autoResolved && !$activeItem.userPortfolioCategory;
      setPortfolioCategory($activeItem.id, isRedundant ? "" : selectedPortfolioCategory);
      triggerFlash("category");
    }
  }

  function markWrong() {
    if (!$activeItem) return;
    setLabel($activeItem.id, $activeItem.userLabel === "wrong" ? "" : "wrong");
  }

  function cycleGenre(delta: number) {
    if (!$activeItem || !$session?.genres.length) return;
    const allGenres = [$activeItem.finalGenre, ...$session.genres];
    const uniqueGenres = [...new Set(allGenres)];
    const currentIdx = uniqueGenres.indexOf(selectedGenre);
    const nextIdx = (currentIdx + delta + uniqueGenres.length) % uniqueGenres.length;
    selectedGenre = uniqueGenres[nextIdx];
  }

  function cycleCategory(delta: number) {
    const currentIdx = PORTFOLIO_CATEGORY_OPTIONS.indexOf(selectedPortfolioCategory);
    if (currentIdx < 0) return;
    const nextIdx = (currentIdx + delta + PORTFOLIO_CATEGORY_OPTIONS.length) % PORTFOLIO_CATEGORY_OPTIONS.length;
    selectedPortfolioCategory = PORTFOLIO_CATEGORY_OPTIONS[nextIdx];
  }

  function handleKeydown(event: KeyboardEvent) {
    // Skip if user is typing in an input/textarea
    const target = event.target as HTMLElement;
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT") return;
    if (!$activeItem) return;

    switch (event.key) {
      case "ArrowLeft":
        event.preventDefault();
        move(-1);
        break;
      case "ArrowRight":
        event.preventDefault();
        move(1);
        break;
      case "Enter":
        event.preventDefault();
        // Only approve if no genre override is active
        if (!$activeItem.userGenre) {
          approveModelDecision($activeItem.id);
        }
        break;
      case "w":
      case "W":
        event.preventDefault();
        markWrong();
        break;
      case "g":
      case "G":
        event.preventDefault();
        if (genreChanged) applySelectedGenre();
        break;
      case "p":
      case "P":
        event.preventDefault();
        if (categoryChanged) applyPortfolioCategory();
        break;
      case "a":
      case "A":
        event.preventDefault();
        applyBothOverrides();
        break;
      case "ArrowUp":
        event.preventDefault();
        if (event.shiftKey) {
          cycleCategory(1);
        } else {
          cycleGenre(1);
        }
        break;
      case "ArrowDown":
        event.preventDefault();
        if (event.shiftKey) {
          cycleCategory(-1);
        } else {
          cycleGenre(-1);
        }
        break;
    }
  }

  onMount(() => window.addEventListener("keydown", handleKeydown));
  onDestroy(() => window.removeEventListener("keydown", handleKeydown));
</script>

<div class="inspector">
  {#if $activeItem}
    <header class="inspector-header">
      <h1>{$activeItem.filename}</h1>
      <span class="path-hint">{$activeItem.imagePathDisplay}</span>
    </header>

    <DecisionRail
      item={$activeItem}
      currentPosition={activeIndex + 1}
      totalVisible={$visibleItems.length}
      hasPrev={!!previousItem}
      hasNext={!!nextItem}
      onPrev={() => move(-1)}
      onNext={() => move(1)}
      onApprove={() => approveModelDecision($activeItem.id)}
      onMarkWrong={markWrong}
    />

    <div class="workspace">
      <div class="stage">
        {#if imageUrl}
          <img src={imageUrl} alt={$activeItem.filename} />
        {:else}
          <div class="missing">Image not found at {$activeItem.imagePathDisplay}</div>
        {/if}
      </div>

      <div class="sidebar-controls">
        <!-- ── Genre Override ──────────────────────────────── -->
        <div class="control-group" class:flash={genreFlash}>
          <div class="group-header">
            <span class="group-label">Genre Override</span>
            {#if hasGenreOverride}
              <span class="override-indicator genre">overridden</span>
            {/if}
          </div>
          <Combobox
            label=""
            options={[$activeItem.finalGenre, ...($session?.genres ?? [])]}
            bind:value={selectedGenre}
          />
          <div class="btn-row">
            <button
              class="apply-btn"
              class:changed={genreChanged}
              class:genre-apply={genreChanged}
              disabled={!genreChanged}
              on:click={applySelectedGenre}
            >
              {#if genreChanged}
                Apply Genre Override
              {:else if hasGenreOverride}
                Genre Overridden ✓
              {:else}
                No Changes
              {/if}
            </button>
            <span class="shortcut-hint">G</span>
          </div>
        </div>

        <!-- ── Portfolio & Routing — ALWAYS VISIBLE ────────── -->
        <div class="control-group" class:flash={categoryFlash}>
          <div class="group-header">
            <span class="group-label">Portfolio & Routing</span>
            {#if $activeItem.userPortfolioCategory}
              <span class="override-indicator category">overridden</span>
            {/if}
          </div>
          <Combobox
            label=""
            options={PORTFOLIO_CATEGORY_OPTIONS}
            bind:value={selectedPortfolioCategory}
          />
          <div class="btn-row">
            <button
              class="apply-btn"
              class:changed={categoryChanged}
              class:category-apply={categoryChanged}
              disabled={!categoryChanged}
              on:click={applyPortfolioCategory}
            >
              {#if categoryChanged}
                Apply Category Override
              {:else if $activeItem.userPortfolioCategory}
                Category Overridden ✓
              {:else}
                No Changes
              {/if}
            </button>
            <span class="shortcut-hint">P</span>
          </div>

          <div class="path-info">
            <div class="path-row">
              <span>Current Category</span>
              <strong class:has-override={$activeItem.userPortfolioCategory}>
                {$activeItem.userPortfolioCategory || currentAutoCategory}
                {#if $activeItem.userPortfolioCategory}
                  <small>(auto: {currentAutoCategory})</small>
                {/if}
              </strong>
            </div>
            <div class="path-row">
              <span>Destination</span>
              <strong>{joinOutputPath(organizeOutputRoot, $activeItem.destRelpath || $activeItem.filename)}</strong>
            </div>
          </div>
        </div>

        <!-- ── Apply Both ──────────────────────────────────── -->
        {#if genreChanged || categoryChanged}
          <button class="apply-both-btn" on:click={applyBothOverrides}>
            Apply All Overrides
            {#if genreChanged && categoryChanged}(Genre + Category){:else if genreChanged}(Genre){:else}(Category){/if}
            <span class="shortcut-hint inline">A</span>
          </button>
        {/if}

        <!-- ── AI Evidence — collapsed ─────────────────────── -->
        <details class="advanced-section">
          <summary>AI Evidence</summary>
          <div class="detail-content">
            {#if $activeItem.caption}
              <div class="evidence-block">
                <span class="evidence-label">Caption</span>
                <p>{$activeItem.caption}</p>
              </div>
            {/if}
            {#if $activeItem.objects}
              <div class="evidence-block">
                <span class="evidence-label">Objects</span>
                <p>{$activeItem.objects}</p>
              </div>
            {/if}
            {#if $activeItem.ocrText}
              <div class="evidence-block">
                <span class="evidence-label">OCR</span>
                <p>{$activeItem.ocrText}</p>
              </div>
            {/if}
            {#if $activeItem.evidence}
              <div class="evidence-block">
                <span class="evidence-label">Evidence Log</span>
                <pre>{$activeItem.evidence}</pre>
              </div>
            {/if}
          </div>
        </details>

        <!-- ── Keyboard Shortcuts Legend ────────────────────── -->
        <div class="shortcuts-legend">
          <span class="legend-title">Keyboard Shortcuts</span>
          <div class="legend-grid">
            <kbd>←</kbd><span>Previous photo</span>
            <kbd>→</kbd><span>Next photo</span>
            <kbd>↑↓</kbd><span>Cycle genre</span>
            <kbd>⇧↑↓</kbd><span>Cycle category</span>
            <kbd>Enter</kbd><span>Approve</span>
            <kbd>W</kbd><span>Mark wrong</span>
            <kbd>G</kbd><span>Apply genre</span>
            <kbd>P</kbd><span>Apply category</span>
            <kbd>A</kbd><span>Apply all overrides</span>
          </div>
        </div>
      </div>
    </div>

    <Filmstrip items={$visibleItems} activeId={$activeItem.id} onSelect={selectItem} />
  {:else}
    <div class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
      <p>Select an item from the Review tab to inspect it.</p>
    </div>
  {/if}
</div>

<style>
  .inspector {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .inspector-header {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  h1 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  .path-hint {
    color: var(--pc-text-muted);
    font-size: 0.78rem;
    word-break: break-all;
  }

  .workspace {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .stage {
    min-height: 28rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-lg);
    overflow: hidden;
    background: var(--pc-surface);
    display: grid;
    place-items: center;
  }

  img {
    max-width: 100%;
    max-height: 70vh;
    object-fit: contain;
  }

  .missing {
    color: var(--pc-text-muted);
    padding: 2rem;
    text-align: center;
  }

  .sidebar-controls {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  /* ── Control Groups ─────────────────────────────────────── */
  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    padding: 0.75rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg-elevated);
    transition: border-color 0.3s var(--pc-ease), box-shadow 0.3s var(--pc-ease);
  }

  .control-group.flash {
    border-color: var(--pc-primary);
    box-shadow: var(--pc-glow);
    animation: flash-border 0.6s ease;
  }

  @keyframes flash-border {
    0%   { box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.3); }
    100% { box-shadow: var(--pc-glow); }
  }

  .group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .group-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--pc-text-soft);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .override-indicator {
    padding: 0.1rem 0.35rem;
    border-radius: var(--pc-radius-sm);
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    animation: flash-in 0.3s ease;
  }

  .override-indicator.genre {
    color: var(--pc-warning);
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.25);
  }

  .override-indicator.category {
    color: var(--pc-secondary);
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.25);
  }

  @keyframes flash-in {
    0%   { opacity: 0; transform: scale(0.85); }
    100% { opacity: 1; transform: scale(1); }
  }

  .btn-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  /* ── Apply Buttons ──────────────────────────────────────── */
  .apply-btn {
    flex: 1;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.4rem 0.65rem;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    background: transparent;
    color: var(--pc-text-muted);
    transition: all var(--pc-duration-fast) var(--pc-ease);
    text-align: center;
  }

  .apply-btn:disabled {
    cursor: default;
    opacity: 0.7;
  }

  .apply-btn.changed {
    cursor: pointer;
    opacity: 1;
  }

  .apply-btn.genre-apply {
    color: var(--pc-warning);
    border-color: rgba(245, 158, 11, 0.4);
    background: rgba(245, 158, 11, 0.08);
  }

  .apply-btn.genre-apply:hover {
    background: rgba(245, 158, 11, 0.16);
    border-color: rgba(245, 158, 11, 0.6);
  }

  .apply-btn.category-apply {
    color: var(--pc-secondary);
    border-color: rgba(99, 102, 241, 0.4);
    background: rgba(99, 102, 241, 0.08);
  }

  .apply-btn.category-apply:hover {
    background: rgba(99, 102, 241, 0.16);
    border-color: rgba(99, 102, 241, 0.6);
  }

  .shortcut-hint {
    display: grid;
    place-items: center;
    width: 22px;
    height: 22px;
    border-radius: var(--pc-radius-sm);
    background: var(--pc-surface);
    color: var(--pc-text-muted);
    font-size: 0.65rem;
    font-weight: 700;
    font-family: var(--pc-font-mono);
    border: 1px solid var(--pc-border);
    flex-shrink: 0;
  }

  .shortcut-hint.inline {
    display: inline-grid;
    margin-left: 0.35rem;
  }

  /* ── Apply Both ─────────────────────────────────────────── */
  .apply-both-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    border: 1px solid rgba(20, 184, 166, 0.35);
    border-radius: var(--pc-radius-md);
    padding: 0.5rem 0.75rem;
    color: var(--pc-primary);
    background: rgba(20, 184, 166, 0.06);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--pc-duration-fast) var(--pc-ease);
    animation: flash-in 0.25s ease;
  }

  .apply-both-btn:hover {
    background: rgba(20, 184, 166, 0.12);
    border-color: rgba(20, 184, 166, 0.5);
  }

  /* ── Path Info ──────────────────────────────────────────── */
  .path-info {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    margin-top: 0.25rem;
    padding-top: 0.45rem;
    border-top: 1px solid var(--pc-border);
  }

  .path-row {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .path-row span {
    color: var(--pc-text-muted);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .path-row strong {
    color: var(--pc-text-soft);
    font-size: 0.8rem;
    font-weight: 500;
    word-break: break-all;
  }

  .path-row strong.has-override {
    color: var(--pc-secondary);
  }

  .path-row small {
    color: var(--pc-text-muted);
    font-size: 0.72rem;
    margin-left: 0.35rem;
  }

  /* ── Collapsible Details ────────────────────────────────── */
  .advanced-section {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg-elevated);
    overflow: hidden;
  }

  .advanced-section summary {
    padding: 0.55rem 0.75rem;
    cursor: pointer;
    color: var(--pc-text-soft);
    font-size: 0.8rem;
    font-weight: 600;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 0.35rem;
    transition: background var(--pc-duration-fast) var(--pc-ease);
  }

  .advanced-section summary:hover {
    background: var(--pc-surface-soft);
  }

  .advanced-section summary::-webkit-details-marker {
    display: none;
  }

  .advanced-section summary::before {
    content: "▸";
    font-size: 0.65rem;
    color: var(--pc-text-muted);
    transition: transform var(--pc-duration-fast) var(--pc-ease);
  }

  .advanced-section[open] summary::before {
    transform: rotate(90deg);
  }

  .detail-content {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    padding: 0.75rem;
    border-top: 1px solid var(--pc-border);
  }

  .evidence-block {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .evidence-label {
    color: var(--pc-text-muted);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
  }

  .evidence-block p,
  .evidence-block pre {
    margin: 0;
    color: var(--pc-text-soft);
    font-size: 0.8rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .evidence-block pre {
    font-family: var(--pc-font-mono);
    font-size: 0.72rem;
  }

  /* ── Keyboard Shortcuts Legend ───────────────────────────── */
  .shortcuts-legend {
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg-elevated);
  }

  .legend-title {
    display: block;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--pc-text-muted);
    margin-bottom: 0.4rem;
  }

  .legend-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.2rem 0.5rem;
    align-items: center;
  }

  kbd {
    display: inline-grid;
    place-items: center;
    min-width: 26px;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
    background: var(--pc-surface);
    border: 1px solid var(--pc-border);
    color: var(--pc-text-soft);
    font-family: var(--pc-font-mono);
    font-size: 0.65rem;
    font-weight: 600;
    text-align: center;
  }

  .legend-grid span {
    color: var(--pc-text-muted);
    font-size: 0.72rem;
  }

  /* ── Empty State ────────────────────────────────────────── */
  .empty {
    min-height: 24rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    color: var(--pc-text-muted);
  }

  .empty p {
    margin: 0;
    font-size: 0.9rem;
  }

  @media (min-width: 1120px) {
    .workspace {
      grid-template-columns: minmax(0, 1.5fr) 340px;
    }

    .sidebar-controls {
      position: sticky;
      top: 1rem;
      align-self: start;
    }
  }
</style>
