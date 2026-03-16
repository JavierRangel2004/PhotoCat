import { EventEmitter } from "node:events";
import { spawnPipeline } from "./pythonBridge.js";
import type { PipelineRunRequest, PipelineStatus } from "../../../../shared/types/review.js";

const PROGRESS_RE = /\[(\d+)\/(\d+)\]/;

export class PipelineManager {
  private process: ReturnType<typeof spawnPipeline> | null = null;
  private logBuffer: string[] = [];
  private status: PipelineStatus = {
    state: "idle",
    progress: 0,
    total: 0,
    bufferedLogLines: 0,
  };

  readonly events = new EventEmitter();

  getStatus() {
    return this.status;
  }

  getLogs() {
    return [...this.logBuffer];
  }

  start(request: PipelineRunRequest) {
    if (this.process) {
      throw new Error("Pipeline already running.");
    }

    const args: string[] = ["--input-dir", request.inputDir];
    if (request.csvOutput) args.push("--csv", request.csvOutput);
    if (request.recursive) args.push("--recursive");
    if (request.writeXmp) args.push("--write-xmp");
    if (request.genreOnly) args.push("--genre-only");
    if (request.noCache) args.push("--no-cache");
    if (request.organize) args.push("--organize");
    if (request.dryRun) args.push("--dry-run");
    if (request.minConfidence !== undefined) args.push("--min-confidence", String(request.minConfidence));
    if (request.workers !== undefined) args.push("--workers", String(request.workers));
    if (request.extensions) args.push("--extensions", request.extensions);

    this.process = spawnPipeline(args);
    this.status = { state: "running", progress: 0, total: 0, bufferedLogLines: 0 };
    this.logBuffer = [];

    const handleChunk = (chunk: Buffer) => {
      const text = chunk.toString("utf8");
      const lines = text.split(/\r?\n/).filter(Boolean);
      for (const line of lines) {
        const match = PROGRESS_RE.exec(line);
        if (match) {
          this.status.progress = Number(match[1]);
          this.status.total = Number(match[2]);
        }
        this.logBuffer.push(line);
        this.status.bufferedLogLines = this.logBuffer.length;
        this.events.emit("log", line);
      }
    };

    this.process.stdout.on("data", handleChunk);
    this.process.stderr.on("data", handleChunk);
    this.process.on("exit", (code) => {
      this.status.state = code === 0 ? "done" : "error";
      if (code !== 0) {
        this.status.error = `Pipeline exited with code ${code}`;
      }
      this.process = null;
      this.events.emit("status", this.status);
    });
  }

  stop() {
    if (!this.process) {
      return { stopped: false, message: "No pipeline is running." };
    }
    this.status.state = "stopping";
    this.process.kill();
    return { stopped: true, message: "Stop signal sent." };
  }
}
