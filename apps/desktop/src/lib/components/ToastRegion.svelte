<script lang="ts">
  export type Toast = {
    id: number;
    tone: "neutral" | "success" | "warning" | "danger";
    message: string;
  };

  export let toasts: Toast[] = [];
</script>

<div class="region" aria-live="polite">
  {#each toasts as toast (toast.id)}
    <div class={`toast ${toast.tone}`}>{toast.message}</div>
  {/each}
</div>

<style>
  .region {
    position: fixed;
    right: 1rem;
    bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    z-index: 20;
  }

  .toast {
    min-width: 18rem;
    max-width: 28rem;
    padding: 0.9rem 1rem;
    border-radius: var(--pc-radius-md);
    border: 1px solid var(--pc-border);
    background: rgba(18, 9, 24, 0.95);
    box-shadow: var(--pc-shadow-soft);
    color: var(--pc-text);
  }

  .success {
    border-color: rgba(225, 75, 115, 0.4);
  }

  .warning {
    border-color: rgba(201, 144, 63, 0.45);
  }

  .danger {
    border-color: rgba(216, 75, 95, 0.45);
  }
</style>
