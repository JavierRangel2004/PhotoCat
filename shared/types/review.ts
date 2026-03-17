export type ReviewStatus = "auto" | "review" | "title-inferred" | "skipped" | "";

export type UserLabel = "" | "correct" | "wrong";

export type ReviewItem = {
  id: string;
  rowKey: string;
  filename: string;
  sourcePath: string;
  relativeInputPath: string;
  imagePath: string;
  imagePathDisplay: string;
  finalGenre: string;
  effectiveGenre: string;
  userGenre: string;
  userLabel: UserLabel;
  userPortfolioCategory: string;
  reviewStatus: ReviewStatus;
  rating: string;
  isBlurry: string;
  exposure: string;
  caption: string;
  objects: string;
  ocrText: string;
  siglipScores: string[];
  evidence: string;
  modelFirstConf: number | null;
  modelSecondConf: number | null;
  portfolioCategory: string;
  portfolioGroup: string;
  exportInclude: boolean;
  destRelpath: string;
  portfolioNeedsReview: boolean;
  portfolioMappingSource: string;
};

export type ReviewSession = {
  csvPath: string;
  imageDir: string;
  summary: {
    total: number;
    auto: number;
    review: number;
    titleInferred: number;
    corrected: number;
    visible: number;
    genreCounts: Record<string, number>;
  };
  genres: string[];
  statuses: string[];
  items: ReviewItem[];
};

export type PipelineRunRequest = {
  inputDir: string;
  csvOutput?: string | null;
  recursive?: boolean;
  writeXmp?: boolean;
  genreOnly?: boolean;
  noCache?: boolean;
  organize?: boolean;
  dryRun?: boolean;
  minConfidence?: number;
  workers?: number;
  extensions?: string;
};

export type OrganizeMoveEntry = {
  source_path: string;
  dest_path: string;
  dest_relpath: string;
  portfolio_category: string;
  effective_genre: string;
  filename: string;
};

export type OrganizeConflict = {
  dest_path: string;
  sources: string[];
};

export type OrganizeInvalidDestination = {
  source_path: string;
  filename: string;
  dest_relpath: string;
  reason: string;
};

export type OrganizePreviewResult = {
  ok: boolean;
  moves: OrganizeMoveEntry[];
  missing: { source_path: string; filename: string }[];
  conflicts: OrganizeConflict[];
  counts_by_category: Record<string, number>;
  excluded_count: number;
  total: number;
  manifest_path_preview: string;
  errors: string[];
  invalid_destinations: OrganizeInvalidDestination[];
  contract_valid: boolean;
  allowed_photo_categories: string[];
  present_photo_categories: string[];
};

export type OrganizeCommitResult = {
  ok: boolean;
  moved: number;
  skipped: number;
  missing: number;
  conflicts: number;
  manifest_path: string;
  errors: string[];
};

export type RestoreResult = {
  ok: boolean;
  restored: number;
  missing: number;
  errors: string[];
};

export type PipelineState = "idle" | "starting" | "running" | "stopping" | "done" | "error";

export type PipelineLogChannel = "python" | "system";

export type PipelineLogLevel = "info" | "warning" | "error";

export type PipelineLogEntry = {
  id: string;
  timestamp: number;
  channel: PipelineLogChannel;
  level: PipelineLogLevel;
  line: string;
  runId?: string;
};

export type PipelineStatus = {
  state: PipelineState;
  progress: number;
  total: number;
  message?: string;
  error?: string;
  runId?: string;
  startedAt?: number;
  endedAt?: number;
  hasPythonOutput: boolean;
  pythonLogLines: number;
  systemLogLines: number;
  csvPath?: string;
  inputDir?: string;
};

export type PipelineEvent =
  | { type: "status"; status: PipelineStatus }
  | { type: "log"; entry: PipelineLogEntry }
  | { type: "warning"; code: string; message: string; runId?: string; timestamp: number }
  | { type: "error"; code: string; message: string; runId?: string; timestamp: number }
  | { type: "process-started"; runId: string; pid: number; command: string[]; timestamp: number }
  | { type: "process-exit"; runId: string; code: number | null; signal: string | null; timestamp: number };
