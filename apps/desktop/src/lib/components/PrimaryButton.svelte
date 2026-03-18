<script lang="ts">
  export let type: "button" | "submit" = "button";
  export let disabled = false;
</script>

<button class="primary" {type} {disabled} on:click>
  <slot />
</button>

<style>
  .primary {
    border: none;
    border-radius: 999px;
    padding: 0.85rem 1.2rem;
    color: #fff7fb;
    background: linear-gradient(135deg, var(--pc-primary), var(--pc-primary-strong));
    box-shadow: var(--pc-glow);
    font-weight: 700;
    cursor: pointer;
    transition:
      transform var(--pc-duration-fast) var(--pc-ease),
      filter var(--pc-duration-fast) var(--pc-ease);
  }

  .primary:hover:enabled {
    transform: translateY(-1px);
    filter: brightness(1.08);
  }

  .primary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .primary:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
