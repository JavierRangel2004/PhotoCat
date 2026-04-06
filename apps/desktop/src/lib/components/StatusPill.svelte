<script lang="ts">
  export let value = "";

  $: tone =
    value === "review"
      ? "warning"
      : value === "wrong"
        ? "danger"
        : value === "correct" || value === "done"
          ? "success"
          : value === "running" || value === "starting"
            ? "running"
            : value === "stopping"
              ? "warning"
              : value === "export-required"
                ? "warning"
                : value === "preview-ready"
                  ? "success"
                  : "neutral";
</script>

<span class={`pill ${tone}`}>{value || "idle"}</span>

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 0.25rem 0.55rem;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background: var(--pc-surface);
    color: var(--pc-text-muted);
    border: 1px solid var(--pc-border);
    white-space: nowrap;
  }

  .running {
    color: var(--pc-primary);
    border-color: rgba(20, 184, 166, 0.3);
    background: rgba(20, 184, 166, 0.1);
  }

  .warning {
    color: var(--pc-warning);
    border-color: rgba(245, 158, 11, 0.3);
    background: rgba(245, 158, 11, 0.08);
  }

  .danger {
    color: var(--pc-danger);
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.08);
  }

  .success {
    color: var(--pc-success);
    border-color: rgba(34, 197, 94, 0.3);
    background: rgba(34, 197, 94, 0.08);
  }
</style>
