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
    setOrganizeMode,
    setReplaceModeAcknowledged,
    setOrganizeOutputDir,
  } from "../../lib/stores/review";

  const previewMoveLimit = 8;

  $: preview = $organizeFlow.preview;
  $: visibleMoves = preview?.moves.slice(0, previewMoveLimit) ?? [];
  $: canRestore = Boolean($organizeFlow.lastManifestPath);
  $: effectiveOutputRoot = preview?.resolved_output_dir?.trim() || $organizeFlow.outputDir.trim();
</script>

<div class="organize">
  <div class="organize-header">
    <h2>Organize & Export</h2>
    <StatusPill
      value={$organizeFlow.hasUnexportedChanges ? "export-required" : preview ? (preview.contract_valid ? "preview-ready" : "preview-invalid") : "waiting"}
    />
  </div>

  <!-- Step 1: Export -->
  <div class="step">
    <div class="step-header">
      <span class="step-num">1</span>
      <span class="step-title">Export Corrected CSV</span>
    </div>
    <div class="step-body">
      <SecondaryButton disabled={!$session || $organizeFlow.exportState === "loading"} on:click={exportCorrected}>
        {$organizeFlow.exportState === "loading" ? "Exporting..." : "Export CSV"}
      </SecondaryButton>
      {#if $organizeFlow.correctedCsvPath}
        <span class="step-status ok">✓ {$organizeFlow.correctedCsvPath}</span>
      {/if}
      {#if $organizeFlow.exportError}
        <span class="step-status error">{$organizeFlow.exportError}</span>
      {/if}
    </div>
  </div>

  <!-- Step 2: Preview -->
  <div class="step">
    <div class="step-header">
      <span class="step-num">2</span>
      <span class="step-title">Preview Organization</span>
    </div>
    <div class="step-body">
      {#if $session}
        <p class="path-hint">
          <span class="path-label">Image root (session)</span>
          <span class="path-value">{$session.imageDir}</span>
        </p>
      {/if}
      <label class="field-inline">
        <span>Output Directory</span>
        <input
          value={$organizeFlow.outputDir}
          on:input={(event) => setOrganizeOutputDir((event.currentTarget as HTMLInputElement).value)}
          placeholder="/path/to/portfolio_root"
        />
      </label>
      <fieldset class="mode-fieldset">
        <legend class="mode-legend">Organize mode</legend>
        <label class="radio-row">
          <input
            type="radio"
            name="organize-mode"
            checked={$organizeFlow.organizeMode === "append_dedupe"}
            on:change={() => setOrganizeMode("append_dedupe")}
          />
          <span>
            Add to portfolio (dedupe by content)
            <span
              class="info-tip"
              title="Uses SHA-256 of file bytes. Same export re-saved as JPEG may not match; perceptual dedupe is not included yet."
            >?</span>
          </span>
        </label>
        <label class="radio-row secondary-mode">
          <input
            type="radio"
            name="organize-mode"
            checked={$organizeFlow.organizeMode === "replace"}
            on:change={() => setOrganizeMode("replace")}
          />
          <span>Replace / rebuild tree (overwrite risk)</span>
        </label>
      </fieldset>
      {#if $organizeFlow.organizeMode === "replace"}
        <label class="warn-check">
          <input
            type="checkbox"
            checked={$organizeFlow.replaceAcknowledged}
            on:change={(event) =>
              setReplaceModeAcknowledged((event.currentTarget as HTMLInputElement).checked)}
          />
          <span>I understand existing files at the same relative paths may be overwritten when moving into the output folder.</span>
        </label>
      {/if}
      <label class="check-inline">
        <input
          type="checkbox"
          checked={$organizeFlow.includeExcluded}
          on:change={(event) => setIncludeExcluded((event.currentTarget as HTMLInputElement).checked)}
        />
        <span>Park excluded files under <code>excluded/</code></span>
      </label>
      <SecondaryButton disabled={!$organizeCanPreview} on:click={requestOrganizePreview}>
        {$organizeFlow.previewState === "loading" ? "Previewing..." : "Run Preview"}
      </SecondaryButton>
      {#if $organizeFlow.previewError}
        <span class="step-status error">{$organizeFlow.previewError}</span>
      {/if}
    </div>
  </div>

  <!-- Preview Results -->
  {#if preview}
    <details class="preview-details" open>
      <summary>
        Preview: {preview.moves.length} moves, {preview.excluded_count} excluded
        {#if !preview.contract_valid} — ⚠ Blocked{/if}
      </summary>
      <div class="preview-content">
        {#if preview.resolved_csv_path}
          <p class="path-hint">
            <span class="path-label">Resolved CSV</span>
            <span class="path-value">{preview.resolved_csv_path}</span>
          </p>
        {/if}
        {#if preview.resolved_output_dir}
          <p class="path-hint commit-target">
            <span class="path-label">Commit will write under</span>
            <span class="path-value">{preview.resolved_output_dir}</span>
          </p>
        {/if}
        <div class="stat-row">
          <div class="mini-stat"><span>Total</span><strong>{preview.total}</strong></div>
          <div class="mini-stat"><span>Moves</span><strong>{preview.moves.length}</strong></div>
          <div class="mini-stat"><span>Excluded</span><strong>{preview.excluded_count}</strong></div>
          <div class="mini-stat"><span>Missing</span><strong>{preview.missing.length}</strong></div>
          <div class="mini-stat"><span>Conflicts</span><strong>{preview.conflicts.length}</strong></div>
        </div>
        {#if preview.mode === "append_dedupe" && (preview.dedupe_skipped_duplicate ?? 0) + (preview.dedupe_renamed_collision ?? 0) > 0}
          <div class="stat-row dedupe-row">
            <div class="mini-stat">
              <span>Dedupe skips</span><strong>{preview.dedupe_skipped_duplicate ?? 0}</strong>
            </div>
            <div class="mini-stat">
              <span>Renamed (collision)</span><strong>{preview.dedupe_renamed_collision ?? 0}</strong>
            </div>
          </div>
        {/if}

        {#if Object.keys(preview.counts_by_category).length}
          <div class="category-list">
            {#each Object.entries(preview.counts_by_category) as [category, count]}
              <div class="cat-row"><span>{category}</span><strong>{count}</strong></div>
            {/each}
          </div>
        {/if}

        {#if visibleMoves.length}
          <div class="move-list">
            <p class="move-hint">Showing {visibleMoves.length} of {preview.moves.length}</p>
            {#each visibleMoves as move}
              <div class="move-row">
                <strong>{move.filename}</strong>
                <span>{move.portfolio_category} → {joinOutputPath(effectiveOutputRoot, move.dest_relpath)}</span>
              </div>
            {/each}
          </div>
        {/if}

        {#if preview.errors.length}
          <div class="issue-list">
            {#each preview.errors as err}
              <p class="step-status error">{err}</p>
            {/each}
          </div>
        {/if}
      </div>
    </details>
  {/if}

  <!-- Step 3: Commit -->
  <div class="step">
    <div class="step-header">
      <span class="step-num">3</span>
      <span class="step-title">Commit</span>
    </div>
    <div class="step-body">
      <div class="btn-group">
        <PrimaryButton disabled={!$organizeCanCommit} on:click={commitOrganize}>
          {$organizeFlow.isCommitting
            ? "Committing..."
            : $organizeFlow.organizeMode === "replace"
              ? "Commit (replace mode)"
              : "Add to portfolio (commit)"}
        </PrimaryButton>
        <SecondaryButton disabled={!canRestore || $organizeFlow.isRestoring} on:click={restoreLastOrganize}>
          {$organizeFlow.isRestoring ? "Restoring..." : "Restore Last"}
        </SecondaryButton>
      </div>
      {#if $organizeFlow.commitResult}
        <span class="step-status ok">
          Moved {$organizeFlow.commitResult.moved}, skipped {$organizeFlow.commitResult.skipped}
          {#if ($organizeFlow.commitResult.dedupe_skipped_duplicate ?? 0) > 0}
            , dedupe skipped {$organizeFlow.commitResult.dedupe_skipped_duplicate}
          {/if}
          {#if ($organizeFlow.commitResult.dedupe_renamed_collision ?? 0) > 0}
            , renamed {$organizeFlow.commitResult.dedupe_renamed_collision}
          {/if}
        </span>
      {/if}
      {#if $organizeFlow.restoreResult}
        <span class="step-status ok">
          Restored {$organizeFlow.restoreResult.restored}
        </span>
      {/if}
    </div>
  </div>

  {#if $organizeFlow.hasUnexportedChanges}
    <p class="banner warning">Changes are newer than the last export. Re-export before previewing or committing.</p>
  {/if}
</div>

<style>
  .organize {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding-top: 0.5rem;
    border-top: 1px solid var(--pc-border);
    margin-top: 0.5rem;
  }

  .organize-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }

  h2 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
  }

  /* ── Steps ───────────────────────────────────────────────── */
  .step {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem 0.85rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-bg-elevated);
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .step-num {
    display: grid;
    place-items: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--pc-primary-glow);
    color: var(--pc-primary);
    font-size: 0.72rem;
    font-weight: 700;
    flex-shrink: 0;
  }

  .step-title {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--pc-text);
  }

  .step-body {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-left: 1.9rem;
  }

  .step-status {
    font-size: 0.78rem;
    word-break: break-all;
  }

  .step-status.ok {
    color: var(--pc-success);
  }

  .step-status.error {
    color: var(--pc-danger);
  }

  .btn-group {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .field-inline {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .field-inline span {
    color: var(--pc-text-muted);
    font-size: 0.78rem;
    font-weight: 500;
  }

  .field-inline input {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.5rem 0.65rem;
    color: var(--pc-text);
    background: var(--pc-surface);
    font-size: 0.85rem;
  }

  .check-inline {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--pc-text-soft);
    font-size: 0.82rem;
    cursor: pointer;
  }

  .check-inline code {
    color: var(--pc-text-muted);
    font-family: var(--pc-font-mono);
    font-size: 0.78rem;
  }

  /* ── Preview Details ─────────────────────────────────────── */
  .preview-details {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    overflow: hidden;
  }

  .preview-details summary {
    padding: 0.6rem 0.85rem;
    cursor: pointer;
    color: var(--pc-text-soft);
    font-size: 0.82rem;
    font-weight: 600;
    list-style: none;
    transition: background var(--pc-duration-fast) var(--pc-ease);
  }

  .preview-details summary:hover {
    background: var(--pc-surface-soft);
  }

  .preview-details summary::-webkit-details-marker {
    display: none;
  }

  .preview-content {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
    padding: 0.85rem;
    border-top: 1px solid var(--pc-border);
  }

  .stat-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .mini-stat {
    display: flex;
    align-items: baseline;
    gap: 0.25rem;
  }

  .mini-stat span {
    color: var(--pc-text-muted);
    font-size: 0.72rem;
    text-transform: uppercase;
  }

  .mini-stat strong {
    font-size: 0.9rem;
    color: var(--pc-text);
  }

  .category-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .cat-row {
    display: flex;
    align-items: baseline;
    gap: 0.3rem;
    padding: 0.2rem 0.5rem;
    border-radius: var(--pc-radius-sm);
    background: var(--pc-surface);
    font-size: 0.78rem;
  }

  .cat-row span {
    color: var(--pc-text-muted);
  }

  .cat-row strong {
    color: var(--pc-text);
  }

  .move-list {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .move-hint {
    margin: 0;
    color: var(--pc-text-muted);
    font-size: 0.72rem;
  }

  .move-row {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    padding: 0.4rem 0.5rem;
    border-radius: var(--pc-radius-sm);
    background: var(--pc-surface);
    font-size: 0.78rem;
  }

  .move-row strong {
    color: var(--pc-text);
        font-weight: 600;
  }

  .move-row span {
    color: var(--pc-text-muted);
    word-break: break-all;
  }

  .issue-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .issue-list p {
    margin: 0;
  }

  .banner {
    margin: 0;
    padding: 0.55rem 0.75rem;
    border-radius: var(--pc-radius-md);
    font-size: 0.82rem;
  }

  .warning {
    color: var(--pc-warning);
    border: 1px solid rgba(245, 158, 11, 0.25);
    background: rgba(245, 158, 11, 0.06);
  }

  .path-hint {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    font-size: 0.76rem;
  }

  .path-hint.commit-target .path-value {
    color: var(--pc-primary);
    font-weight: 600;
  }

  .path-label {
    color: var(--pc-text-muted);
    text-transform: uppercase;
    font-size: 0.68rem;
    letter-spacing: 0.03em;
  }

  .path-value {
    color: var(--pc-text-soft);
    word-break: break-all;
    font-family: var(--pc-font-mono);
  }

  .mode-fieldset {
    margin: 0;
    padding: 0.5rem 0.65rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: var(--pc-surface);
  }

  .mode-legend {
    padding: 0 0.25rem;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--pc-text-muted);
  }

  .radio-row {
    display: flex;
    align-items: flex-start;
    gap: 0.45rem;
    font-size: 0.82rem;
    color: var(--pc-text);
    cursor: pointer;
    margin: 0.35rem 0 0;
  }

  .radio-row.secondary-mode {
    color: var(--pc-text-soft);
    font-size: 0.8rem;
  }

  .radio-row input {
    margin-top: 0.2rem;
    flex-shrink: 0;
  }

  .info-tip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1rem;
    height: 1rem;
    margin-left: 0.2rem;
    border-radius: 50%;
    background: var(--pc-surface-soft);
    color: var(--pc-text-muted);
    font-size: 0.65rem;
    font-weight: 700;
    cursor: help;
    vertical-align: middle;
  }

  .warn-check {
    display: flex;
    align-items: flex-start;
    gap: 0.45rem;
    font-size: 0.78rem;
    color: var(--pc-warning);
    cursor: pointer;
    margin: 0;
    padding: 0.45rem 0.55rem;
    border-radius: var(--pc-radius-md);
    border: 1px solid rgba(245, 158, 11, 0.35);
    background: rgba(245, 158, 11, 0.06);
  }

  .warn-check input {
    margin-top: 0.15rem;
    flex-shrink: 0;
  }

  .dedupe-row .mini-stat span {
    color: var(--pc-text-muted);
  }
</style>
