import { createReadStream } from "node:fs";
import path from "node:path";
import type { FastifyInstance } from "fastify";
import { ReviewSessionService } from "../services/reviewSession.js";

const MIME_BY_EXT: Record<string, string> = {
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".webp": "image/webp",
  ".tiff": "image/tiff",
};

export async function registerAssetRoutes(app: FastifyInstance, reviewService: ReviewSessionService) {
  app.get<{ Querystring: { path?: string } }>("/api/assets/image", async (request, reply) => {
    const imagePath = request.query.path;
    if (!imagePath) {
      reply.code(400);
      return { error: "Missing path query parameter." };
    }

    const normalized = path.resolve(imagePath);
    const allowedRoots = reviewService.getAllowedRoots();
    const allowed = allowedRoots.some((root) => normalized.startsWith(path.resolve(root)));
    if (!allowed) {
      reply.code(403);
      return { error: "Image path is outside the active review roots." };
    }

    const ext = path.extname(normalized).toLowerCase();
    reply.header("Content-Type", MIME_BY_EXT[ext] ?? "application/octet-stream");
    return reply.send(createReadStream(normalized));
  });
}
