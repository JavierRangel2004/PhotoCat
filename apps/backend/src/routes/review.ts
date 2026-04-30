import type { FastifyInstance } from "fastify";
import { ReviewSessionService } from "../services/reviewSession.js";
import {
  organizeFromCsvPreview,
  organizeFromCsvCommit,
  restoreFromManifest,
} from "../services/pythonBridge.js";
import { resolveAbsolutePath } from "../utils/normalizeFsPath.js";

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

  app.post<{ Body: { itemId: string; portfolioCategory: string } }>(
    "/api/review/item/portfolio-category",
    async (request) => {
      return reviewService.setPortfolioCategory(
        request.body.itemId,
        request.body.portfolioCategory,
      );
    },
  );

  // --- Organize from corrected CSV ---
  app.post<{ Body: { csvPath: string; outputDir: string; mode?: string } }>(
    "/api/review/organize-from-csv/preview",
    async (request) => {
      const csvPath = resolveAbsolutePath(request.body.csvPath);
      const outputDir = resolveAbsolutePath(request.body.outputDir);
      return organizeFromCsvPreview(csvPath, outputDir, {
        organizeMode: request.body.mode,
      });
    },
  );

  app.post<{
    Body: {
      csvPath: string;
      outputDir: string;
      dryRun?: boolean;
      includeExcluded?: boolean;
      mode?: string;
    };
  }>("/api/review/organize-from-csv/commit", async (request) => {
    const csvPath = resolveAbsolutePath(request.body.csvPath);
    const outputDir = resolveAbsolutePath(request.body.outputDir);
    return organizeFromCsvCommit(csvPath, outputDir, {
      dryRun: request.body.dryRun,
      includeExcluded: request.body.includeExcluded,
      organizeMode: request.body.mode,
    });
  });

  app.post<{ Body: { manifestPath: string; dryRun?: boolean } }>(
    "/api/review/restore-from-manifest",
    async (request) => {
      return restoreFromManifest(request.body.manifestPath, request.body.dryRun);
    },
  );
}
