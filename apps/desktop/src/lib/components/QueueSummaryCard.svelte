<script lang="ts">
  import type { ReviewSession } from "../../../../shared/types/review.js";

  export let session: ReviewSession | null = null;
</script>

<div class="summary">
  <div class="stat">
    <span class="stat-value">{session?.summary.total ?? 0}</span>
    <span class="stat-label">Total</span>
  </div>
  <div class="stat">
    <span class="stat-value">{session?.summary.review ?? 0}</span>
    <span class="stat-label">Review</span>
  </div>
  <div class="stat">
    <span class="stat-value">{session?.summary.corrected ?? 0}</span>
    <span class="stat-label">Corrected</span>
  </div>
  <div class="stat">
    <span class="stat-value">{session?.summary.auto ?? 0}</span>
    <span class="stat-label">Auto</span>
  </div>
</div>

<style>
  .summary {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    align-items: baseline;
    gap: 0.35rem;
  }

  .stat-value {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--pc-text);
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--pc-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
</style>
