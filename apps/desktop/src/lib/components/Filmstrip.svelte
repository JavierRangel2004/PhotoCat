<script lang="ts">
  import { desktopApi } from "../api";
  import type { ReviewItem } from "../../../../shared/types/review.js";

  export let items: ReviewItem[] = [];
  export let activeId: string | null = null;
  export let onSelect: (id: string) => void = () => {};
</script>

<div class="filmstrip">
  {#each items.slice(0, 20) as item}
    <button
      class="thumb"
      class:active={item.id === activeId}
      on:click={() => onSelect(item.id)}
      aria-label={item.filename}
    >
      {#if item.imagePath}
        <img
          src={desktopApi.thumbnailUrl(item.imagePath, 80)}
          alt={item.filename}
          loading="lazy"
        />
      {:else}
        <div class="no-img"></div>
      {/if}
    </button>
  {/each}
</div>

<style>
  .filmstrip {
    display: flex;
    gap: 0.35rem;
    overflow-x: auto;
    padding: 0.25rem 0;
    scrollbar-width: thin;
  }

  .thumb {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    border: 2px solid transparent;
    border-radius: var(--pc-radius-sm);
    overflow: hidden;
    cursor: pointer;
    padding: 0;
    background: var(--pc-surface);
    transition: border-color var(--pc-duration-fast) var(--pc-ease);
  }

  .thumb:hover {
    border-color: var(--pc-border-strong);
  }

  .thumb.active {
    border-color: var(--pc-primary);
  }

  .thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .no-img {
    width: 100%;
    height: 100%;
    background: var(--pc-surface-strong);
  }
</style>
