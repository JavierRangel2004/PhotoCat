<script lang="ts">
  import { onMount } from "svelte";
  import { desktopApi } from "../api";
  import GenreChip from "./GenreChip.svelte";
  import StatusPill from "./StatusPill.svelte";
  import type { ReviewItem } from "../../../../shared/types/review.js";

  export let item: ReviewItem;
  export let selected = false;

  $: imageUrl = item.imagePath ? desktopApi.thumbnailUrl(item.imagePath, 400) : "";
  $: imageSrcset = item.imagePath
    ? `${desktopApi.thumbnailUrl(item.imagePath, 400)} 400w, ${desktopApi.thumbnailUrl(item.imagePath, 800)} 800w`
    : undefined;

  let imageLoaded = false;
  $: {
    imageUrl;
    imageLoaded = false;
  }

  let tileEl: HTMLElement;
  let inView = false;

  onMount(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          inView = true;
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(tileEl);
    return () => observer.disconnect();
  });
</script>

<article bind:this={tileEl} class:selected class:in-view={inView} class="tile">
  <div class="preview">
    {#if imageUrl}
      {#if !imageLoaded}
        <div class="skeleton"></div>
      {/if}
      <img
        src={imageUrl}
        srcset={imageSrcset}
        sizes="(min-width: 1120px) 25vw, (min-width: 720px) 33vw, 50vw"
        alt={item.filename}
        loading="lazy"
        class:loaded={imageLoaded}
        on:load={() => (imageLoaded = true)}
      />
    {:else}
      <div class="missing">No image</div>
    {/if}
  </div>

  <div class="meta">
    <div class="row">
      <strong>{item.filename}</strong>
      <StatusPill value={item.userLabel || item.reviewStatus} />
    </div>
    <GenreChip label={item.effectiveGenre || item.finalGenre || "Unassigned"} active={selected} />
  </div>
</article>

<style>
  .tile {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg-elevated);
    overflow: hidden;
    opacity: 0;
    transform: translateY(8px);
    transition: opacity 0.35s ease,
                transform 0.35s ease,
                border-color var(--pc-duration-fast) var(--pc-ease),
                box-shadow var(--pc-duration-fast) var(--pc-ease);
    cursor: pointer;
  }

  .tile.in-view {
    opacity: 1;
    transform: translateY(0);
  }

  .tile:hover {
    border-color: var(--pc-border-strong);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .selected {
    border-color: var(--pc-primary) !important;
    box-shadow: var(--pc-glow) !important;
  }

  .preview {
    position: relative;
    aspect-ratio: 4 / 3;
    background: var(--pc-surface);
  }

  @keyframes skeleton-pulse {
    0%, 100% { background-color: var(--pc-surface); }
    50%      { background-color: var(--pc-surface-strong); }
  }

  .skeleton {
    position: absolute;
    inset: 0;
    animation: skeleton-pulse 1.4s ease-in-out infinite;
  }

  img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  img.loaded {
    opacity: 1;
  }

  .missing {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
    color: var(--pc-text-muted);
    font-size: 0.8rem;
  }

  .meta {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.6rem 0.7rem;
  }

  .row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }

  strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.82rem;
    font-weight: 600;
  }
</style>
