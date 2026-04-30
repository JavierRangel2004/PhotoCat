import type { FastifyInstance } from "fastify";
import type { PipelineEvent, PipelineLogEntry, PipelineRunRequest } from "../../../../shared/types/review.js";
import { LogBuffer } from "../services/logBuffer.js";
import { PipelineManager, PipelineManagerError } from "../services/pipelineManager.js";

export async function registerPipelineRoutes(
  app: FastifyInstance,
  pipelineManager: PipelineManager,
  debugLogBuffer: LogBuffer,
) {
  app.get("/api/pipeline/status", async () => pipelineManager.getStatus());

  app.get("/api/pipeline/logs", async () => ({ entries: debugLogBuffer.getEntries() }));

  app.get("/api/pipeline/events", (request, reply) => {
    // Hijack the response so Fastify does not auto-send when the handler returns.
    reply.hijack();

    reply.raw.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "Access-Control-Allow-Origin": "*",
    });

    const emitSseEvent = (eventName: string, payload: PipelineEvent) => {
      if (!reply.raw.writable) return;
      reply.raw.write(`event: ${eventName}\ndata: ${JSON.stringify(payload)}\n\n`);
    };

    // Send a keep-alive comment every 15 seconds so proxies/browsers don't time out.
    const keepAlive = setInterval(() => {
      if (!reply.raw.writable) {
        clearInterval(keepAlive);
        return;
      }
      reply.raw.write(":keepalive\n\n");
    }, 15_000);

    const onLog = (entry: PipelineLogEntry) => {
      emitSseEvent("log", { type: "log", entry });
    };
    const onStatus = (eventPayload: PipelineEvent) => {
      emitSseEvent("status", eventPayload);
    };
    const onWarning = (eventPayload: PipelineEvent) => emitSseEvent("warning", eventPayload);
    const onError = (eventPayload: PipelineEvent) => emitSseEvent("error", eventPayload);
    const onProcessStarted = (eventPayload: PipelineEvent) => emitSseEvent("process-started", eventPayload);
    const onProcessExit = (eventPayload: PipelineEvent) => emitSseEvent("process-exit", eventPayload);

    const initialStatus = pipelineManager.getStatus();
    emitSseEvent("status", { type: "status", status: initialStatus });

    debugLogBuffer.events.on("entry", onLog);
    pipelineManager.events.on("status", onStatus);
    pipelineManager.events.on("warning", onWarning);
    pipelineManager.events.on("error", onError);
    pipelineManager.events.on("process-started", onProcessStarted);
    pipelineManager.events.on("process-exit", onProcessExit);

    const cleanup = () => {
      clearInterval(keepAlive);
      debugLogBuffer.events.off("entry", onLog);
      pipelineManager.events.off("status", onStatus);
      pipelineManager.events.off("warning", onWarning);
      pipelineManager.events.off("error", onError);
      pipelineManager.events.off("process-started", onProcessStarted);
      pipelineManager.events.off("process-exit", onProcessExit);
    };
    request.raw.on("close", cleanup);
    reply.raw.on("close", cleanup);
  });

  app.post<{ Body: PipelineRunRequest }>("/api/pipeline/run", async (request, reply) => {
    try {
      return await pipelineManager.start(request.body);
    } catch (error) {
      const err = error instanceof PipelineManagerError ? error : new PipelineManagerError((error as Error).message, "PIPELINE_START_FAILED", 500);
      reply.code(err.statusCode);
      return {
        error: err.message,
        code: err.code,
      };
    }
  });

  app.post("/api/pipeline/stop", async () => pipelineManager.stop());
}
