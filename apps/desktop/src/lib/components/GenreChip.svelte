<script lang="ts">
  export let label = "";
  export let active = false;
</script>

<span class="chip" class:active>{label}</span>

<style>
  .chip {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.5rem;
    border-radius: var(--pc-radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    background: var(--pc-surface);
    color: var(--pc-text-muted);
    border: 1px solid var(--pc-border);
    white-space: nowrap;
  }

  .active {
    color: var(--pc-primary);
    border-color: rgba(20, 184, 166, 0.25);
    background: rgba(20, 184, 166, 0.08);
  }
</style>
