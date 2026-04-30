<script lang="ts">
  export let title = "";
  export let eyebrow = "";
  export let padded = true;
  export let compact = false;
</script>

<section class="panel" class:padded class:compact>
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
    background: var(--pc-bg-elevated);
  }

  .padded {
    padding: 1.25rem;
  }

  .compact {
    padding: 1rem;
  }

  .panel-head {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    margin-bottom: 1rem;
  }

  .eyebrow {
    margin: 0;
    color: var(--pc-primary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.68rem;
    font-weight: 600;
  }

  h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }
</style>
