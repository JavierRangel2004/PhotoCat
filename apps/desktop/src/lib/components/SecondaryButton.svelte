<script lang="ts">
  export let type: "button" | "submit" = "button";
  export let disabled = false;
</script>

<button class="secondary" {type} {disabled} on:click>
  <slot />
</button>

<style>
  .secondary {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.5rem 0.9rem;
    color: var(--pc-text-soft);
    background: transparent;
    font-weight: 500;
    font-size: 0.85rem;
    cursor: pointer;
    transition: color var(--pc-duration-fast) var(--pc-ease),
                border-color var(--pc-duration-fast) var(--pc-ease),
                background var(--pc-duration-fast) var(--pc-ease);
  }

  .secondary:hover:enabled {
    color: var(--pc-text);
    border-color: var(--pc-border-strong);
    background: var(--pc-surface-soft);
  }

  .secondary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .secondary:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
