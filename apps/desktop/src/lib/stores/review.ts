import { derived, get, writable } from "svelte/store";
import type {
  OrganizeCommitResult,
  OrganizeMode,
  OrganizePreviewResult,
  RestoreResult,
  ReviewItem,
  ReviewSession,
  UserLabel,
} from "../../../../shared/types/review.js";
import { desktopApi } from "../api";
import { defaultOutputDirFromCsv, normalizeOrganizePath } from "../pathUtils";
import { deriveReviewItemOrganizeFields } from "../review/portfolioMapping";
import { pushToast } from "./app";

type OrganizeFlowState = {
  correctedCsvPath: string;
  outputDir: string;
  organizeMode: OrganizeMode;
  replaceAcknowledged: boolean;
  includeExcluded: boolean;
  preview: OrganizePreviewResult | null;
  previewState: "idle" | "loading" | "ready" | "error";
  previewError: string;
  exportState: "idle" | "loading" | "done" | "error";
  exportError: string;
  hasUnexportedChanges: boolean;
  isCommitting: boolean;
  isRestoring: boolean;
  commitResult: OrganizeCommitResult | null;
  restoreResult: RestoreResult | null;
  lastManifestPath: string;
};

const initialOrganizeFlow = (): OrganizeFlowState => ({
  correctedCsvPath: "",
  outputDir: "",
  organizeMode: "append_dedupe",
  replaceAcknowledged: false,
  includeExcluded: true,
  preview: null,
  previewState: "idle",
  previewError: "",
  exportState: "idle",
  exportError: "",
  hasUnexportedChanges: true,
  isCommitting: false,
  isRestoring: false,
  commitResult: null,
  restoreResult: null,
  lastManifestPath: "",
});

export const backendHealth = writable<{ ok: boolean; message: string; error: string }>({
  ok: false,
  message: "Checking backend bridge...",
  error: "",
});

export const session = writable<ReviewSession | null>(null);
export const sessionForm = writable({
  csvPath: "",
  imageDir: "",
});
export const reviewFilters = writable({
  search: "",
  genre: "All",
  status: "All",
  maxConfidence: 1,
});
export const activeItemId = writable<string | null>(null);
export const isSessionLoading = writable(false);
export const organizeFlow = writable<OrganizeFlowState>(initialOrganizeFlow());

function enrichItem(item: ReviewItem): ReviewItem {
  return {
    ...item,
    ...deriveReviewItemOrganizeFields(item),
  };
}

function enrichSessionPayload(payload: ReviewSession): ReviewSession {
  const items = payload.items.map(enrichItem);
  return {
    ...payload,
    items,
    summary: {
      ...payload.summary,
      corrected: recalculateCorrectedCount(items),
    },
  };
}

function resetOrganizeFlow(csvPath = "") {
  organizeFlow.set({
    ...initialOrganizeFlow(),
    outputDir: csvPath ? defaultOutputDirFromCsv(csvPath) : "",
  });
}

function markOrganizeFlowDirty() {
  organizeFlow.update((flow) => ({
    ...flow,
    hasUnexportedChanges: true,
    preview: null,
    previewState: "idle",
    previewError: "",
    commitResult: null,
    restoreResult: null,
    replaceAcknowledged: false,
  }));
}

export const visibleItems = derived([session, reviewFilters], ([$session, $filters]) => {
  const items = $session?.items ?? [];
  return items.filter((item) => {
    const matchesSearch =
      !$filters.search ||
      item.filename.toLowerCase().includes($filters.search.toLowerCase()) ||
      item.caption.toLowerCase().includes($filters.search.toLowerCase());
    const matchesGenre =
      $filters.genre === "All" || (item.effectiveGenre || item.finalGenre) === $filters.genre;
    const matchesStatus = $filters.status === "All" || item.reviewStatus === $filters.status;
    const matchesConfidence = (item.modelFirstConf ?? 1) <= $filters.maxConfidence;
    return matchesSearch && matchesGenre && matchesStatus && matchesConfidence;
  });
});
export const reviewOnlyItems = derived(session, ($session) =>
  ($session?.items ?? []).filter((item) => item.reviewStatus === "review"),
);
export const activeItem = derived([session, activeItemId], ([$session, $activeItemId]) => {
  if (!$session || !$activeItemId) return null;
  return $session.items.find((item) => item.id === $activeItemId) ?? null;
});
export const lowConfidenceItems = derived(session, ($session) =>
  ($session?.items ?? []).filter((item) => (item.modelFirstConf ?? 1) < 0.7),
);
export const correctedItems = derived(session, ($session) =>
  ($session?.items ?? []).filter((item) => item.userGenre || item.userLabel || item.userPortfolioCategory),
);
export const organizeCanPreview = derived([session, organizeFlow], ([$session, $flow]) =>
  Boolean(
    $session &&
    $flow.correctedCsvPath &&
    $flow.outputDir.trim() &&
    !$flow.hasUnexportedChanges &&
    $flow.previewState !== "loading",
  ),
);
export const organizeCanCommit = derived([organizeFlow, organizeCanPreview], ([$flow, $canPreview]) =>
  Boolean(
    $canPreview &&
    $flow.preview &&
    $flow.preview.contract_valid &&
    $flow.preview.errors.length === 0 &&
    !$flow.isCommitting &&
    ($flow.organizeMode === "append_dedupe" ||
      ($flow.organizeMode === "replace" && $flow.replaceAcknowledged)),
  ),
);

function recalculateCorrectedCount(items: ReviewItem[]) {
  return items.filter((item) => item.userGenre || item.userLabel || item.userPortfolioCategory).length;
}

function patchItemInSession(
  itemId: string,
  updater: (item: ReviewItem) => ReviewItem,
  options: { markDirty?: boolean } = {},
) {
  session.update(($session) => {
    if (!$session) return $session;
    const items = $session.items.map((item) => (item.id === itemId ? enrichItem(updater(item)) : item));
    return {
      ...$session,
      items,
      summary: {
        ...$session.summary,
        corrected: recalculateCorrectedCount(items),
      },
    };
  });

  if (options.markDirty !== false) {
    markOrganizeFlowDirty();
  }
}

function applySessionResult(result: ReviewSession | null) {
  if (!result) {
    session.set(null);
    activeItemId.set(null);
    resetOrganizeFlow();
    return;
  }

  const enriched = enrichSessionPayload(result);
  session.set(enriched);
  activeItemId.set(enriched.items[0]?.id ?? null);
  resetOrganizeFlow(enriched.csvPath);
}

export async function checkHealth() {
  try {
    const result = await desktopApi.health();
    backendHealth.set({
      ok: result.ok,
      message: `Backend online. Boundary: ${result.pythonBoundary}`,
      error: "",
    });
  } catch (error) {
    backendHealth.set({
      ok: false,
      message: "Backend unavailable.",
      error: (error as Error).message,
    });
  }
}

export async function hydrateSession() {
  try {
    const result = await desktopApi.session();
    applySessionResult(result);
  } catch (error) {
    pushToast((error as Error).message, "warning");
  }
}

export async function loadSession(csvPath: string, imageDir: string) {
  isSessionLoading.set(true);
  try {
    const result = await desktopApi.loadSession(csvPath, imageDir);
    applySessionResult(result);
    sessionForm.set({ csvPath, imageDir });
    pushToast(`Loaded ${result.summary.total} items.`, "success");
  } catch (error) {
    pushToast((error as Error).message, "danger");
  } finally {
    isSessionLoading.set(false);
  }
}

export function selectItem(itemId: string) {
  activeItemId.set(itemId);
}

export function setOrganizeOutputDir(outputDir: string) {
  organizeFlow.update((flow) => ({
    ...flow,
    outputDir: normalizeOrganizePath(outputDir),
    preview: null,
    previewState: "idle",
    previewError: "",
    commitResult: null,
    restoreResult: null,
    replaceAcknowledged: false,
  }));
}

export function setOrganizeMode(mode: OrganizeMode) {
  organizeFlow.update((flow) => ({
    ...flow,
    organizeMode: mode,
    replaceAcknowledged: false,
    preview: null,
    previewState: "idle",
    previewError: "",
    commitResult: null,
  }));
}

export function setReplaceModeAcknowledged(acknowledged: boolean) {
  organizeFlow.update((flow) => ({
    ...flow,
    replaceAcknowledged: acknowledged,
  }));
}

export function setIncludeExcluded(includeExcluded: boolean) {
  organizeFlow.update((flow) => ({
    ...flow,
    includeExcluded,
    preview: null,
    previewState: "idle",
    previewError: "",
    commitResult: null,
    replaceAcknowledged: false,
  }));
}

export async function setGenre(itemId: string, genre: string) {
  const current = get(session)?.items.find((item) => item.id === itemId);
  if (!current) return;

  const normalizedGenre = genre === current.finalGenre ? "" : genre;
  const nextLabel: UserLabel = normalizedGenre ? "wrong" : current.userLabel === "wrong" ? "" : current.userLabel;

  patchItemInSession(itemId, (item) => ({
    ...item,
    userGenre: normalizedGenre,
    userLabel: nextLabel,
    effectiveGenre: normalizedGenre || item.finalGenre,
  }));

  try {
    await desktopApi.setGenre(itemId, normalizedGenre);
    await desktopApi.setLabel(itemId, nextLabel);
    pushToast(
      normalizedGenre ? "Override applied. Item marked as wrong for the original model decision." : "Override cleared. Using the model genre again.",
      "success",
    );
  } catch (error) {
    patchItemInSession(itemId, () => current, { markDirty: false });
    pushToast((error as Error).message, "danger");
  }
}

export async function setLabel(itemId: string, label: UserLabel) {
  const current = get(session)?.items.find((item) => item.id === itemId);
  if (!current) return;

  patchItemInSession(itemId, (item) => ({ ...item, userLabel: label }));

  try {
    await desktopApi.setLabel(itemId, label);
    pushToast(`Marked ${label || "cleared"} for review item.`, "success");
  } catch (error) {
    patchItemInSession(itemId, () => current, { markDirty: false });
    pushToast((error as Error).message, "danger");
  }
}

export async function setPortfolioCategory(itemId: string, portfolioCategory: string) {
  const current = get(session)?.items.find((item) => item.id === itemId);
  if (!current) return;

  patchItemInSession(itemId, (item) => ({
    ...item,
    userPortfolioCategory: portfolioCategory,
  }));

  try {
    await desktopApi.setPortfolioCategory(itemId, portfolioCategory);
    pushToast(portfolioCategory ? `Portfolio category set to ${portfolioCategory}.` : "Portfolio category override cleared.", "success");
  } catch (error) {
    patchItemInSession(itemId, () => current, { markDirty: false });
    pushToast((error as Error).message, "danger");
  }
}

export async function approveModelDecision(itemId: string) {
  const current = get(session)?.items.find((item) => item.id === itemId);
  if (!current) return;

  patchItemInSession(itemId, (item) => ({
    ...item,
    userGenre: "",
    userLabel: "correct",
    effectiveGenre: item.finalGenre,
  }));

  try {
    await desktopApi.setGenre(itemId, "");
    await desktopApi.setLabel(itemId, "correct");
    pushToast("Model genre approved for this item.", "success");
  } catch (error) {
    patchItemInSession(itemId, () => current, { markDirty: false });
    pushToast((error as Error).message, "danger");
  }
}

export async function exportCorrected() {
  const currentSession = get(session);
  if (!currentSession) {
    pushToast("Load a session before exporting a corrected CSV.", "warning");
    return;
  }

  organizeFlow.update((flow) => ({
    ...flow,
    exportState: "loading",
    exportError: "",
  }));

  try {
    const result = await desktopApi.exportCorrected();
    organizeFlow.update((flow) => ({
      ...flow,
      correctedCsvPath: result.outputPath,
      exportState: "done",
      exportError: "",
      hasUnexportedChanges: false,
      preview: null,
      previewState: "idle",
      previewError: "",
      commitResult: null,
      restoreResult: null,
    }));
    pushToast(result.message, "success");
  } catch (error) {
    organizeFlow.update((flow) => ({
      ...flow,
      exportState: "error",
      exportError: (error as Error).message,
    }));
    pushToast((error as Error).message, "danger");
  }
}

export async function requestOrganizePreview() {
  const flow = get(organizeFlow);
  if (!flow.correctedCsvPath) {
    pushToast("Export the corrected CSV before requesting organize preview.", "warning");
    return;
  }
  if (!flow.outputDir.trim()) {
    pushToast("Set an organize output directory before requesting preview.", "warning");
    return;
  }
  if (flow.hasUnexportedChanges) {
    pushToast("Export the corrected CSV again so preview uses your latest review changes.", "warning");
    return;
  }

  organizeFlow.update((current) => ({
    ...current,
    previewState: "loading",
    previewError: "",
    commitResult: null,
  }));

  try {
    const result = await desktopApi.organizeFromCsvPreview(flow.correctedCsvPath, flow.outputDir, {
      mode: flow.organizeMode,
    });
    organizeFlow.update((current) => ({
      ...current,
      preview: result,
      previewState: "ready",
      previewError: "",
      lastManifestPath: current.lastManifestPath || result.manifest_path_preview,
    }));
    pushToast(
      result.errors.length ? "Preview completed with contract warnings." : "Organize preview updated.",
      result.errors.length ? "warning" : "success",
    );
  } catch (error) {
    organizeFlow.update((current) => ({
      ...current,
      previewState: "error",
      previewError: (error as Error).message,
    }));
    pushToast((error as Error).message, "danger");
  }
}

export async function commitOrganize() {
  const flow = get(organizeFlow);
  if (!flow.correctedCsvPath || !flow.outputDir.trim()) {
    pushToast("Export the corrected CSV and choose an output directory before commit.", "warning");
    return;
  }
  if (flow.hasUnexportedChanges) {
    pushToast("Re-export the corrected CSV before commit so organize uses the latest review state.", "warning");
    return;
  }
  if (!flow.preview || !flow.preview.contract_valid || flow.preview.errors.length) {
    pushToast("Run a successful organize preview before commit.", "warning");
    return;
  }

  organizeFlow.update((current) => ({
    ...current,
    isCommitting: true,
    commitResult: null,
  }));

  try {
    const result = await desktopApi.organizeFromCsvCommit(flow.correctedCsvPath, flow.outputDir, {
      includeExcluded: flow.includeExcluded,
      mode: flow.organizeMode,
    });
    organizeFlow.update((current) => ({
      ...current,
      isCommitting: false,
      commitResult: result,
      lastManifestPath: result.manifest_path || current.lastManifestPath,
    }));
    pushToast(
      result.errors.length ? "Organize commit finished with errors." : `Organize commit completed: ${result.moved} moved.`,
      result.errors.length ? "warning" : "success",
    );
  } catch (error) {
    organizeFlow.update((current) => ({
      ...current,
      isCommitting: false,
    }));
    pushToast((error as Error).message, "danger");
  }
}

export async function restoreLastOrganize() {
  const manifestPath = get(organizeFlow).lastManifestPath || get(organizeFlow).commitResult?.manifest_path;
  if (!manifestPath) {
    pushToast("No organize manifest is available to restore.", "warning");
    return;
  }

  organizeFlow.update((current) => ({
    ...current,
    isRestoring: true,
    restoreResult: null,
  }));

  try {
    const result = await desktopApi.restoreFromManifest(manifestPath);
    organizeFlow.update((current) => ({
      ...current,
      isRestoring: false,
      restoreResult: result,
    }));
    pushToast(
      result.errors.length ? "Restore finished with errors." : `Restore completed: ${result.restored} restored.`,
      result.errors.length ? "warning" : "success",
    );
  } catch (error) {
    organizeFlow.update((current) => ({
      ...current,
      isRestoring: false,
    }));
    pushToast((error as Error).message, "danger");
  }
}
