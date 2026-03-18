<script lang="ts">
  import Badge from "./Badge.svelte";
  import type { ReviewSession } from "../../../../shared/types/review.js";

  export let session: ReviewSession | null = null;
</script>

<div class="summary">
  <div>
    <p>Total</p>
    <strong>{session?.summary.total ?? 0}</strong>
  </div>
  <div>
    <p>Review</p>
    <strong>{session?.summary.review ?? 0}</strong>
  </div>
  <div>
    <p>Corrected</p>
    <strong>{session?.summary.corrected ?? 0}</strong>
  </div>
  <div class="badges">
    <Badge tone="primary">Auto {session?.summary.auto ?? 0}</Badge>
    <Badge tone="warning">Title inferred {session?.summary.titleInferred ?? 0}</Badge>
  </div>
</div>

<style>
  .summary {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
  }

  p,
  strong {
    margin: 0;
  }

  p {
    color: var(--pc-text-muted);
    font-size: 0.82rem;
  }

  strong {
    display: block;
    margin-top: 0.2rem;
    font-size: 1.7rem;
    font-family: var(--pc-font-display);
  }

  .badges {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    gap: 0.55rem;
  }

  @media (max-width: 920px) {
    .summary {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>
