<script lang="ts">
  export let tone: "neutral" | "primary" | "danger" | "warning" | "success" = "neutral";
</script>

<span class={`badge ${tone}`}>
  <slot />
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    border-radius: 999px;
    padding: 0.38rem 0.7rem;
    font-size: 0.76rem;
    font-weight: 700;
    border: 1px solid var(--pc-border);
    color: var(--pc-text-soft);
    background: rgba(255, 255, 255, 0.03);
  }

  .primary {
    color: #ffd7e0;
    border-color: rgba(191, 39, 66, 0.5);
    background: rgba(158, 27, 50, 0.16);
  }

  .danger {
    color: #ffd4da;
    border-color: rgba(216, 75, 95, 0.48);
    background: rgba(216, 75, 95, 0.16);
  }

  .warning {
    color: #ffe7b8;
    border-color: rgba(201, 144, 63, 0.5);
    background: rgba(201, 144, 63, 0.16);
  }

  .success {
    color: #ffd8e5;
    border-color: rgba(225, 75, 115, 0.48);
    background: rgba(225, 75, 115, 0.16);
  }
</style>
