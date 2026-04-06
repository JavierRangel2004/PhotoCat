<script lang="ts">
  export let type: "button" | "submit" = "button";
  export let disabled = false;
</script>

<button class="primary" {type} {disabled} on:click>
  <slot />
</button>

<style>
  .primary {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    border: none;
    border-radius: var(--pc-radius-md);
    padding: 0.55rem 1rem;
    color: #fff;
    background: var(--pc-primary);
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background var(--pc-duration-fast) var(--pc-ease),
                transform var(--pc-duration-fast) var(--pc-ease);
  }

  .primary:hover:enabled {
    background: var(--pc-primary-strong);
    transform: translateY(-1px);
  }

  .primary:active:enabled {
    transform: translateY(0);
  }

  .primary:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .primary:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
