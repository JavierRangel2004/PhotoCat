import type { FastifyInstance } from "fastify";
import { ReviewSessionService } from "../services/reviewSession.js";

export async function registerReviewRoutes(app: FastifyInstance, reviewService: ReviewSessionService) {
  app.post<{ Body: { csvPath: string; imageDir: string } }>("/api/review/load", async (request) => {
    return reviewService.load(request.body.csvPath, request.body.imageDir);
  });

  app.get("/api/review/session", async () => {
    return reviewService.getSession() ?? { session: null };
  });

  app.post<{ Body: { itemId: string; genre: string } }>("/api/review/item/genre", async (request) => {
    return reviewService.setGenre(request.body.itemId, request.body.genre);
  });

  app.post<{ Body: { itemId: string; label: "" | "correct" | "wrong" } }>("/api/review/item/label", async (request) => {
    return reviewService.setLabel(request.body.itemId, request.body.label);
  });

  app.post("/api/review/export", async () => {
    return reviewService.exportCorrected();
  });

  app.get("/api/review/organize-preview", async () => {
    return reviewService.organizePreview();
  });
}
