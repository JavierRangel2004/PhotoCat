<script lang="ts">
  import PrimaryButton from "./PrimaryButton.svelte";
  import { isSessionLoading, loadSession, sessionForm } from "../stores/review";

  export let open = false;
  export let onClose: () => void = () => {};

  let form = { csvPath: "", imageDir: "" };
  const unsubscribe = sessionForm.subscribe((value) => {
    form = value;
  });

  async function onSubmit() {
    await loadSession(form.csvPath, form.imageDir);
    onClose();
  }

  function handleBackdrop(event: MouseEvent) {
    if (event.target === event.currentTarget) onClose();
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape") onClose();
  }
</script>

{#if open}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <div class="backdrop" on:click={handleBackdrop} role="dialog" aria-modal="true" aria-label="Load Review Session" tabindex="-1">
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="modal" on:keydown={handleKeydown}>
      <div class="modal-header">
        <h2>Load Session</h2>
        <button class="close-btn" aria-label="Close" on:click={onClose}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <p class="description">Open an existing audit CSV and image directory to enter the review workspace.</p>

      <div class="fields">
        <label>
          <span>CSV Path</span>
          <input
            bind:value={form.csvPath}
            placeholder="/photos/output/full_audit.csv"
            on:keydown={(e) => e.key === "Enter" && form.csvPath && form.imageDir && onSubmit()}
          />
        </label>

        <label>
          <span>Image Directory</span>
          <input
            bind:value={form.imageDir}
            placeholder="/photos/images"
            on:keydown={(e) => e.key === "Enter" && form.csvPath && form.imageDir && onSubmit()}
          />
        </label>
      </div>

      <div class="footer">
        <PrimaryButton
          disabled={$isSessionLoading || !form.csvPath || !form.imageDir}
          on:click={onSubmit}
        >
          {$isSessionLoading ? "Loading..." : "Load Session"}
        </PrimaryButton>
      </div>
    </div>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: grid;
    place-items: center;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    animation: fadeIn var(--pc-duration-fast) var(--pc-ease);
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  .modal {
    width: 100%;
    max-width: 520px;
    margin: 1rem;
    padding: 1.5rem;
    background: var(--pc-bg-elevated);
    border: 1px solid var(--pc-border-strong);
    border-radius: var(--pc-radius-xl);
    box-shadow: var(--pc-shadow);
    animation: slideUp var(--pc-duration-normal) var(--pc-ease);
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  h2 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  .close-btn {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    border: none;
    border-radius: var(--pc-radius-sm);
    background: transparent;
    color: var(--pc-text-muted);
    cursor: pointer;
    transition: color var(--pc-duration-fast) var(--pc-ease),
                background var(--pc-duration-fast) var(--pc-ease);
  }

  .close-btn:hover {
    color: var(--pc-text);
    background: var(--pc-surface);
  }

  .description {
    margin: 0 0 1.25rem;
    color: var(--pc-text-muted);
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .fields {
    display: grid;
    gap: 1rem;
    margin-bottom: 1.25rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  span {
    color: var(--pc-text-muted);
    font-size: 0.8rem;
    font-weight: 500;
  }

  input {
    width: 100%;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.65rem 0.75rem;
    color: var(--pc-text);
    background: var(--pc-surface);
    transition: border-color var(--pc-duration-fast) var(--pc-ease);
  }

  input:hover {
    border-color: var(--pc-border-strong);
  }

  .footer {
    display: flex;
    justify-content: flex-end;
  }
</style>
