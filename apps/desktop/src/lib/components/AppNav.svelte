<script lang="ts">
  import PrimaryButton from "./PrimaryButton.svelte";
  import SecondaryButton from "./SecondaryButton.svelte";
  import StatusPill from "./StatusPill.svelte";

  export let currentView = "dashboard";
  export let pipelineState = "idle";
  export let onNavigate: (viewId: string) => void = () => {};
  export let onOpenSession: () => void = () => {};
  export let onOpenPipeline: () => void = () => {};

  const views = [
    { id: "dashboard", label: "Review" },
    { id: "inspector", label: "Inspector" },
    { id: "pipeline", label: "Pipeline" },
  ];
</script>

<nav class="nav">
  <div class="brand">
    <div class="mark">P</div>
    <div>
      <p>PhotoCat</p>
      <small>Node frontend, Python engine</small>
    </div>
  </div>

  <div class="tabs">
    {#each views as view}
      <button class:active={currentView === view.id} on:click={() => onNavigate(view.id)}>
        {view.label}
      </button>
    {/each}
  </div>

  <div class="actions">
    <StatusPill value={pipelineState} />
    <SecondaryButton on:click={onOpenSession}>Load Session</SecondaryButton>
    <PrimaryButton on:click={onOpenPipeline}>Run Pipeline</PrimaryButton>
  </div>
</nav>

<style>
  .nav {
    position: sticky;
    top: 0;
    z-index: 10;
    display: grid;
    grid-template-columns: 1fr;
    justify-items: start;
    gap: var(--pc-space-5);
    align-items: center;
    padding: 1rem 1.2rem;
    border: 1px solid var(--pc-border);
    border-radius: calc(var(--pc-radius-lg) + 4px);
    background: rgba(12, 7, 17, 0.86);
    backdrop-filter: blur(18px);
    box-shadow: var(--pc-shadow-soft);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: var(--pc-space-3);
  }

  .mark {
    width: 2.6rem;
    height: 2.6rem;
    display: grid;
    place-items: center;
    border-radius: 0.95rem;
    background: linear-gradient(135deg, var(--pc-primary), var(--pc-secondary));
    color: white;
    font-family: var(--pc-font-display);
    font-weight: 800;
    box-shadow: var(--pc-glow);
  }

  p,
  small {
    margin: 0;
  }

  p {
    font-family: var(--pc-font-display);
    font-weight: 700;
  }

  small {
    color: var(--pc-text-muted);
  }

  .tabs {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 0.55rem;
  }

  .tabs button {
    border: 1px solid transparent;
    border-radius: 999px;
    padding: 0.7rem 0.95rem;
    background: transparent;
    color: var(--pc-text-muted);
    font-weight: 700;
    cursor: pointer;
  }

  .tabs button.active {
    border-color: var(--pc-border);
    color: var(--pc-text);
    background: rgba(93, 42, 122, 0.15);
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.75rem;
  }

  .tabs button:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }

  @media (min-width: 1120px) {
    .nav {
      grid-template-columns: auto 1fr auto;
      justify-items: initial;
    }

    .tabs {
      flex-wrap: nowrap;
      justify-content: center;
    }

    .actions {
      flex-wrap: nowrap;
    }
  }
</style>
