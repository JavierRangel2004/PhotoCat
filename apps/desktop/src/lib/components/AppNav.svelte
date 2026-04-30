<script lang="ts">
  import StatusPill from "./StatusPill.svelte";

  export let currentView = "dashboard";
  export let pipelineState = "idle";
  export let backendOk = false;
  export let onNavigate: (viewId: string) => void = () => {};
  export let onOpenSession: () => void = () => {};
  export let onOpenPipeline: () => void = () => {};

  const views = [
    { id: "dashboard", label: "Review", icon: "grid" },
    { id: "inspector", label: "Inspector", icon: "eye" },
    { id: "pipeline",  label: "Pipeline",  icon: "play" },
  ];
</script>

<nav class="sidebar" aria-label="Main navigation">
  <div class="sidebar-top">
    <div class="brand">
      <div class="mark">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">PhotoCat</span>
        <span class="brand-health" class:online={backendOk}></span>
      </div>
    </div>

    <div class="nav-tabs" role="tablist">
      {#each views as view}
        <button
          class="nav-tab"
          class:active={currentView === view.id}
          role="tab"
          aria-selected={currentView === view.id}
          on:click={() => onNavigate(view.id)}
        >
          <span class="nav-icon">
            {#if view.icon === "grid"}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
                <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
              </svg>
            {:else if view.icon === "eye"}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            {:else}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            {/if}
          </span>
          <span class="nav-label">{view.label}</span>
        </button>
      {/each}
    </div>

    <div class="status-section">
      <StatusPill value={pipelineState} />
    </div>
  </div>

  <div class="sidebar-bottom">
    <button class="action-btn" on:click={onOpenSession} aria-label="Load session">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
      <span>Load Session</span>
    </button>
    <button class="action-btn accent" on:click={onOpenPipeline} aria-label="Run pipeline">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polygon points="5 3 19 12 5 21 5 3" />
      </svg>
      <span>Run Pipeline</span>
    </button>
  </div>
</nav>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: var(--pc-sidebar-width);
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: var(--pc-bg-elevated);
    border-right: 1px solid var(--pc-border);
    z-index: 20;
    padding: 1rem 0.75rem;
    overflow-y: auto;
  }

  .sidebar-top {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.25rem 0.25rem;
  }

  .mark {
    width: 36px;
    height: 36px;
    display: grid;
    place-items: center;
    border-radius: var(--pc-radius-md);
    background: linear-gradient(135deg, var(--pc-primary), var(--pc-secondary));
    color: white;
    flex-shrink: 0;
  }

  .brand-text {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .brand-name {
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: -0.01em;
  }

  .brand-health {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--pc-danger);
    transition: background var(--pc-duration-normal) var(--pc-ease);
  }

  .brand-health.online {
    background: var(--pc-success);
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
  }

  .nav-tabs {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .nav-tab {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    padding: 0.55rem 0.65rem;
    border: none;
    border-radius: var(--pc-radius-md);
    background: transparent;
    color: var(--pc-text-muted);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: color var(--pc-duration-fast) var(--pc-ease),
                background var(--pc-duration-fast) var(--pc-ease);
    text-align: left;
  }

  .nav-tab:hover {
    color: var(--pc-text);
    background: var(--pc-surface-soft);
  }

  .nav-tab.active {
    color: var(--pc-primary);
    background: var(--pc-primary-glow);
  }

  .nav-icon {
    display: grid;
    place-items: center;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }

  .status-section {
    padding: 0 0.25rem;
  }

  .sidebar-bottom {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding-top: 1rem;
    border-top: 1px solid var(--pc-border);
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    width: 100%;
    padding: 0.55rem 0.65rem;
    border: none;
    border-radius: var(--pc-radius-md);
    background: transparent;
    color: var(--pc-text-muted);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: color var(--pc-duration-fast) var(--pc-ease),
                background var(--pc-duration-fast) var(--pc-ease);
    text-align: left;
  }

  .action-btn:hover {
    color: var(--pc-text);
    background: var(--pc-surface-soft);
  }

  .action-btn.accent {
    color: var(--pc-primary);
  }

  .action-btn.accent:hover {
    background: var(--pc-primary-glow);
  }

  .nav-tab:focus-visible,
  .action-btn:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }

  @media (max-width: 768px) {
    .sidebar {
      width: 100%;
      height: auto;
      position: fixed;
      top: auto;
      bottom: 0;
      left: 0;
      right: 0;
      flex-direction: row;
      padding: 0.5rem;
      border-right: none;
      border-top: 1px solid var(--pc-border);
    }

    .sidebar-top {
      flex-direction: row;
      align-items: center;
      gap: 0.5rem;
      flex: 1;
    }

    .brand,
    .status-section,
    .sidebar-bottom,
    .nav-label {
      display: none;
    }

    .nav-tabs {
      flex-direction: row;
      gap: 0.25rem;
      flex: 1;
      justify-content: center;
    }

    .nav-tab {
      justify-content: center;
      padding: 0.6rem 1rem;
    }
  }
</style>
