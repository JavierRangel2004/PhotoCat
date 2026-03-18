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
    gap: 0.45rem;
  }

  .meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    color: var(--pc-text-soft);
    font-size: 0.84rem;
  }

  strong {
    color: #ffe0e8;
  }

  .track {
    overflow: hidden;
    border-radius: 999px;
    height: 0.65rem;
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(147, 122, 173, 0.16);
  }

  .fill {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--pc-secondary), var(--pc-primary));
    box-shadow: 0 0 24px rgba(225, 75, 115, 0.25);
    transition: width var(--pc-duration-normal) var(--pc-ease);
  }
</style>
