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
            ? "primary"
            : value === "stopping"
              ? "warning"
            : "neutral";
</script>

<span class={`pill ${tone}`}>{value || "idle"}</span>

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 0.42rem 0.72rem;
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: rgba(255, 255, 255, 0.04);
    color: var(--pc-text-soft);
    border: 1px solid var(--pc-border);
  }

  .primary {
    color: #ffd7e0;
    border-color: rgba(191, 39, 66, 0.45);
    background: rgba(158, 27, 50, 0.18);
  }

  .warning {
    color: #ffe7b8;
    border-color: rgba(201, 144, 63, 0.45);
    background: rgba(201, 144, 63, 0.14);
  }

  .danger {
    color: #ffd4da;
    border-color: rgba(216, 75, 95, 0.45);
    background: rgba(216, 75, 95, 0.14);
  }

  .success {
    color: #ffd8e5;
    border-color: rgba(225, 75, 115, 0.45);
    background: rgba(225, 75, 115, 0.16);
  }
</style>
