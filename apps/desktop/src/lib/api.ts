import type {
  OrganizeCommitResult,
  OrganizePreviewResult,
  PipelineEvent,
  PipelineLogEntry,
  PipelineRunRequest,
  PipelineStatus,
  RestoreResult,
  ReviewItem,
  ReviewSession,
  UserLabel,
} from "../../../../shared/types/review.js";

const API_BASE = import.meta.env.VITE_PHOTOCAT_API_BASE_URL ?? "http://127.0.0.1:8797";

type MaybeSessionResponse = ReviewSession | { session: ReviewSession | null };

export type HealthResponse = {
  ok: boolean;
  pythonBoundary: string;
  service: string;
};

export type ExportResponse = {
  ok: boolean;
  message: string;
  csvPath: string;
  outputPath: string;
};

export type PipelineLogsResponse = {
  entries: PipelineLogEntry[];
};

export type PipelineRunResponse = {
  started: true;
  runId: string;
  acceptedCommand: string[];
  state: PipelineStatus["state"];
  inputDir: string;
  csvPath: string;
};

type ApiErrorPayload = {
  error?: string;
  message?: string;
};

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const hasBody = init?.body !== undefined;
  const response = await fetch(`${API_BASE}${url}`, {
    headers: hasBody
      ? {
          "Content-Type": "application/json",
          ...(init?.headers ?? {}),
        }
      : init?.headers,
    ...init,
  });

  if (!response.ok) {
    let payload: ApiErrorPayload | null = null;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = null;
    }
    const message = payload?.error ?? payload?.message ?? `Request failed: ${response.status}`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

function normalizeSession(response: MaybeSessionResponse): ReviewSession | null {
  if ("session" in response) {
    return response.session;
  }
  return response;
}

export function createPipelineEvents(onEvent: (event: PipelineEvent) => void) {
  const source = new EventSource(`${API_BASE}/api/pipeline/events`);
  const eventNames = ["status", "log", "warning", "error", "process-started", "process-exit"] as const;
  for (const eventName of eventNames) {
    source.addEventListener(eventName, (event) => {
      const payload = JSON.parse((event as MessageEvent<string>).data) as PipelineEvent;
      onEvent(payload);
    });
  }
  return source;
}

export const desktopApi = {
  health: () => request<HealthResponse>("/api/health"),
  pipelineStatus: () => request<PipelineStatus>("/api/pipeline/status"),
  pipelineLogs: () => request<PipelineLogsResponse>("/api/pipeline/logs"),
  pipelineRun: (payload: PipelineRunRequest) =>
    request<PipelineRunResponse>("/api/pipeline/run", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  pipelineStop: () =>
    request<{ stopped: boolean; message: string }>("/api/pipeline/stop", {
      method: "POST",
    }),
  createPipelineEvents,
  loadSession: (csvPath: string, imageDir: string) =>
    request<ReviewSession>("/api/review/load", {
      method: "POST",
      body: JSON.stringify({ csvPath, imageDir }),
    }),
  session: async () => normalizeSession(await request<MaybeSessionResponse>("/api/review/session")),
  setGenre: (itemId: string, genre: string) =>
    request<ReviewItem>("/api/review/item/genre", {
      method: "POST",
      body: JSON.stringify({ itemId, genre }),
    }),
  setLabel: (itemId: string, label: UserLabel) =>
    request<ReviewItem>("/api/review/item/label", {
      method: "POST",
      body: JSON.stringify({ itemId, label }),
    }),
  setPortfolioCategory: (itemId: string, portfolioCategory: string) =>
    request<ReviewItem>("/api/review/item/portfolio-category", {
      method: "POST",
      body: JSON.stringify({ itemId, portfolioCategory }),
    }),
  exportCorrected: () =>
    request<ExportResponse>("/api/review/export", {
      method: "POST",
    }),
  organizeFromCsvPreview: (csvPath: string, outputDir: string) =>
    request<OrganizePreviewResult>("/api/review/organize-from-csv/preview", {
      method: "POST",
      body: JSON.stringify({ csvPath, outputDir }),
    }),
  organizeFromCsvCommit: (csvPath: string, outputDir: string, options?: { dryRun?: boolean; includeExcluded?: boolean }) =>
    request<OrganizeCommitResult>("/api/review/organize-from-csv/commit", {
      method: "POST",
      body: JSON.stringify({ csvPath, outputDir, ...options }),
    }),
  restoreFromManifest: (manifestPath: string, dryRun = false) =>
    request<RestoreResult>("/api/review/restore-from-manifest", {
      method: "POST",
      body: JSON.stringify({ manifestPath, dryRun }),
    }),
  assetUrl: (imagePath: string) => `${API_BASE}/api/assets/image?path=${encodeURIComponent(imagePath)}`,
  thumbnailUrl: (imagePath: string, width: number) =>
    `${API_BASE}/api/assets/image?path=${encodeURIComponent(imagePath)}&w=${width}`,
};
