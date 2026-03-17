<script lang="ts">
  import ConfidenceBar from "../../lib/components/ConfidenceBar.svelte";
  import LogConsole from "../../lib/components/LogConsole.svelte";
  import Panel from "../../lib/components/Panel.svelte";
  import PipelineProgressCard from "../../lib/components/PipelineProgressCard.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import StatusPill from "../../lib/components/StatusPill.svelte";
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

<Panel eyebrow="Pipeline" title="Run And Monitor">
  <div class="top">
    <StatusPill value={$pipelineStatus.state} />
    <div class="progress-wrap">
      <ConfidenceBar
        label="Progress"
        value={$pipelineStatus.total ? $pipelineStatus.progress / $pipelineStatus.total : 0}
      />
      <span class="progress-caption">
        {$pipelineStatus.state === "error"
          ? "Pipeline failed. Check details below."
          : $pipelineStatus.total
          ? `${$pipelineStatus.progress} of ${$pipelineStatus.total}`
          : $pipelineStatus.message || "Waiting for pipeline progress"}
      </span>
    </div>
  </div>

  <PipelineProgressCard
    state={$pipelineStatus.state}
    progress={$pipelineStatus.progress}
    total={$pipelineStatus.total}
    pythonLogLines={$pipelineStatus.pythonLogLines}
    systemLogLines={$pipelineStatus.systemLogLines}
    message={$pipelineStatus.message}
    error={$pipelineStatus.error}
  />

  {#if $pipelineStatus.state === "starting" && !$pipelineStatus.hasPythonOutput}
    <p class="banner warning">Python process was launched. Waiting for first output line...</p>
  {/if}

  {#if canLoadSession}
    <div class="done-card">
      <p>Pipeline completed. CSV ready at:</p>
      <pre>{$pipelineStatus.csvPath}</pre>
      <SecondaryButton on:click={loadPipelineResultSession}>Load Session From Output</SecondaryButton>
    </div>
  {/if}

  <div class="grid">
    <label>
      <span>Input directory</span>
      <input bind:value={formValue.inputDir} on:input={persistForm} placeholder="C:\photos\input" />
    </label>

    <label>
      <span>CSV output</span>
      <input bind:value={formValue.csvOutput} on:input={persistForm} placeholder="C:\photos\output\audit.csv" />
    </label>
  </div>

  <div class="options">
    <label><input type="checkbox" bind:checked={formValue.recursive} on:change={persistForm} /> Recursive</label>
    <label><input type="checkbox" bind:checked={formValue.genreOnly} on:change={persistForm} /> Genre only</label>
    <label><input type="checkbox" bind:checked={formValue.writeXmp} on:change={persistForm} /> Write XMP</label>
    <label><input type="checkbox" bind:checked={formValue.noCache} on:change={persistForm} /> No cache</label>
    <label><input type="checkbox" bind:checked={formValue.organize} on:change={persistForm} /> Organize</label>
    <label><input type="checkbox" bind:checked={formValue.dryRun} on:change={persistForm} /> Dry run</label>
  </div>

  <div class="grid slim">
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

  <div class="actions">
    <PrimaryButton disabled={!formValue.inputDir || isRunning} on:click={() => runPipeline(formValue)}>Run Pipeline</PrimaryButton>
    <SecondaryButton disabled={!isRunning} on:click={stopPipeline}>Stop</SecondaryButton>
  </div>

  <div class="logs">
    <LogConsole lines={pythonLines} title="Python Pipeline Logs" open={pythonOpen} />
    <LogConsole lines={systemLines} title="System And Lifecycle Logs" open={$pipelineStatus.state === "error"} />
  </div>
</Panel>

<style>
  .top {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 1rem;
    align-items: center;
    margin-bottom: 1rem;
  }

  .progress-wrap {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .progress-caption {
    color: var(--pc-text-muted);
    font-size: 0.8rem;
  }

  .banner {
    margin: 0 0 1rem;
    padding: 0.75rem 0.9rem;
    border-radius: var(--pc-radius-md);
    border: 1px solid var(--pc-border);
  }

  .warning {
    color: #ffe7b8;
    border-color: rgba(201, 144, 63, 0.35);
    background: rgba(201, 144, 63, 0.12);
  }

  .done-card {
    margin-bottom: 1rem;
    padding: 0.9rem;
    border-radius: var(--pc-radius-md);
    border: 1px solid rgba(225, 75, 115, 0.34);
    background: rgba(225, 75, 115, 0.1);
    display: grid;
    gap: 0.65rem;
  }

  .done-card p,
  .done-card pre {
    margin: 0;
    color: var(--pc-text-soft);
  }

  .done-card pre {
    word-break: break-word;
    white-space: pre-wrap;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .slim {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .options {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
    color: var(--pc-text-soft);
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .options label {
    flex-direction: row;
    align-items: center;
  }

  span {
    color: var(--pc-text-muted);
  }

  input {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    padding: 0.8rem 0.9rem;
    color: var(--pc-text);
    background: rgba(255, 255, 255, 0.04);
  }

  .actions {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .logs {
    display: grid;
    gap: 0.8rem;
  }

  @media (max-width: 980px) {
    .top,
    .grid,
    .slim {
      grid-template-columns: 1fr;
    }
  }
</style>
