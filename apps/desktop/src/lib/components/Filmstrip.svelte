<script lang="ts">
  import type { ReviewItem } from "../../../../shared/types/review.js";

  export let items: ReviewItem[] = [];
  export let activeId: string | null = null;
  export let onSelect: (itemId: string) => void = () => {};
</script>

<div class="filmstrip">
  {#each items.slice(0, 12) as item}
    <button class:active={item.id === activeId} on:click={() => onSelect(item.id)}>
      <span>{item.filename}</span>
    </button>
  {/each}
</div>

<style>
  .filmstrip {
    display: flex;
    gap: 0.6rem;
    overflow: auto;
    padding-bottom: 0.35rem;
  }

  button {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    background: rgba(255, 255, 255, 0.03);
    color: var(--pc-text-soft);
    padding: 0.65rem 0.8rem;
    min-height: 2.75rem;
    white-space: nowrap;
    cursor: pointer;
  }

  button.active {
    border-color: rgba(191, 39, 66, 0.48);
    color: #ffe0e8;
    box-shadow: var(--pc-glow);
  }

  button:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
