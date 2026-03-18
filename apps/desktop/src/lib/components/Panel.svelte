<script lang="ts">
  export let title = "";
  export let eyebrow = "";
  export let padded = true;
</script>

<section class:padded class="panel">
  {#if eyebrow || title}
    <header class="panel-head">
      {#if eyebrow}
        <p class="eyebrow">{eyebrow}</p>
      {/if}
      {#if title}
        <h2>{title}</h2>
      {/if}
    </header>
  {/if}
  <slot />
</section>

<style>
  .panel {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-lg);
    background: var(--pc-surface-glass);
    box-shadow: var(--pc-shadow-soft);
    backdrop-filter: blur(18px);
  }

  .padded {
    padding: var(--pc-space-5);
  }

  .panel-head {
    display: flex;
    flex-direction: column;
    gap: var(--pc-space-2);
    margin-bottom: var(--pc-space-4);
  }

  .eyebrow {
    margin: 0;
    color: var(--pc-primary);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    font-weight: 700;
  }

  h2 {
    margin: 0;
    font-size: 1.1rem;
    font-family: var(--pc-font-display);
    letter-spacing: 0.01em;
  }
</style>
