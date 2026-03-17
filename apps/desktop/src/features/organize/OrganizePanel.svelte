<script lang="ts">
  import Panel from "../../lib/components/Panel.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import StatusPill from "../../lib/components/StatusPill.svelte";
  import { joinOutputPath } from "../../lib/review/portfolioMapping";
  import {
    commitOrganize,
    exportCorrected,
    organizeCanCommit,
    organizeCanPreview,
    organizeFlow,
    requestOrganizePreview,
    restoreLastOrganize,
    session,
    setIncludeExcluded,
    setOrganizeOutputDir,
  } from "../../lib/stores/review";

  const previewMoveLimit = 12;

  $: preview = $organizeFlow.preview;
  $: visibleMoves = preview?.moves.slice(0, previewMoveLimit) ?? [];
  $: previewHasWarnings = Boolean(preview && (preview.missing.length || preview.conflicts.length || preview.invalid_destinations.length));
  $: canRestore = Boolean($organizeFlow.lastManifestPath);
</script>

<Panel eyebrow="Organize" title="Corrected CSV Flow">
  <div class="head">
    <div>
      <p class="copy">
        Export the corrected CSV, preview the exact destination plan, then commit the organize step.
        The UI now uses the corrected CSV contract instead of the legacy in-memory preview.
      </p>
      {#if $session}
        <p class="meta">Review session: {$session.csvPath}</p>
      {/if}
      {#if $organizeFlow.correctedCsvPath}
        <p class="meta">Corrected CSV: {$organizeFlow.correctedCsvPath}</p>
      {/if}
    </div>
    <StatusPill
      value={$organizeFlow.hasUnexportedChanges ? "export-required" : preview ? (preview.contract_valid ? "preview-ready" : "preview-invalid") : "waiting"}
    />
  </div>

  <div class="controls">
    <label class="field">
      <span>Output Directory</span>
      <input
        value={$organizeFlow.outputDir}
        on:input={(event) => setOrganizeOutputDir((event.currentTarget as HTMLInputElement).value)}
        placeholder="C:\portfolio\staging"
      />
    </label>

    <label class="checkbox">
      <input
        type="checkbox"
        checked={$organizeFlow.includeExcluded}
        on:change={(event) => setIncludeExcluded((event.currentTarget as HTMLInputElement).checked)}
      />
      <span>Park excluded files under `excluded/` during commit</span>
    </label>
  </div>

  <div class="actions">
    <SecondaryButton disabled={!$session || $organizeFlow.exportState === "loading"} on:click={exportCorrected}>
      {$organizeFlow.exportState === "loading" ? "Exporting..." : "Export Corrected CSV"}
    </SecondaryButton>
    <SecondaryButton disabled={!$organizeCanPreview} on:click={requestOrganizePreview}>
      {$organizeFlow.previewState === "loading" ? "Previewing..." : "Run Preview"}
    </SecondaryButton>
    <PrimaryButton disabled={!$organizeCanCommit} on:click={commitOrganize}>
      {$organizeFlow.isCommitting ? "Committing..." : "Commit Organize"}
    </PrimaryButton>
    <SecondaryButton disabled={!canRestore || $organizeFlow.isRestoring} on:click={restoreLastOrganize}>
      {$organizeFlow.isRestoring ? "Restoring..." : "Restore Last Commit"}
    </SecondaryButton>
  </div>

  {#if $organizeFlow.hasUnexportedChanges}
    <p class="banner warning">Review changes are newer than the last corrected CSV export. Export again before preview or commit.</p>
  {/if}

  {#if $organizeFlow.exportError}
    <p class="banner danger">Export failed: {$organizeFlow.exportError}</p>
  {/if}

  {#if $organizeFlow.previewError}
    <p class="banner danger">Preview failed: {$organizeFlow.previewError}</p>
  {/if}

  {#if preview}
    <div class="summary-grid">
      <div class="summary-card">
        <span>Total Rows</span>
        <strong>{preview.total}</strong>
      </div>
      <div class="summary-card">
        <span>Included Moves</span>
        <strong>{preview.moves.length}</strong>
      </div>
      <div class="summary-card">
        <span>Excluded</span>
        <strong>{preview.excluded_count}</strong>
      </div>
      <div class="summary-card">
        <span>Missing</span>
        <strong>{preview.missing.length}</strong>
      </div>
      <div class="summary-card">
        <span>Conflicts</span>
        <strong>{preview.conflicts.length}</strong>
      </div>
      <div class="summary-card">
        <span>Contract</span>
        <strong>{preview.contract_valid ? "Valid" : "Blocked"}</strong>
      </div>
    </div>

    <div class="sections">
      <section class="card">
        <h3>Portfolio Contract</h3>
        <p class="meta">Allowed categories: {preview.allowed_photo_categories.join(", ")}</p>
        <p class="meta">Present in preview: {preview.present_photo_categories.join(", ") || "none"}</p>
        <p class="meta">Preview manifest: {preview.manifest_path_preview}</p>
        {#if preview.errors.length}
          <ul class="issues">
            {#each preview.errors as error}
              <li>{error}</li>
            {/each}
          </ul>
        {:else}
          <p class="ok">Preview contract checks passed.</p>
        {/if}
      </section>

      <section class="card">
        <h3>Counts By Category</h3>
        {#if Object.keys(preview.counts_by_category).length}
          <ul class="counts">
            {#each Object.entries(preview.counts_by_category) as [category, count]}
              <li>
                <span>{category}</span>
                <strong>{count}</strong>
              </li>
            {/each}
          </ul>
        {:else}
          <p class="meta">No included portfolio moves in this preview.</p>
        {/if}
      </section>

      <section class="card wide">
        <h3>Exact Destination Preview</h3>
        <p class="meta">
          Showing the first {visibleMoves.length} of {preview.moves.length} included files.
        </p>
        {#if visibleMoves.length}
          <div class="move-list">
            {#each visibleMoves as move}
              <div class="move-row">
                <div>
                  <strong>{move.filename}</strong>
                  <small>{move.portfolio_category}</small>
                </div>
                <div class="paths">
                  <span>{move.source_path}</span>
                  <strong>{joinOutputPath($organizeFlow.outputDir, move.dest_relpath)}</strong>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="meta">No included moves to preview.</p>
        {/if}
      </section>

      {#if preview.invalid_destinations.length}
        <section class="card wide">
          <h3>Invalid Destinations</h3>
          <ul class="issues">
            {#each preview.invalid_destinations as entry}
              <li>{entry.filename}: {entry.reason} ({entry.dest_relpath})</li>
            {/each}
          </ul>
        </section>
      {/if}

      {#if preview.missing.length}
        <section class="card">
          <h3>Missing Files</h3>
          <ul class="issues">
            {#each preview.missing as entry}
              <li>{entry.filename}: {entry.source_path}</li>
            {/each}
          </ul>
        </section>
      {/if}

      {#if preview.conflicts.length}
        <section class="card">
          <h3>Destination Conflicts</h3>
          <ul class="issues">
            {#each preview.conflicts as conflict}
              <li>{conflict.dest_path}: {conflict.sources.length} source files</li>
            {/each}
          </ul>
        </section>
      {/if}
    </div>
  {:else if !$session}
    <p class="meta">Load a review session to unlock the corrected CSV organize flow.</p>
  {/if}

  {#if $organizeFlow.commitResult}
    <section class="card">
      <h3>Last Commit</h3>
      <p class="meta">Manifest: {$organizeFlow.commitResult.manifest_path}</p>
      <p class="meta">
        Moved {$organizeFlow.commitResult.moved}, skipped {$organizeFlow.commitResult.skipped},
        missing {$organizeFlow.commitResult.missing}, conflicts {$organizeFlow.commitResult.conflicts}.
      </p>
      {#if $organizeFlow.commitResult.errors.length}
        <ul class="issues">
          {#each $organizeFlow.commitResult.errors as error}
            <li>{error}</li>
          {/each}
        </ul>
      {:else}
        <p class="ok">Commit completed without organizer errors.</p>
      {/if}
    </section>
  {/if}

  {#if $organizeFlow.restoreResult}
    <section class="card">
      <h3>Last Restore</h3>
      <p class="meta">Restored {$organizeFlow.restoreResult.restored}, missing {$organizeFlow.restoreResult.missing}.</p>
      {#if $organizeFlow.restoreResult.errors.length}
        <ul class="issues">
          {#each $organizeFlow.restoreResult.errors as error}
            <li>{error}</li>
          {/each}
        </ul>
      {:else}
        <p class="ok">Restore completed without errors.</p>
      {/if}
    </section>
  {/if}
</Panel>

<style>
  .head {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 1rem;
    align-items: start;
  }

  .copy,
  .meta,
  .ok {
    margin: 0;
  }

  .copy {
    color: var(--pc-text-soft);
    line-height: 1.55;
  }

  .meta {
    color: var(--pc-text-muted);
    word-break: break-word;
  }

  .controls,
  .sections,
  .summary-grid {
    margin-top: 1rem;
  }

  .controls {
    display: grid;
    gap: 0.9rem;
  }

  .field,
  .checkbox {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .checkbox {
    flex-direction: row;
    align-items: center;
  }

  input:not([type="checkbox"]) {
    width: 100%;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    padding: 0.8rem 0.9rem;
    color: var(--pc-text);
    background: rgba(255, 255, 255, 0.04);
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  .banner {
    margin: 1rem 0 0;
    padding: 0.8rem 0.9rem;
    border-radius: var(--pc-radius-md);
    border: 1px solid var(--pc-border);
  }

  .warning {
    color: #ffe7b8;
    border-color: rgba(201, 144, 63, 0.35);
    background: rgba(201, 144, 63, 0.12);
  }

  .danger {
    color: #ffc4d0;
    border-color: rgba(186, 59, 85, 0.35);
    background: rgba(186, 59, 85, 0.12);
  }

  .summary-grid,
  .sections {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .summary-card,
  .card {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: rgba(255, 255, 255, 0.03);
    padding: 1rem;
    display: grid;
    gap: 0.55rem;
  }

  .summary-card span,
  .field span {
    color: var(--pc-text-muted);
  }

  .summary-card strong,
  .card h3 {
    margin: 0;
  }

  .counts,
  .issues {
    margin: 0;
    padding-left: 1.1rem;
    color: var(--pc-text-soft);
  }

  .counts li {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }

  .move-list {
    display: grid;
    gap: 0.75rem;
  }

  .move-row {
    display: grid;
    gap: 0.45rem;
    padding: 0.9rem;
    border-radius: var(--pc-radius-sm);
    background: rgba(255, 255, 255, 0.03);
  }

  .move-row small,
  .paths span {
    color: var(--pc-text-muted);
  }

  .paths {
    display: grid;
    gap: 0.25rem;
    word-break: break-word;
  }

  .ok {
    color: #bfe3c0;
  }

  @media (min-width: 960px) {
    .summary-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .sections {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .wide {
      grid-column: 1 / -1;
    }
  }
</style>
