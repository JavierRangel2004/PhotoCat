<script lang="ts">
  import ConfidenceBar from "./ConfidenceBar.svelte";
  import StatusPill from "./StatusPill.svelte";

  export let state: "idle" | "starting" | "running" | "stopping" | "done" | "error" = "idle";
  export let progress = 0;
  export let total = 0;
  export let pythonLogLines = 0;
  export let systemLogLines = 0;
  export let message: string | undefined = undefined;
  export let error: string | undefined = undefined;

  $: ratio = total > 0 ? progress / total : 0;
  $: remaining = total > 0 ? Math.max(total - progress, 0) : 0;
</script>

<div class="card">
  <div class="header">
    <div>
      <p class="kicker">Pipeline Snapshot</p>
      <h3>{total > 0 ? `${progress} / ${total}` : state === "running" ? "Preparing run" : "Waiting for run"}</h3>
    </div>
    <StatusPill value={state} />
  </div>

  <ConfidenceBar label="Completion" value={ratio} />

  <div class="stats">
    <div>
      <span>Processed</span>
      <strong>{progress}</strong>
    </div>
    <div>
      <span>Remaining</span>
      <strong>{remaining}</strong>
    </div>
    <div>
      <span>Python logs</span>
      <strong>{pythonLogLines}</strong>
    </div>
    <div>
      <span>System logs</span>
      <strong>{systemLogLines}</strong>
    </div>
  </div>

  {#if message && message !== error}
    <p class="message">{message}</p>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}
</div>

<style>
  .card {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    padding: 1rem 1.05rem;
    border-radius: var(--pc-radius-lg);
    border: 1px solid var(--pc-border);
    background:
      radial-gradient(circle at top right, rgba(191, 39, 66, 0.18), transparent 28%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02));
  }

  .header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: start;
  }

  .kicker,
  h3,
  .error {
    margin: 0;
  }

  .kicker {
    color: var(--pc-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    font-weight: 700;
  }

  h3 {
    margin-top: 0.35rem;
    font-size: 1.3rem;
    line-height: 1;
  }

  .stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.8rem;
  }

  .stats div {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .stats span {
    color: var(--pc-text-muted);
    font-size: 0.78rem;
  }

  .stats strong {
    font-size: 1rem;
    color: var(--pc-text);
  }

  .error {
    color: #ffc4d0;
    line-height: 1.5;
  }

  .message {
    margin: 0;
    color: var(--pc-text-soft);
    line-height: 1.5;
  }

  @media (max-width: 640px) {
    .stats {
      grid-template-columns: 1fr;
    }
  }
</style>
