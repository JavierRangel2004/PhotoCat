export type ReviewStatus = "auto" | "review" | "title-inferred" | "skipped" | "";

export type UserLabel = "" | "correct" | "wrong";

export type ReviewItem = {
  id: string;
  filename: string;
  imagePath: string;
  imagePathDisplay: string;
  finalGenre: string;
  effectiveGenre: string;
  userGenre: string;
  userLabel: UserLabel;
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

export type PipelineStatus = {
  state: "idle" | "running" | "stopping" | "done" | "error";
  progress: number;
  total: number;
  error?: string;
  bufferedLogLines: number;
};
