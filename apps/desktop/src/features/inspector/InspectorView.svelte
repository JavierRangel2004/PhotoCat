<script lang="ts">
  import { desktopApi } from "../../lib/api";
  import DecisionRail from "../../lib/components/DecisionRail.svelte";
  import EvidenceCard from "../../lib/components/EvidenceCard.svelte";
  import Filmstrip from "../../lib/components/Filmstrip.svelte";
  import Panel from "../../lib/components/Panel.svelte";
  import PrimaryButton from "../../lib/components/PrimaryButton.svelte";
  import SecondaryButton from "../../lib/components/SecondaryButton.svelte";
  import { activeItem, approveModelDecision, exportCorrected, refreshOrganizePreview, selectItem, session, setGenre, visibleItems } from "../../lib/stores/review";

  let selectedGenre = "";
  let activeIndex = -1;

  $: if ($activeItem) {
    selectedGenre = $activeItem.userGenre || $activeItem.finalGenre;
  }

  $: imageUrl = $activeItem?.imagePath ? desktopApi.assetUrl($activeItem.imagePath) : "";
  $: activeIndex = $activeItem ? $visibleItems.findIndex((item) => item.id === $activeItem.id) : -1;
  $: previousItem = activeIndex > 0 ? $visibleItems[activeIndex - 1] : null;
  $: nextItem = activeIndex >= 0 && activeIndex < $visibleItems.length - 1 ? $visibleItems[activeIndex + 1] : null;

  function move(delta: number) {
    if (!$activeItem || !$visibleItems.length) return;
    const index = $visibleItems.findIndex((item) => item.id === $activeItem.id);
    const next = $visibleItems[index + delta];
    if (next) selectItem(next.id);
  }

  function applySelectedGenre() {
    if (!$activeItem) return;
    setGenre($activeItem.id, selectedGenre);
  }
</script>

<div class="inspector">
  <Panel eyebrow="Inspector" title="Active Review Item">
    {#if $activeItem}
      <div class="workspace">
        <div class="stage">
          {#if imageUrl}
            <img src={imageUrl} alt={$activeItem.filename} />
          {:else}
            <div class="missing">Image missing at {$activeItem.imagePathDisplay}</div>
          {/if}
        </div>

        <div class="rail">
          <DecisionRail
            item={$activeItem}
            currentPosition={activeIndex + 1}
            totalVisible={$visibleItems.length}
          />

          <div class="control-card">
            <label>
              <span>Override Genre</span>
              <div class="select-wrap">
                <select bind:value={selectedGenre}>
                  <option value={$activeItem.finalGenre}>Use model genre: {$activeItem.finalGenre}</option>
                  {#each $session?.genres ?? [] as genre}
                    <option value={genre}>{genre}</option>
                  {/each}
                </select>
              </div>
            </label>

            <p class="helper">
              If you choose a different genre than the model assigned, PhotoCat automatically marks
              the original decision as wrong and keeps your override active.
            </p>

            <div class="action-row">
              <PrimaryButton on:click={() => approveModelDecision($activeItem.id)}>Keep Model Genre</PrimaryButton>
              <SecondaryButton on:click={applySelectedGenre}>
                {selectedGenre !== $activeItem.finalGenre ? "Apply Override" : "Clear Override"}
              </SecondaryButton>
            </div>

            <div class="utility-row">
              <SecondaryButton on:click={exportCorrected}>Export Corrected CSV</SecondaryButton>
              <SecondaryButton on:click={refreshOrganizePreview}>Refresh Preview</SecondaryButton>
            </div>
          </div>

          <div class="navigator">
            <div class="nav-head">
              <span>Navigation</span>
              <strong>{activeIndex >= 0 ? `${activeIndex + 1} of ${$visibleItems.length}` : "No selection"}</strong>
            </div>

            <div class="nav-row">
              <button class="nav-button" on:click={() => move(-1)} disabled={!previousItem}>
                <small>Previous</small>
                <strong>{previousItem?.filename || "Start of queue"}</strong>
              </button>

              <button class="nav-button" on:click={() => move(1)} disabled={!nextItem}>
                <small>Next</small>
                <strong>{nextItem?.filename || "End of queue"}</strong>
              </button>
            </div>
          </div>

          <div class="path-card">
            <span>Resolved Path</span>
            <strong>{$activeItem.imagePathDisplay}</strong>
          </div>
        </div>
      </div>

      <div class="evidence-grid">
        <EvidenceCard title="Caption" content={$activeItem.caption} />
        <EvidenceCard title="Detected Objects" content={$activeItem.objects} />
        <EvidenceCard title="OCR Text" content={$activeItem.ocrText} />
        <EvidenceCard title="Evidence Log" content={$activeItem.evidence} />
      </div>

      <div class="filmstrip-wrap">
        <Filmstrip items={$visibleItems} activeId={$activeItem.id} onSelect={selectItem} />
      </div>
    {:else}
      <div class="empty">Select an item from the dashboard to open the inspector.</div>
    {/if}
  </Panel>
</div>

<style>
  .workspace {
    display: grid;
    grid-template-columns: minmax(0, 1.4fr) 360px;
    gap: 1rem;
  }

  .stage {
    min-height: 28rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-lg);
    overflow: hidden;
    background: rgba(255, 255, 255, 0.03);
  }

  img,
  .missing {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .missing {
    display: grid;
    place-items: center;
    padding: 2rem;
    color: var(--pc-text-muted);
    text-align: center;
  }

  .rail {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    position: sticky;
    top: 6rem;
    align-self: start;
  }

  label,
  .control-card,
  .navigator,
  .path-card {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .control-card,
  .navigator,
  .path-card {
    padding: 1rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: rgba(255, 255, 255, 0.03);
  }

  span {
    color: var(--pc-text-muted);
  }

  .select-wrap {
    position: relative;
  }

  select {
    width: 100%;
    appearance: none;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    padding: 0.95rem 2.8rem 0.95rem 0.95rem;
    color: var(--pc-text);
    background:
      linear-gradient(180deg, rgba(34, 20, 42, 0.94), rgba(24, 13, 31, 0.94));
    font-weight: 600;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
  }

  .select-wrap::after {
    content: "▾";
    position: absolute;
    right: 0.95rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--pc-text-soft);
    pointer-events: none;
  }

  .helper {
    margin: 0;
    color: var(--pc-text-muted);
    line-height: 1.45;
  }

  .action-row,
  .utility-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
  }

  .nav-head {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: baseline;
  }

  .nav-head strong,
  .path-card strong {
    color: var(--pc-text);
    line-height: 1.35;
    word-break: break-word;
  }

  .nav-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.7rem;
  }

  .nav-button {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    align-items: flex-start;
    min-height: 4.6rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.9rem;
    background: rgba(93, 42, 122, 0.08);
    color: var(--pc-text);
    transition:
      border-color var(--pc-duration-fast) var(--pc-ease),
      background var(--pc-duration-fast) var(--pc-ease),
      transform var(--pc-duration-fast) var(--pc-ease);
    cursor: pointer;
    text-align: left;
  }

  .nav-button:hover:enabled {
    background: rgba(93, 42, 122, 0.18);
    border-color: rgba(191, 39, 66, 0.35);
    transform: translateY(-1px);
  }

  .nav-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .nav-button small {
    color: var(--pc-text-muted);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .nav-button strong {
    font-size: 0.92rem;
    line-height: 1.35;
  }

  .evidence-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }

  .filmstrip-wrap {
    margin-top: 1rem;
  }

  .empty {
    min-height: 20rem;
    display: grid;
    place-items: center;
    color: var(--pc-text-muted);
  }

  @media (max-width: 1120px) {
    .workspace {
      grid-template-columns: 1fr;
    }

    .rail {
      position: static;
    }
  }

  @media (max-width: 720px) {
    .evidence-grid {
      grid-template-columns: 1fr;
    }

    .nav-row {
      grid-template-columns: 1fr;
    }
  }
</style>
