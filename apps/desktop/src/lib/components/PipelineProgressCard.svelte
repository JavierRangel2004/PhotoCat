<script lang="ts">
  import ConfidenceBar from "./ConfidenceBar.svelte";
  import StatusPill from "./StatusPill.svelte";

  export let state: "idle" | "starting" | "running" | "stopping" | "done" | "error" = "idle";
  export let progress = 0;
  export let total = 0;
  /* Accept but ignore legacy props passed by callers */
  export let pythonLogLines: unknown = undefined;
  export let systemLogLines: unknown = undefined;
  export let message: string | undefined = undefined;
  export let error: string | undefined = undefined;

  $: ratio = total > 0 ? progress / total : 0;
</script>

<div class="card">
  <div class="header">
    <div class="header-left">
      <StatusPill value={state} />
      <span class="caption">
        {state === "error"
          ? "Pipeline failed"
          : total > 0
          ? `${progress} of ${total} processed`
          : message || "Ready"}
      </span>
    </div>
    <strong class="pct">{total > 0 ? `${Math.round(ratio * 100)}%` : ""}</strong>
  </div>

  <ConfidenceBar label="Progress" value={ratio} />

  {#if error}
    <p class="error">{error}</p>
  {/if}
</div>

<style>
  .card {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    padding: 0.85rem 1rem;
    border-radius: var(--pc-radius-lg);
    border: 1px solid var(--pc-border);
    background: var(--pc-bg-elevated);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .caption {
    color: var(--pc-text-muted);
    font-size: 0.8rem;
  }

  .pct {
    color: var(--pc-text);
    font-size: 0.9rem;
    font-weight: 700;
  }

  .error {
    margin: 0;
    color: var(--pc-danger);
    font-size: 0.82rem;
    line-height: 1.45;
  }
</style>
