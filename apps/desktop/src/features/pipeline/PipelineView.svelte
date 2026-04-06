<script lang="ts">
  import ConfidenceBar from "../../lib/components/ConfidenceBar.svelte";
  import LogConsole from "../../lib/components/LogConsole.svelte";
  import PipelineProgressCard from "../../lib/components/PipelineProgressCard.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import StatusPill from "../../lib/components/StatusPill.svelte";
  import OrganizePanel from "../organize/OrganizePanel.svelte";
  import {
    loadPipelineResultSession,
    pipelineForm,
    pipelinePythonLogs,
    pipelineStatus,
    pipelineSystemLogs,
    runPipeline,
    stopPipeline,
  } from "../../lib/stores/pipeline";

  let formValue = {
    inputDir: "",
    csvOutput: "",
    recursive: true,
    writeXmp: false,
    genreOnly: false,
    noCache: false,
    organize: false,
    dryRun: false,
    minConfidence: 0.55,
    workers: 1,
    extensions: ".jpg,.jpeg,.png,.webp,.tiff",
  };

  const runningStates = new Set(["starting", "running", "stopping"]);

  const unsubscribe = pipelineForm.subscribe((value) => {
    formValue = value;
  });

  $: pythonLines = $pipelinePythonLogs.map((entry) => entry.line);
  $: systemLines = $pipelineSystemLogs.map((entry) => entry.line);
  $: isRunning = runningStates.has($pipelineStatus.state);
  $: canLoadSession = $pipelineStatus.state === "done" && !!$pipelineStatus.csvPath && !!$pipelineStatus.inputDir;
  $: pythonOpen = $pipelineStatus.state === "starting" || $pipelineStatus.state === "running" || $pipelineStatus.state === "error";

  function persistForm() {
    pipelineForm.set(formValue);
  }
</script>

<div class="pipeline-page">
  <header class="page-header">
    <h1>Pipeline</h1>
    <StatusPill value={$pipelineStatus.state} />
  </header>

  <PipelineProgressCard
    state={$pipelineStatus.state}
    progress={$pipelineStatus.progress}
    total={$pipelineStatus.total}
    pythonLogLines={$pipelineStatus.pythonLogLines}
    systemLogLines={$pipelineStatus.systemLogLines}
    message={$pipelineStatus.message}
    error={$pipelineStatus.error}
  />

  {#if canLoadSession}
    <div class="done-card">
      <p>Pipeline complete — CSV ready:</p>
      <pre>{$pipelineStatus.csvPath}</pre>
      <SecondaryButton on:click={loadPipelineResultSession}>Load Session from Output</SecondaryButton>
    </div>
  {/if}

  <div class="form-section">
    <div class="form-grid">
      <label>
        <span>Input directory</span>
        <input bind:value={formValue.inputDir} on:input={persistForm} placeholder="/photos/input" />
      </label>

      <label>
        <span>CSV output</span>
        <input bind:value={formValue.csvOutput} on:input={persistForm} placeholder="/photos/output/audit.csv" />
      </label>
    </div>

    <div class="actions">
      <PrimaryButton disabled={!formValue.inputDir || isRunning} on:click={() => runPipeline(formValue)}>
        {isRunning ? "Running..." : "Run Pipeline"}
      </PrimaryButton>
      <SecondaryButton disabled={!isRunning} on:click={stopPipeline}>Stop</SecondaryButton>
    </div>
  </div>

  <details class="advanced-section">
    <summary>Advanced Options</summary>
    <div class="advanced-content">
      <div class="options-grid">
        <label class="check"><input type="checkbox" bind:checked={formValue.recursive} on:change={persistForm} /> Recursive</label>
        <label class="check"><input type="checkbox" bind:checked={formValue.genreOnly} on:change={persistForm} /> Genre only</label>
        <label class="check"><input type="checkbox" bind:checked={formValue.writeXmp} on:change={persistForm} /> Write XMP</label>
        <label class="check"><input type="checkbox" bind:checked={formValue.noCache} on:change={persistForm} /> No cache</label>
        <label class="check"><input type="checkbox" bind:checked={formValue.organize} on:change={persistForm} /> Organize</label>
        <label class="check"><input type="checkbox" bind:checked={formValue.dryRun} on:change={persistForm} /> Dry run</label>
      </div>
      <div class="form-grid slim">
        <label>
          <span>Min confidence</span>
          <input type="number" min="0" max="1" step="0.01" bind:value={formValue.minConfidence} on:input={persistForm} />
        </label>
        <label>
          <span>Workers</span>
          <input type="number" min="1" step="1" bind:value={formValue.workers} on:input={persistForm} />
        </label>
        <label>
          <span>Extensions</span>
          <input bind:value={formValue.extensions} on:input={persistForm} />
        </label>
      </div>
    </div>
  </details>

  <div class="logs-section">
    <LogConsole lines={pythonLines} title="Python Logs" open={pythonOpen} />
    <LogConsole lines={systemLines} title="System Logs" open={$pipelineStatus.state === "error"} />
  </div>

  <OrganizePanel />
</div>

<style>
  .pipeline-page {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.02em;
  }

  .done-card {
    padding: 0.85rem;
    border-radius: var(--pc-radius-md);
    border: 1px solid rgba(34, 197, 94, 0.25);
    background: rgba(34, 197, 94, 0.06);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .done-card p, .done-card pre {
    margin: 0;
    color: var(--pc-text-soft);
    font-size: 0.85rem;
  }

  .done-card pre {
    word-break: break-word;
    white-space: pre-wrap;
    font-family: var(--pc-font-mono);
    font-size: 0.78rem;
  }

  .form-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-lg);
    background: var(--pc-bg-elevated);
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
  }

  .slim {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  span {
    color: var(--pc-text-muted);
    font-size: 0.78rem;
    font-weight: 500;
  }

  input:not([type="checkbox"]) {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.55rem 0.7rem;
    color: var(--pc-text);
    background: var(--pc-surface);
    font-size: 0.85rem;
    transition: border-color var(--pc-duration-fast) var(--pc-ease);
  }

  input:not([type="checkbox"]):hover {
    border-color: var(--pc-border-strong);
  }

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  /* ── Advanced Collapsible ───────────────────────────────── */
  .advanced-section {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    overflow: hidden;
  }

  .advanced-section summary {
    padding: 0.6rem 0.85rem;
    cursor: pointer;
    color: var(--pc-text-muted);
    font-size: 0.82rem;
    font-weight: 600;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: background var(--pc-duration-fast) var(--pc-ease);
  }

  .advanced-section summary:hover {
    background: var(--pc-surface-soft);
  }

  .advanced-section summary::-webkit-details-marker {
    display: none;
  }

  .advanced-section summary::before {
    content: "▸";
    font-size: 0.7rem;
    transition: transform var(--pc-duration-fast) var(--pc-ease);
  }

  .advanced-section[open] summary::before {
    transform: rotate(90deg);
  }

  .advanced-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.85rem;
    border-top: 1px solid var(--pc-border);
  }

  .options-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .check {
    flex-direction: row;
    align-items: center;
    gap: 0.35rem;
    color: var(--pc-text-soft);
    font-size: 0.85rem;
    cursor: pointer;
  }

  .logs-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  @media (max-width: 768px) {
    .form-grid, .slim {
      grid-template-columns: 1fr;
    }
  }
</style>
