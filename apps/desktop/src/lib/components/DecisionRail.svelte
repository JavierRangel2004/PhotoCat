<script lang="ts">
  import ConfidenceBar from "./ConfidenceBar.svelte";
  import GenreChip from "./GenreChip.svelte";
  import StatusPill from "./StatusPill.svelte";
  import type { ReviewItem } from "../../../../shared/types/review.js";

  export let item: ReviewItem | null = null;
  export let currentPosition = 0;
  export let totalVisible = 0;
  export let onPrev: () => void = () => {};
  export let onNext: () => void = () => {};
  export let onApprove: () => void = () => {};
  export let onMarkWrong: () => void = () => {};
  export let hasPrev = false;
  export let hasNext = false;

  $: hasOverride = Boolean(item?.userGenre);
  $: isApproved = item?.userLabel === "correct";
  $: isWrong = item?.userLabel === "wrong";
</script>

<div class="rail">
  <div class="rail-left">
    <button class="nav-arrow" disabled={!hasPrev} on:click={onPrev} aria-label="Previous item (←)">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>

    <div class="genre-section">
      <GenreChip label={item?.effectiveGenre || item?.finalGenre || "Unassigned"} active />
      {#if item?.userGenre}
        <span class="override-badge">Override: {item.userGenre}</span>
      {/if}
    </div>

    <StatusPill value={item?.userLabel || item?.reviewStatus || "idle"} />

    <span class="position">
      {totalVisible ? `${currentPosition}/${totalVisible}` : ""}
    </span>
  </div>

  <div class="rail-right">
    <div class="confidence-inline">
      <ConfidenceBar label="Confidence" value={item?.modelFirstConf ?? null} />
    </div>

    <div class="action-group">
      {#if !hasOverride}
        <button
          class="action-btn approve"
          class:active-state={isApproved}
          on:click={onApprove}
          aria-label="Approve model decision (Enter)"
          title="Enter"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {isApproved ? "Approved" : "Approve"}
        </button>
      {/if}

      <button
        class="action-btn wrong"
        class:active-state={isWrong && !hasOverride}
        on:click={onMarkWrong}
        aria-label="Mark as wrong (W)"
        title="W"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
        {isWrong ? "Wrong" : "Mark Wrong"}
      </button>
    </div>

    <button class="nav-arrow" disabled={!hasNext} on:click={onNext} aria-label="Next item (→)">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="9 18 15 12 9 6" />
      </svg>
    </button>
  </div>
</div>

<style>
  .rail {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg-elevated);
    flex-wrap: wrap;
  }

  .rail-left, .rail-right {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .genre-section {
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }

  .override-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.15rem 0.45rem;
    border-radius: var(--pc-radius-sm);
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--pc-warning);
    border: 1px solid rgba(245, 158, 11, 0.3);
    background: rgba(245, 158, 11, 0.08);
    animation: flash-in 0.3s var(--pc-ease);
  }

  @keyframes flash-in {
    0%   { opacity: 0; transform: scale(0.9); }
    100% { opacity: 1; transform: scale(1); }
  }

  .position {
    color: var(--pc-text-muted);
    font-size: 0.75rem;
    font-weight: 500;
    font-family: var(--pc-font-mono);
  }

  .confidence-inline {
    min-width: 110px;
  }

  .action-group {
    display: flex;
    gap: 0.3rem;
  }

  .nav-arrow {
    display: grid;
    place-items: center;
    width: 30px;
    height: 30px;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    background: transparent;
    color: var(--pc-text-muted);
    cursor: pointer;
    transition: color var(--pc-duration-fast) var(--pc-ease),
                background var(--pc-duration-fast) var(--pc-ease);
    flex-shrink: 0;
  }

  .nav-arrow:hover:enabled {
    color: var(--pc-text);
    background: var(--pc-surface-soft);
  }

  .nav-arrow:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.35rem 0.6rem;
    font-weight: 600;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--pc-duration-fast) var(--pc-ease);
    white-space: nowrap;
  }

  .action-btn.approve {
    color: var(--pc-success);
    background: transparent;
    border-color: rgba(34, 197, 94, 0.25);
  }

  .action-btn.approve:hover {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.4);
  }

  .action-btn.approve.active-state {
    color: #fff;
    background: var(--pc-success);
    border-color: var(--pc-success);
  }

  .action-btn.wrong {
    color: var(--pc-danger);
    background: transparent;
    border-color: rgba(239, 68, 68, 0.25);
  }

  .action-btn.wrong:hover {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.4);
  }

  .action-btn.wrong.active-state {
    color: #fff;
    background: var(--pc-danger);
    border-color: var(--pc-danger);
  }

  .nav-arrow:focus-visible,
  .action-btn:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
