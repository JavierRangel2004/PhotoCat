<script lang="ts">
  import ConfidenceBar from "./ConfidenceBar.svelte";
  import GenreChip from "./GenreChip.svelte";
  import StatusPill from "./StatusPill.svelte";
  import type { ReviewItem } from "../../../../shared/types/review.js";

  export let item: ReviewItem | null = null;
  export let currentPosition = 0;
  export let totalVisible = 0;
</script>

<div class="rail">
  <div class="header">
    <div>
      <p>Assigned Genre</p>
      <h3>{item?.effectiveGenre || item?.finalGenre || "No item selected"}</h3>
    </div>
    <StatusPill value={item?.userLabel || item?.reviewStatus || "idle"} />
  </div>

  <div class="facts">
    <div>
      <span>File</span>
      <strong>{item?.filename || "No active file"}</strong>
    </div>
    <div>
      <span>Queue</span>
      <strong>{totalVisible ? `${currentPosition} / ${totalVisible}` : "0 / 0"}</strong>
    </div>
  </div>

  <div class="chips">
    <GenreChip label={`Model: ${item?.finalGenre || "No final genre"}`} />
    {#if item?.userGenre}
      <GenreChip label={`Override: ${item.userGenre}`} active />
    {/if}
  </div>

  <ConfidenceBar label="Model first confidence" value={item?.modelFirstConf ?? null} />
  <ConfidenceBar label="Model second confidence" value={item?.modelSecondConf ?? null} />

  <small>
    Choosing a different genre applies an override and marks the original model decision as wrong
    automatically.
  </small>
</div>

<style>
  .rail {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
  }

  p,
  h3,
  small,
  span,
  strong {
    margin: 0;
  }

  p,
  small,
  span {
    color: var(--pc-text-muted);
  }

  h3 {
    margin-top: 0.25rem;
    font-family: var(--pc-font-display);
  }

  .facts {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.85rem;
    padding: 0.9rem 1rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: rgba(255, 255, 255, 0.03);
  }

  .facts div {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    min-width: 0;
  }

  strong {
    color: var(--pc-text);
    font-size: 0.92rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
  }
</style>
