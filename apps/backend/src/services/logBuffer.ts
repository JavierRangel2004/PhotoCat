import { EventEmitter } from "node:events";
import type { PipelineLogChannel, PipelineLogEntry, PipelineLogLevel } from "../../../../shared/types/review.js";

type AppendLogOptions = {
  channel: PipelineLogChannel;
  line: string;
  runId?: string;
  level?: PipelineLogLevel;
};

function inferLevel(line: string): PipelineLogLevel {
  if (line.includes('"level":50') || /\[ERROR\]/i.test(line)) return "error";
  if (line.includes('"level":40') || /\[WARN(ING)?\]/i.test(line)) return "warning";
  return "info";
}

export class LogBuffer {
  private readonly entries: PipelineLogEntry[] = [];
  private nextId = 1;
  readonly events = new EventEmitter();

  constructor(private readonly maxEntries = 500) {}

  append(options: AppendLogOptions) {
    const line = options.line.trimEnd();
    if (!line) return;

    const entry: PipelineLogEntry = {
      id: String(this.nextId++),
      timestamp: Date.now(),
      channel: options.channel,
      level: options.level ?? inferLevel(line),
      line,
      runId: options.runId,
    };

    this.entries.push(entry);
    if (this.entries.length > this.maxEntries) {
      this.entries.splice(0, this.entries.length - this.maxEntries);
    }

    this.events.emit("entry", entry);
  }

  getEntries() {
    return [...this.entries];
  }
}
