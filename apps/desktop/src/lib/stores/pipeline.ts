import { derived, get, writable } from "svelte/store";
import type {
  PipelineEvent,
  PipelineLogEntry,
  PipelineRunRequest,
  PipelineStatus,
} from "../../../../shared/types/review.js";
import { desktopApi } from "../api";
import { pushToast } from "./app";
import { loadSession } from "./review";

const initialStatus: PipelineStatus = {
  state: "idle",
  progress: 0,
  total: 0,
  hasPythonOutput: false,
  pythonLogLines: 0,
  systemLogLines: 0,
  message: "Ready",
};

const MAX_LOG_ENTRIES = 500;

export const pipelineStatus = writable<PipelineStatus>(initialStatus);
export const pipelineLogEntries = writable<PipelineLogEntry[]>([]);
export const pipelineForm = writable<PipelineRunRequest>({
  inputDir: "",
  csvOutput: "",
  recursive: true,
  writeXmp: false,
  genreOnly: false,
  noCache: false,
  organize: false,
  dryRun: false,
  minConfidence: 0.55,
  workers: 1,
  extensions: ".jpg,.jpeg,.png,.webp,.tiff",
});

let eventSource: EventSource | null = null;
let lastCompletedRunId: string | undefined;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
const RECONNECT_DELAY_MS = 2_000;

export const pipelinePythonLogs = derived(
  [pipelineLogEntries, pipelineStatus],
  ([$entries, $status]) =>
    $entries.filter((entry) => entry.channel === "python" && (!entry.runId || entry.runId === $status.runId)),
);

export const pipelineSystemLogs = derived(
  [pipelineLogEntries, pipelineStatus],
  ([$entries, $status]) =>
    $entries.filter((entry) => entry.channel === "system" && (!entry.runId || entry.runId === $status.runId)),
);

export async function hydratePipeline() {
  try {
    const [status, logs] = await Promise.all([desktopApi.pipelineStatus(), desktopApi.pipelineLogs()]);
    pipelineStatus.set(status);
    pipelineLogEntries.set(logs.entries);
  } catch (error) {
    pushToast((error as Error).message, "warning");
  }
}

function appendLogEntry(entry: PipelineLogEntry) {
  pipelineLogEntries.update((entries) => [...entries.slice(-(MAX_LOG_ENTRIES - 1)), entry]);
}

function handlePipelineEvent(event: PipelineEvent) {
  if (event.type === "status") {
    pipelineStatus.set(event.status);
    if (event.status.state === "done" && event.status.runId && event.status.runId !== lastCompletedRunId) {
      lastCompletedRunId = event.status.runId;
      pushToast("Pipeline completed. Review CSV is ready to load.", "success");
    }
    return;
  }

  if (event.type === "log") {
    appendLogEntry(event.entry);
    return;
  }

  if (event.type === "warning") {
    pushToast(event.message, "warning");
    return;
  }

  if (event.type === "error") {
    pushToast(event.message, "danger");
    return;
  }

  if (event.type === "process-started") {
    pushToast(`Python started (pid ${event.pid}).`, "success");
    return;
  }

  if (event.type === "process-exit" && event.code !== 0) {
    pushToast(`Pipeline exited with code ${event.code}.`, "danger");
  }
}

export function connectPipelineEvents() {
  if (eventSource) return;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  eventSource = desktopApi.createPipelineEvents((event) => {
    handlePipelineEvent(event);
  });

  eventSource.onerror = () => {
    eventSource?.close();
    eventSource = null;
    // Auto-reconnect after a brief delay.
    if (!reconnectTimer) {
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectPipelineEvents();
      }, RECONNECT_DELAY_MS);
    }
  };
}

export async function runPipeline(payload: PipelineRunRequest) {
  try {
    const result = await desktopApi.pipelineRun(payload);
    pipelineStatus.update((status) => ({
      ...status,
      state: "starting",
      message: "Launching Python pipeline...",
      runId: result.runId,
      inputDir: result.inputDir,
      csvPath: result.csvPath,
      error: undefined,
      endedAt: undefined,
      startedAt: Date.now(),
      hasPythonOutput: false,
      progress: 0,
      total: 0,
      pythonLogLines: 0,
      systemLogLines: 0,
    }));
    pushToast(`Pipeline run accepted (${result.runId}).`, "success");
  } catch (error) {
    pipelineStatus.update((status) => ({
      ...status,
      state: "error",
      error: (error as Error).message,
      message: "Pipeline run rejected.",
      endedAt: Date.now(),
    }));
    pushToast((error as Error).message, "danger");
  }
}

export async function stopPipeline() {
  try {
    const result = await desktopApi.pipelineStop();
    pushToast(result.message, result.stopped ? "warning" : "neutral");
    await hydratePipeline();
  } catch (error) {
    pushToast((error as Error).message, "danger");
  }
}

export async function loadPipelineResultSession() {
  const status = get(pipelineStatus);
  if (!status.csvPath || !status.inputDir) {
    pushToast("No pipeline output is available to load.", "warning");
    return;
  }
  await loadSession(status.csvPath, status.inputDir);
}
