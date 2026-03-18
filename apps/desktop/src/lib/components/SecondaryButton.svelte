<script lang="ts">
  export let type: "button" | "submit" = "button";
  export let disabled = false;
</script>

<button class="secondary" {type} {disabled} on:click>
  <slot />
</button>

<style>
  .secondary {
    border: 1px solid var(--pc-border);
    border-radius: 999px;
    padding: 0.82rem 1.15rem;
    color: var(--pc-text);
    background: rgba(93, 42, 122, 0.12);
    font-weight: 600;
    cursor: pointer;
    transition:
      background var(--pc-duration-fast) var(--pc-ease),
      border-color var(--pc-duration-fast) var(--pc-ease);
  }

  .secondary:hover:enabled {
    background: rgba(93, 42, 122, 0.2);
    border-color: rgba(147, 122, 173, 0.42);
  }

  .secondary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .secondary:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
