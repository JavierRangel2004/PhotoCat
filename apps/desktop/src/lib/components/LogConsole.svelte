<script lang="ts">
  import { pushToast } from "../stores/app";

  export let lines: string[] = [];
  export let title = "Debug Logs";
  export let open = true;

  async function copyAll() {
    if (!lines.length) {
      pushToast("No logs available to copy.", "warning");
      return;
    }

    await navigator.clipboard.writeText(lines.join("\n"));
    pushToast(`Copied ${lines.length} log lines.`, "success");
  }
</script>

<details class="console-shell" {open}>
  <summary>
    <div class="summary-copy">
      <strong>{title}</strong>
      <span>{lines.length} lines</span>
    </div>
    <button type="button" on:click|stopPropagation={copyAll}>Copy All</button>
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
    background: rgba(6, 7, 11, 0.58);
    overflow: hidden;
  }

  summary {
    list-style: none;
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: center;
    cursor: pointer;
    padding: 0.85rem 0.95rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  summary::-webkit-details-marker {
    display: none;
  }

  .summary-copy {
    display: flex;
    gap: 0.8rem;
    align-items: baseline;
    flex-wrap: wrap;
  }

  strong {
    color: var(--pc-text);
    font-size: 0.92rem;
  }

  summary span {
    color: var(--pc-text-muted);
    font-size: 0.78rem;
  }

  button {
    border: 1px solid var(--pc-border);
    border-radius: 999px;
    padding: 0.4rem 0.7rem;
    color: var(--pc-text);
    background: rgba(255, 255, 255, 0.04);
    font: inherit;
  }

  .console {
    max-height: 22rem;
    overflow: auto;
    padding: 0.9rem;
  }

  .line {
    display: grid;
    grid-template-columns: 3rem 1fr;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .line-no {
    color: var(--pc-text-muted);
    font-family: "Consolas", "SFMono-Regular", monospace;
    font-size: 0.78rem;
    text-align: right;
    user-select: none;
  }

  pre,
  p {
    margin: 0;
    color: #eef3ff;
    font-family: "Consolas", "SFMono-Regular", monospace;
    font-size: 0.82rem;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .empty {
    color: var(--pc-text-muted);
  }

  @media (max-width: 640px) {
    .line {
      grid-template-columns: 1fr;
    }

    .line-no {
      text-align: left;
    }
  }
</style>
