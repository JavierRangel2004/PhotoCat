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

  // P1: Skeleton loading state — reset whenever imageUrl changes
  let imageLoaded = false;
  $: {
    imageUrl;
    imageLoaded = false;
  }

  // P2: Intersection Observer fade-in
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
        <div class="skeleton" />
      {/if}
      <img
        src={imageUrl}
        srcset={imageSrcset}
        sizes="(min-width: 1120px) 33vw, (min-width: 720px) 50vw, 100vw"
        alt={item.filename}
        loading="lazy"
        class:loaded={imageLoaded}
        on:load={() => (imageLoaded = true)}
      />
    {:else}
      <div class="missing">Missing image</div>
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
    gap: 0.8rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: rgba(255, 255, 255, 0.03);
    overflow: hidden;
    opacity: 0;
    transform: translateY(12px);
    transition:
      opacity 0.4s ease,
      transform 0.4s ease;
  }

  .tile.in-view {
    opacity: 1;
    transform: translateY(0);
  }

  .selected {
    border-color: rgba(191, 39, 66, 0.48);
    box-shadow: var(--pc-glow);
  }

  .preview {
    position: relative;
    aspect-ratio: 4 / 3;
    background: rgba(255, 255, 255, 0.03);
  }

  @keyframes skeleton-pulse {
    0%,
    100% {
      background-color: rgba(255, 255, 255, 0.05);
    }
    50% {
      background-color: rgba(255, 255, 255, 0.1);
    }
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
  }

  .meta {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0 0.9rem 0.9rem;
  }

  .row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  strong {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
