import Fastify from "fastify";
import { backendConfig } from "./config.js";
import { registerAssetRoutes } from "./routes/assets.js";
import { registerPipelineRoutes } from "./routes/pipeline.js";
import { LogBuffer } from "./services/logBuffer.js";
import { registerReviewRoutes } from "./routes/review.js";
import { PipelineManager } from "./services/pipelineManager.js";
import { ReviewSessionService } from "./services/reviewSession.js";

const debugLogBuffer = new LogBuffer();
const app = Fastify({
  logger: {
    stream: {
      write(message: string) {
        process.stdout.write(message);
        debugLogBuffer.append({
          channel: "system",
          line: message,
        });
      },
    },
  },
});
const pipelineManager = new PipelineManager(debugLogBuffer);
const reviewService = new ReviewSessionService();

app.addHook("onRequest", async (request, reply) => {
  reply.header("Access-Control-Allow-Origin", "*");
  reply.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  reply.header("Access-Control-Allow-Headers", "Content-Type");

  if (request.method === "OPTIONS") {
    reply.code(204).send();
  }
});

await registerPipelineRoutes(app, pipelineManager, debugLogBuffer);
await registerReviewRoutes(app, reviewService);
await registerAssetRoutes(app, reviewService);

app.get("/api/health", async () => ({
  ok: true,
  service: "@photocat/backend",
  pythonBoundary: "processing stays in Python",
}));

app.listen({ host: backendConfig.host, port: backendConfig.port }).catch((error) => {
  app.log.error(error);
  process.exit(1);
});
