<script lang="ts">
  export let label = "";
  export let active = false;
</script>

<span class:active class="chip">{label}</span>

<style>
  .chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 0.4rem 0.78rem;
    background: rgba(93, 42, 122, 0.12);
    border: 1px solid var(--pc-border);
    color: var(--pc-text-soft);
    font-size: 0.8rem;
  }

  .active {
    background: rgba(158, 27, 50, 0.18);
    border-color: rgba(191, 39, 66, 0.5);
    color: #ffe0e8;
    box-shadow: var(--pc-glow);
  }
</style>
