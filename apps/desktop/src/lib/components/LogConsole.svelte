<script lang="ts">
  import { pushToast } from "../stores/app";

  export let lines: string[] = [];
  export let title = "Debug Logs";
  export let open = false;

  async function copyAll() {
    if (!lines.length) {
      pushToast("No logs to copy.", "warning");
      return;
    }
    await navigator.clipboard.writeText(lines.join("\n"));
    pushToast(`Copied ${lines.length} log lines.`, "success");
  }
</script>

<details class="console-shell" {open}>
  <summary>
    <div class="summary-left">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="4 17 10 11 4 5" />
        <line x1="12" y1="19" x2="20" y2="19" />
      </svg>
      <strong>{title}</strong>
      <span class="count">{lines.length}</span>
    </div>
    <button type="button" class="copy-btn" on:click|stopPropagation={copyAll}>Copy</button>
  </summary>

  <div class="console">
    {#if lines.length}
      {#each lines as line, index}
        <div class="line">
          <span class="line-no">{index + 1}</span>
          <pre>{line}</pre>
        </div>
      {/each}
    {:else}
      <p class="empty">No logs yet.</p>
    {/if}
  </div>
</details>

<style>
  .console-shell {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg);
    overflow: hidden;
  }

  summary {
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid var(--pc-border);
    transition: background var(--pc-duration-fast) var(--pc-ease);
  }

  summary:hover {
    background: var(--pc-surface-soft);
  }

  summary::-webkit-details-marker {
    display: none;
  }

  .summary-left {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    color: var(--pc-text-muted);
  }

  [open] .summary-left svg {
    transform: rotate(90deg);
  }

  .summary-left svg {
    transition: transform var(--pc-duration-fast) var(--pc-ease);
  }

  strong {
    color: var(--pc-text-soft);
    font-size: 0.82rem;
    font-weight: 600;
  }

  .count {
    color: var(--pc-text-muted);
    font-size: 0.72rem;
    background: var(--pc-surface);
    padding: 0.1rem 0.4rem;
    border-radius: 999px;
  }

  .copy-btn {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    padding: 0.25rem 0.5rem;
    color: var(--pc-text-muted);
    background: transparent;
    font-size: 0.72rem;
    font-weight: 500;
    cursor: pointer;
    transition: color var(--pc-duration-fast), background var(--pc-duration-fast);
  }

  .copy-btn:hover {
    color: var(--pc-text);
    background: var(--pc-surface-soft);
  }

  .console {
    max-height: 20rem;
    overflow: auto;
    padding: 0.5rem;
  }

  .line {
    display: grid;
    grid-template-columns: 2.5rem 1fr;
    gap: 0.5rem;
  }

  .line-no {
    color: var(--pc-text-muted);
    font-family: var(--pc-font-mono);
    font-size: 0.72rem;
    text-align: right;
    user-select: none;
    opacity: 0.6;
  }

  pre, p {
    margin: 0;
    color: var(--pc-text-soft);
    font-family: var(--pc-font-mono);
    font-size: 0.75rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .empty {
    color: var(--pc-text-muted);
    padding: 0.5rem;
  }
</style>
