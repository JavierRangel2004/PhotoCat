<script lang="ts">
  import { onMount } from "svelte";
  import AppNav from "./lib/components/AppNav.svelte";
  import SessionModal from "./lib/components/SessionModal.svelte";
  import ToastRegion from "./lib/components/ToastRegion.svelte";
  import "./lib/theme/tokens.css";
  import DashboardView from "./features/dashboard/DashboardView.svelte";
  import InspectorView from "./features/inspector/InspectorView.svelte";
  import PipelineView from "./features/pipeline/PipelineView.svelte";
  import { currentView, pushToast, toasts, type ViewId } from "./lib/stores/app";
  import { connectPipelineEvents, hydratePipeline, pipelineStatus } from "./lib/stores/pipeline";
  import { activeItemId, backendHealth, checkHealth, hydrateSession, session } from "./lib/stores/review";

  let sessionModalOpen = false;

  onMount(() => {
    checkHealth();
    hydrateSession();
    hydratePipeline();
    connectPipelineEvents();
  });

  // Auto-open session modal if no session is loaded after hydration
  $: if ($backendHealth.ok && $session === null) {
    // Small delay to let the hydration attempt finish
    setTimeout(() => {
      if ($session === null) sessionModalOpen = true;
    }, 800);
  }

  function navigate(view: string) {
    currentView.set(view as ViewId);
  }
</script>

<div class="app-shell">
  <AppNav
    currentView={$currentView}
    pipelineState={$pipelineStatus.state}
    backendOk={$backendHealth.ok}
    onNavigate={navigate}
    onOpenSession={() => (sessionModalOpen = true)}
    onOpenPipeline={() => navigate("pipeline")}
  />

  <main class="workspace">
    {#if $currentView === "dashboard"}
      <DashboardView currentItemId={$activeItemId} />
    {:else if $currentView === "inspector"}
      <InspectorView />
    {:else}
      <PipelineView />
    {/if}
  </main>
</div>

<SessionModal
  bind:open={sessionModalOpen}
  onClose={() => (sessionModalOpen = false)}
/>

<ToastRegion toasts={$toasts} />

<style>
  .app-shell {
    display: flex;
    min-height: 100vh;
  }

  .workspace {
    flex: 1;
    margin-left: var(--pc-sidebar-width);
    padding: 1.5rem 2rem;
    max-width: calc(100vw - var(--pc-sidebar-width));
    min-height: 100vh;
  }

  @media (max-width: 768px) {
    .workspace {
      margin-left: 0;
      padding: 1rem;
      padding-bottom: 5rem; /* space for bottom nav */
      max-width: 100vw;
    }
  }
</style>
