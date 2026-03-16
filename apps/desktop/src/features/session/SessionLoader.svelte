<script lang="ts">
  import Panel from "../../lib/components/Panel.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import { isSessionLoading, loadSession, sessionForm } from "../../lib/stores/review";

  let form = { csvPath: "", imageDir: "" };
  const unsubscribe = sessionForm.subscribe((value) => {
    form = value;
  });

  async function onSubmit() {
    await loadSession(form.csvPath, form.imageDir);
  }
</script>

<Panel eyebrow="Session" title="Load Review Session">
  <div class="copy">
    <p>Open an existing audit CSV and image directory to enter the review workspace.</p>
  </div>

  <div class="grid">
    <label>
      <span>CSV Path</span>
      <input bind:value={form.csvPath} placeholder="C:\photos\output\full_audit.csv" />
    </label>

    <label>
      <span>Image Directory</span>
      <input bind:value={form.imageDir} placeholder="C:\photos\images" />
    </label>
  </div>

  <div class="actions">
    <PrimaryButton disabled={$isSessionLoading || !form.csvPath || !form.imageDir} on:click={onSubmit}>
      {$isSessionLoading ? "Loading..." : "Load Session"}
    </PrimaryButton>
    <SecondaryButton disabled>Electron file picker later</SecondaryButton>
  </div>
</Panel>

<style>
  .copy p {
    margin: 0 0 1rem;
    color: var(--pc-text-muted);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  span {
    color: var(--pc-text-muted);
  }

  input {
    width: 100%;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.95rem 1rem;
    color: var(--pc-text);
    background: rgba(255, 255, 255, 0.04);
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  @media (max-width: 900px) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
