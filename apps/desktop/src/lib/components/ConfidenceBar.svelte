<script lang="ts">
  export let value: number | null = null;
  export let label = "Confidence";

  $: normalized = value === null ? 0 : Math.max(0, Math.min(1, value));
</script>

<div class="wrap">
  <div class="meta">
    <span>{label}</span>
    <strong>{value === null ? "n/a" : `${Math.round(normalized * 100)}%`}</strong>
  </div>
  <div class="track">
    <div class="fill" style={`width:${normalized * 100}%`}></div>
  </div>
</div>

<style>
  .wrap {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    font-size: 0.78rem;
  }

  span {
    color: var(--pc-text-muted);
  }

  strong {
    color: var(--pc-text-soft);
    font-weight: 600;
  }

  .track {
    overflow: hidden;
    border-radius: 999px;
    height: 4px;
    background: var(--pc-surface);
  }

  .fill {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--pc-primary), var(--pc-success));
    transition: width var(--pc-duration-normal) var(--pc-ease);
  }
</style>
