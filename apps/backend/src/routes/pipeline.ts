import type { FastifyInstance } from "fastify";
import type { PipelineRunRequest } from "../../../../shared/types/review.js";
import { PipelineManager } from "../services/pipelineManager.js";

export async function registerPipelineRoutes(app: FastifyInstance, pipelineManager: PipelineManager) {
  app.get("/api/pipeline/status", async () => pipelineManager.getStatus());

  app.get("/api/pipeline/logs", async () => ({ lines: pipelineManager.getLogs() }));

  app.get("/api/pipeline/events", async (request, reply) => {
    reply.raw.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    });

    const onLog = (line: string) => {
      reply.raw.write(`event: log\ndata: ${JSON.stringify({ line })}\n\n`);
    };
    const onStatus = (status: unknown) => {
      reply.raw.write(`event: status\ndata: ${JSON.stringify(status)}\n\n`);
    };

    pipelineManager.events.on("log", onLog);
    pipelineManager.events.on("status", onStatus);
    request.raw.on("close", () => {
      pipelineManager.events.off("log", onLog);
      pipelineManager.events.off("status", onStatus);
    });
  });

  app.post<{ Body: PipelineRunRequest }>("/api/pipeline/run", async (request) => {
    pipelineManager.start(request.body);
    return { started: true };
  });

  app.post("/api/pipeline/stop", async () => pipelineManager.stop());
}
