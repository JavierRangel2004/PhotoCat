import { execFile } from "node:child_process";
import { constants, promises as fs } from "node:fs";
import path from "node:path";
import { EventEmitter } from "node:events";
import type {
  PipelineEvent,
  PipelineRunRequest,
  PipelineState,
  PipelineStatus,
} from "../../../../shared/types/review.js";
import { backendConfig } from "../config.js";
import { LogBuffer } from "./logBuffer.js";
import { spawnPipeline, type SpawnedPipeline } from "./pythonBridge.js";

const PROGRESS_RE = /\[(\d+)\/(\d+)\]/;
const STARTUP_OUTPUT_TIMEOUT_MS = 8_000;

type PreflightResult = {
  inputDir: string;
  csvPath: string;
};

type PipelineStartResult = {
  started: true;
  runId: string;
  acceptedCommand: string[];
  state: PipelineState;
  inputDir: string;
  csvPath: string;
};

type PipelineManagerErrorCode = "PIPELINE_ALREADY_RUNNING" | "PIPELINE_PREFLIGHT_FAILED" | "PIPELINE_START_FAILED";

export class PipelineManagerError extends Error {
  constructor(
    message: string,
    readonly code: PipelineManagerErrorCode,
    readonly statusCode = 400,
  ) {
    super(message);
  }
}

function runExecFile(command: string, args: string[]) {
  return new Promise<void>((resolve, reject) => {
    execFile(
      command,
      args,
      {
        cwd: backendConfig.repoRoot,
        timeout: 5_000,
      },
      (error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      },
    );
  });
}

export class PipelineManager {
  private process: SpawnedPipeline["process"] | null = null;
  private status: PipelineStatus = {
    state: "idle",
    progress: 0,
    total: 0,
    hasPythonOutput: false,
    pythonLogLines: 0,
    systemLogLines: 0,
    message: "Ready",
  };
  private runCounter = 1;
  private startupTimeout: NodeJS.Timeout | null = null;
  private stdoutRemainder = "";
  private stderrRemainder = "";
  private activeCommand: string[] = [];

  readonly events = new EventEmitter();

  constructor(private readonly debugLogBuffer: LogBuffer) {}

  getStatus() {
    return { ...this.status };
  }

  async start(request: PipelineRunRequest): Promise<PipelineStartResult> {
    if (this.process) {
      throw new PipelineManagerError("Pipeline already running.", "PIPELINE_ALREADY_RUNNING", 409);
    }

    const preflight = await this.preflight(request);
    const runId = this.nextRunId();
    const args: string[] = ["--input-dir", preflight.inputDir, "--csv", preflight.csvPath];
    if (request.recursive) args.push("--recursive");
    if (request.writeXmp) args.push("--write-xmp");
    if (request.genreOnly) args.push("--genre-only");
    if (request.noCache) args.push("--no-cache");
    if (request.organize) args.push("--organize");
    if (request.dryRun) args.push("--dry-run");
    if (request.minConfidence !== undefined) args.push("--min-confidence", String(request.minConfidence));
    if (request.workers !== undefined) args.push("--workers", String(request.workers));
    if (request.extensions) args.push("--extensions", request.extensions);

    let spawned: SpawnedPipeline;
    try {
      spawned = spawnPipeline(args);
    } catch (error) {
      const message = `Failed to start Python process: ${(error as Error).message}`;
      throw new PipelineManagerError(message, "PIPELINE_START_FAILED", 500);
    }

    this.process = spawned.process;
    this.activeCommand = spawned.command;
    this.stdoutRemainder = "";
    this.stderrRemainder = "";
    this.status = {
      state: "starting",
      progress: 0,
      total: 0,
      message: "Launching Python pipeline...",
      runId,
      startedAt: Date.now(),
      hasPythonOutput: false,
      pythonLogLines: 0,
      systemLogLines: 0,
      csvPath: preflight.csvPath,
      inputDir: preflight.inputDir,
    };
    this.emitStatus();

    this.startupTimeout = setTimeout(() => {
      if (!this.process || this.status.runId !== runId || this.status.hasPythonOutput) {
        return;
      }
      const warningMessage = "Python process started but has not emitted output yet.";
      this.status.message = warningMessage;
      this.appendSystemLog(warningMessage, runId, "warning");
      this.events.emit("warning", {
        type: "warning",
        code: "PIPELINE_NO_OUTPUT_YET",
        message: warningMessage,
        runId,
        timestamp: Date.now(),
      } satisfies PipelineEvent);
      this.emitStatus();
    }, STARTUP_OUTPUT_TIMEOUT_MS);

    this.process.once("spawn", () => {
      this.markProcessStarted(runId, this.process?.pid);
    });

    this.process.on("error", (error) => {
      if (this.status.runId !== runId) return;
      this.clearStartupTimeout();
      this.status.state = "error";
      this.status.error = `Failed to spawn Python process: ${error.message}`;
      this.status.message = "Failed to start Python process.";
      this.status.endedAt = Date.now();
      this.process = null;
      this.emitStatus();
      this.appendSystemLog(this.status.error, runId, "error");
      this.events.emit("error", {
        type: "error",
        code: "PIPELINE_SPAWN_ERROR",
        message: this.status.error,
        runId,
        timestamp: Date.now(),
      } satisfies PipelineEvent);
    });

    this.process.stdout.on("data", (chunk: Buffer) => this.handleOutputChunk(runId, chunk, "stdout"));
    this.process.stderr.on("data", (chunk: Buffer) => this.handleOutputChunk(runId, chunk, "stderr"));

    if (this.process.pid) {
      this.markProcessStarted(runId, this.process.pid);
    }

    this.process.on("exit", (code, signal) => {
      if (this.status.runId !== runId) return;
      this.clearStartupTimeout();
      this.flushRemainders(runId);
      this.process = null;
      this.status.endedAt = Date.now();

      if (this.status.state === "stopping") {
        this.status.state = "idle";
        this.status.message = "Pipeline stopped.";
        this.status.error = undefined;
      } else if (code === 0) {
        this.status.state = "done";
        this.status.message = "Pipeline completed successfully.";
        this.status.error = undefined;
      } else {
        this.status.state = "error";
        this.status.error = `Pipeline exited with code ${code}${signal ? ` (signal: ${signal})` : ""}.`;
        this.status.message = "Pipeline execution failed.";
      }

      this.events.emit("process-exit", {
        type: "process-exit",
        runId,
        code,
        signal,
        timestamp: Date.now(),
      } satisfies PipelineEvent);
      this.appendSystemLog(
        `Python process exited with code ${code}${signal ? ` and signal ${signal}` : ""}.`,
        runId,
        code === 0 ? "info" : "error",
      );
      this.emitStatus();
    });

    return {
      started: true,
      runId,
      acceptedCommand: [...spawned.command],
      state: this.status.state,
      inputDir: preflight.inputDir,
      csvPath: preflight.csvPath,
    };
  }

  stop() {
    if (!this.process) {
      return { stopped: false, message: "No pipeline is running." };
    }

    this.status.state = "stopping";
    this.status.message = "Stop signal sent.";
    this.emitStatus();
    this.appendSystemLog("Stop signal sent to Python process.", this.status.runId);
    this.process.kill();
    return { stopped: true, message: "Stop signal sent." };
  }

  private emitStatus() {
    this.events.emit("status", {
      type: "status",
      status: { ...this.status },
    } satisfies PipelineEvent);
  }

  private markProcessStarted(runId: string, pid?: number) {
    if (this.status.runId !== runId || this.status.state !== "starting") return;
    this.status.state = "running";
    this.status.message = "Python pipeline started.";
    this.emitStatus();
    this.events.emit("process-started", {
      type: "process-started",
      runId,
      pid: pid ?? -1,
      command: this.activeCommand,
      timestamp: Date.now(),
    } satisfies PipelineEvent);
    this.appendSystemLog(`Python process started (pid=${pid ?? "n/a"}).`, runId);
  }

  private appendSystemLog(line: string, runId?: string, level: "info" | "warning" | "error" = "info") {
    this.debugLogBuffer.append({
      channel: "system",
      line,
      runId,
      level,
    });
    if (runId && this.status.runId === runId) {
      this.status.systemLogLines += 1;
    }
  }

  private appendPythonLog(line: string, runId: string) {
    this.debugLogBuffer.append({
      channel: "python",
      line,
      runId,
    });
    if (this.status.runId === runId) {
      this.status.pythonLogLines += 1;
    }
  }

  private handleOutputChunk(runId: string, chunk: Buffer, source: "stdout" | "stderr") {
    const text = chunk.toString("utf8");
    const remainder = source === "stdout" ? this.stdoutRemainder : this.stderrRemainder;
    const combined = remainder + text;
    const parts = combined.split(/\r?\n/);
    const pending = parts.pop() ?? "";

    for (const part of parts) {
      this.handleOutputLine(runId, part);
    }

    if (source === "stdout") {
      this.stdoutRemainder = pending;
    } else {
      this.stderrRemainder = pending;
    }
  }

  private handleOutputLine(runId: string, rawLine: string) {
    const line = rawLine.trimEnd();
    if (!line || this.status.runId !== runId) return;

    if (!this.status.hasPythonOutput) {
      this.status.hasPythonOutput = true;
      this.status.message = "Streaming Python output.";
      this.clearStartupTimeout();
    }

    const match = PROGRESS_RE.exec(line);
    if (match) {
      this.status.progress = Number(match[1]);
      this.status.total = Number(match[2]);
      this.status.message = `Running ${this.status.progress}/${this.status.total}`;
    }

    this.appendPythonLog(line, runId);
    this.emitStatus();
  }

  private flushRemainders(runId: string) {
    if (this.stdoutRemainder.trim()) {
      this.handleOutputLine(runId, this.stdoutRemainder);
    }
    if (this.stderrRemainder.trim()) {
      this.handleOutputLine(runId, this.stderrRemainder);
    }
    this.stdoutRemainder = "";
    this.stderrRemainder = "";
  }

  private clearStartupTimeout() {
    if (!this.startupTimeout) return;
    clearTimeout(this.startupTimeout);
    this.startupTimeout = null;
  }

  private nextRunId() {
    return `run-${Date.now().toString(36)}-${this.runCounter++}`;
  }

  private async preflight(request: PipelineRunRequest): Promise<PreflightResult> {
    const rawInputDir = (request.inputDir ?? "").trim();
    if (!rawInputDir) {
      throw new PipelineManagerError("Input directory is required.", "PIPELINE_PREFLIGHT_FAILED", 400);
    }
    const inputDir = path.resolve(rawInputDir);

    try {
      const stat = await fs.stat(inputDir);
      if (!stat.isDirectory()) {
        throw new PipelineManagerError(
          `Input path is not a directory: ${inputDir}`,
          "PIPELINE_PREFLIGHT_FAILED",
          400,
        );
      }
      await fs.access(inputDir, constants.R_OK);
    } catch (error) {
      if (error instanceof PipelineManagerError) throw error;
      throw new PipelineManagerError(
        `Input directory is not accessible: ${inputDir}`,
        "PIPELINE_PREFLIGHT_FAILED",
        400,
      );
    }

    let csvCandidate = request.csvOutput?.trim() ? request.csvOutput.trim() : path.join(inputDir, "photocat_audit.csv");
    let csvPath = path.resolve(csvCandidate);
    // If the user points csvOutput at a directory, write photocat_audit.csv inside it.
    try {
      const stat = await fs.stat(csvPath);
      if (stat.isDirectory()) {
        csvPath = path.join(csvPath, "photocat_audit.csv");
      }
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== "ENOENT") {
        throw new PipelineManagerError(
          `CSV output path is not writable: ${csvPath}`,
          "PIPELINE_PREFLIGHT_FAILED",
          400,
        );
      }
    }

    try {
      await fs.mkdir(path.dirname(csvPath), { recursive: true });
    } catch {
      throw new PipelineManagerError(
        `Cannot create CSV output directory for: ${csvPath}`,
        "PIPELINE_PREFLIGHT_FAILED",
        400,
      );
    }

    try {
      await fs.access(backendConfig.pythonMainPath, constants.F_OK);
    } catch {
      throw new PipelineManagerError(
        `Python pipeline entry point not found: ${backendConfig.pythonMainPath}`,
        "PIPELINE_PREFLIGHT_FAILED",
        500,
      );
    }

    try {
      await runExecFile(backendConfig.pythonCommand, ["--version"]);
    } catch {
      throw new PipelineManagerError(
        `Python executable is not available: ${backendConfig.pythonCommand}`,
        "PIPELINE_PREFLIGHT_FAILED",
        400,
      );
    }

    return { inputDir, csvPath };
  }
}
