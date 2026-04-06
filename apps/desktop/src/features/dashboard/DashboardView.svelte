<script lang="ts">
  import FilterSidebar from "../../lib/components/FilterSidebar.svelte";
  import ImageTile from "../../lib/components/ImageTile.svelte";
  import QueueSummaryCard from "../../lib/components/QueueSummaryCard.svelte";
  import { correctedItems, lowConfidenceItems, reviewOnlyItems, selectItem, session, visibleItems, reviewFilters } from "../../lib/stores/review";

  export let currentItemId: string | null = null;
</script>

<div class="dashboard">
  <header class="dash-header">
    <div class="header-left">
      <h1>Review</h1>
      <QueueSummaryCard session={$session} />
    </div>
  </header>

  <FilterSidebar
    genres={$session?.genres ?? []}
    statuses={$session?.statuses ?? []}
    bind:selectedGenre={$reviewFilters.genre}
    bind:selectedStatus={$reviewFilters.status}
    bind:search={$reviewFilters.search}
  />

  {#if $visibleItems.length}
    <div class="grid">
      {#each $visibleItems as item}
        <button class="tile-button" aria-label="{item.filename}" on:click={() => selectItem(item.id)}>
          <ImageTile {item} selected={item.id === currentItemId} />
        </button>
      {/each}
    </div>
  {:else}
    <div class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
      <p>Load a review session to populate the queue.</p>
    </div>
  {/if}
</div>

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .dash-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .header-left {
    display: flex;
    align-items: baseline;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.02em;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
  }

  .tile-button {
    border: none;
    padding: 0;
    background: transparent;
    cursor: pointer;
    text-align: left;
    width: 100%;
  }

  .tile-button:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
    border-radius: var(--pc-radius-md);
  }

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

  @media (min-width: 720px) {
    .grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (min-width: 1200px) {
    .grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }
</style>
