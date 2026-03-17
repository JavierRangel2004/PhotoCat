<script lang="ts">
  import { onMount } from "svelte";
  import AppNav from "./lib/components/AppNav.svelte";
  import Panel from "./lib/components/Panel.svelte";
  import PipelineProgressCard from "./lib/components/PipelineProgressCard.svelte";
  import ToastRegion from "./lib/components/ToastRegion.svelte";
  import "./lib/theme/tokens.css";
  import DashboardView from "./features/dashboard/DashboardView.svelte";
  import InspectorView from "./features/inspector/InspectorView.svelte";
  import OrganizePanel from "./features/organize/OrganizePanel.svelte";
  import PipelineView from "./features/pipeline/PipelineView.svelte";
  import SessionLoader from "./features/session/SessionLoader.svelte";
  import { currentView, pushToast, toasts, type ViewId } from "./lib/stores/app";
  import { connectPipelineEvents, hydratePipeline, pipelineStatus } from "./lib/stores/pipeline";
  import { activeItemId, backendHealth, checkHealth, hydrateSession, session } from "./lib/stores/review";

  onMount(() => {
    checkHealth();
    hydrateSession();
    hydratePipeline();
    connectPipelineEvents();
    pushToast("Frontend foundation checkpoint loaded.", "neutral", 2400);
  });

  function navigate(view: string) {
    currentView.set(view as ViewId);
  }
</script>

<div class="shell">
  <AppNav
    currentView={$currentView}
    pipelineState={$pipelineStatus.state}
    onNavigate={navigate}
    onOpenSession={() => navigate("dashboard")}
    onOpenPipeline={() => navigate("pipeline")}
  />

  <section class="hero">
    <div class="hero-copy">
      <p class="eyebrow">Checkpoint</p>
      <h1>Review workstation foundation, not just a scaffold.</h1>
      <p class="lede">
        This checkpoint establishes the reusable shell, dark visual system, shared stores, backend
        API surface, and first-pass review workspace for the Node frontend while keeping all
        processing in Python.
      </p>
    </div>

    <Panel title="Bridge Status">
      <p class="status">{$backendHealth.message}</p>
      {#if $backendHealth.error}
        <p class="error">{$backendHealth.error}</p>
      {/if}
      {#if $session}
        <p class="detail">Loaded session: {$session.csvPath}</p>
      {/if}
      <div class="bridge-progress">
        <PipelineProgressCard
          state={$pipelineStatus.state}
          progress={$pipelineStatus.progress}
          total={$pipelineStatus.total}
          pythonLogLines={$pipelineStatus.pythonLogLines}
          systemLogLines={$pipelineStatus.systemLogLines}
          message={$pipelineStatus.message}
          error={$pipelineStatus.error}
        />
      </div>
    </Panel>
  </section>

  <SessionLoader />

  <section class="view-grid">
    <div class="primary-column">
      {#if $currentView === "dashboard"}
        <DashboardView currentItemId={$activeItemId} />
        <InspectorView />
      {:else if $currentView === "inspector"}
        <InspectorView />
        <DashboardView currentItemId={$activeItemId} />
      {:else}
        <PipelineView />
        <DashboardView currentItemId={$activeItemId} />
      {/if}
    </div>

    <div class="secondary-column">
      {#if $currentView !== "pipeline"}
        <PipelineView />
      {/if}
      <OrganizePanel />
    </div>
  </section>
</div>

<ToastRegion toasts={$toasts} />

<style>
  .shell {
    max-width: 1520px;
    margin: 0 auto;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .hero {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    align-items: stretch;
  }

  .hero-copy {
    padding: 1.6rem 1.8rem;
    border-radius: var(--pc-radius-xl);
    background:
      radial-gradient(circle at top right, rgba(191, 39, 66, 0.26), transparent 26%),
      linear-gradient(135deg, rgba(24, 12, 30, 0.95), rgba(11, 7, 16, 0.94));
    border: 1px solid var(--pc-border);
    box-shadow: var(--pc-shadow);
  }

  .eyebrow,
  .status,
  .detail,
  .error,
  .lede {
    margin: 0;
  }

  .eyebrow {
    color: var(--pc-primary);
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-size: 0.78rem;
    font-weight: 800;
  }

  h1 {
    margin: 0.5rem 0 0.9rem;
    font-family: var(--pc-font-display);
    font-size: clamp(2.6rem, 5vw, 4.9rem);
    line-height: 0.92;
    letter-spacing: -0.04em;
  }

  .lede {
    max-width: 58rem;
    color: var(--pc-text-soft);
    line-height: 1.65;
  }

  .status {
    color: var(--pc-text-soft);
  }

  .detail {
    margin-top: 0.9rem;
    color: var(--pc-text-muted);
    word-break: break-word;
  }

  .error {
    margin-top: 0.7rem;
    color: #ffc4d0;
  }

  .bridge-progress {
    margin-top: 1rem;
  }

  .view-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .primary-column,
  .secondary-column {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  @media (min-width: 1180px) {
    .hero {
      grid-template-columns: minmax(0, 1.45fr) 360px;
    }

    .view-grid {
      grid-template-columns: minmax(0, 1.5fr) 400px;
    }
  }
</style>
