<script lang="ts">
  import ConfidenceBar from "../../lib/components/ConfidenceBar.svelte";
  import LogConsole from "../../lib/components/LogConsole.svelte";
  import Panel from "../../lib/components/Panel.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import StatusPill from "../../lib/components/StatusPill.svelte";
  import { pipelineForm, pipelineLogs, pipelineStatus, runPipeline, stopPipeline } from "../../lib/stores/pipeline";

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

  const unsubscribe = pipelineForm.subscribe((value) => {
    formValue = value;
  });

  function persistForm() {
    pipelineForm.set(formValue);
  }
</script>

<Panel eyebrow="Pipeline" title="Run And Monitor">
  <div class="top">
    <StatusPill value={$pipelineStatus.state} />
    <ConfidenceBar
      label="Progress"
      value={$pipelineStatus.total ? $pipelineStatus.progress / $pipelineStatus.total : 0}
    />
  </div>

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
    <PrimaryButton disabled={!formValue.inputDir} on:click={() => runPipeline(formValue)}>Run Pipeline</PrimaryButton>
    <SecondaryButton on:click={stopPipeline}>Stop</SecondaryButton>
  </div>

  <LogConsole lines={$pipelineLogs} />
</Panel>

<style>
  .top {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 1rem;
    align-items: center;
    margin-bottom: 1rem;
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

  @media (max-width: 980px) {
    .top,
    .grid,
    .slim {
      grid-template-columns: 1fr;
    }
  }
</style>
