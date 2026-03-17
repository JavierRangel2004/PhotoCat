<script lang="ts">
  import FilterSidebar from "../../lib/components/FilterSidebar.svelte";
  import ImageTile from "../../lib/components/ImageTile.svelte";
  import Panel from "../../lib/components/Panel.svelte";
  import QueueSummaryCard from "../../lib/components/QueueSummaryCard.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import { correctedItems, lowConfidenceItems, reviewOnlyItems, selectItem, session, visibleItems } from "../../lib/stores/review";

  export let currentItemId: string | null = null;
</script>

<div class="dashboard">
  <Panel eyebrow="Queue" title="Review Dashboard">
    <QueueSummaryCard session={$session} />
  </Panel>

  <div class="layout">
    <Panel title="Filters">
      <FilterSidebar
        genres={$session?.genres ?? []}
        statuses={$session?.statuses ?? []}
      />
      <div class="quick">
        <SecondaryButton disabled>Review-first view later</SecondaryButton>
        <small>Low confidence now: {$lowConfidenceItems.length}</small>
        <small>Review queue now: {$reviewOnlyItems.length}</small>
        <small>Corrected now: {$correctedItems.length}</small>
      </div>
    </Panel>

    <Panel title="Queue Grid">
      {#if $visibleItems.length}
        <div class="grid">
          {#each $visibleItems.slice(0, 8) as item}
            <button class="tile-button" aria-label="{item.filename} — {item.effectiveGenre || item.finalGenre || 'Unassigned'}" on:click={() => selectItem(item.id)}>
              <ImageTile item={item} selected={item.id === currentItemId} />
            </button>
          {/each}
        </div>
      {:else}
        <div class="empty">Load a review session to populate the queue.</div>
      {/if}
    </Panel>
  </div>
</div>

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .layout {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .tile-button {
    border: none;
    padding: 0;
    background: transparent;
    cursor: pointer;
    text-align: left;
  }

  .tile-button:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
    border-radius: var(--pc-radius-md);
  }

  .quick {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin-top: 1rem;
  }

  small,
  .empty {
    color: var(--pc-text-muted);
  }

  .empty {
    min-height: 16rem;
    display: grid;
    place-items: center;
  }

  @media (min-width: 720px) {
    .grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (min-width: 1120px) {
    .layout {
      grid-template-columns: 280px minmax(0, 1fr);
    }

    .grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
</style>
