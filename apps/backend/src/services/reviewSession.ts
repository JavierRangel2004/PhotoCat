import type { ReviewItem, ReviewSession, UserLabel } from "../../../../shared/types/review.js";
import { constants, promises as fs } from "node:fs";
import path from "node:path";
import { exportCorrectedCsv, loadReviewSession } from "./pythonBridge.js";

type CorrectionEntry = {
  user_genre?: string;
  user_label?: UserLabel;
  user_portfolio_category?: string;
};

type PythonSessionPayload = ReviewSession;

export class ReviewSessionService {
  private session: ReviewSession | null = null;
  private corrections: Record<string, CorrectionEntry> = {};

  async load(csvPath: string, imageDir: string) {
    const normalizedImageDir = path.resolve(imageDir.trim());
    const resolvedCsvPath = await this.resolveCsvPath(path.resolve(csvPath.trim()));
    await this.validateLoadPaths(resolvedCsvPath, normalizedImageDir);

    const payload = (await loadReviewSession(resolvedCsvPath, normalizedImageDir)) as PythonSessionPayload;
    this.session = payload;
    this.corrections = {};
    return payload;
  }

  getSession() {
    return this.session;
  }

  getAllowedRoots() {
    if (!this.session) {
      return [];
    }
    return [this.session.imageDir];
  }

  setGenre(itemId: string, genre: string) {
    const item = this.requireItem(itemId);
    item.userGenre = genre;
    item.effectiveGenre = genre || item.finalGenre;
    const key = item.rowKey || item.filename;
    this.corrections[key] = {
      ...this.corrections[key],
      user_genre: genre,
    };
    return item;
  }

  setLabel(itemId: string, label: UserLabel) {
    const item = this.requireItem(itemId);
    item.userLabel = label;
    const key = item.rowKey || item.filename;
    this.corrections[key] = {
      ...this.corrections[key],
      user_label: label,
    };
    return item;
  }

  setPortfolioCategory(itemId: string, portfolioCategory: string) {
    const item = this.requireItem(itemId);
    item.userPortfolioCategory = portfolioCategory;
    const key = item.rowKey || item.filename;
    this.corrections[key] = {
      ...this.corrections[key],
      user_portfolio_category: portfolioCategory,
    };
    return item;
  }

  async exportCorrected() {
    const session = this.requireSession();
    return exportCorrectedCsv(session.csvPath, session.imageDir, this.corrections);
  }

  private requireSession() {
    if (!this.session) {
      throw new Error("No review session loaded.");
    }
    return this.session;
  }

  private requireItem(itemId: string): ReviewItem {
    const session = this.requireSession();
    const item = session.items.find((entry) => entry.id === itemId);
    if (!item) {
      throw new Error(`Review item not found: ${itemId}`);
    }
    return item;
  }

  private async resolveCsvPath(csvPath: string): Promise<string> {
    const stat = await fs.stat(csvPath).catch(() => null);
    if (!stat) {
      throw new Error(`CSV file not found: ${csvPath}`);
    }
    if (stat.isFile()) {
      return csvPath;
    }
    if (stat.isDirectory()) {
      // Auto-discover a CSV file inside the directory.
      const entries = await fs.readdir(csvPath);
      const csvFiles = entries.filter((f) => f.toLowerCase().endsWith(".csv")).sort();
      // Prefer the default audit CSV name.
      const preferred = csvFiles.find((f) => f === "photocat_audit.csv") ?? csvFiles[0];
      if (preferred) {
        return path.join(csvPath, preferred);
      }
      throw new Error(`No CSV files found in directory: ${csvPath}`);
    }
    throw new Error(`CSV path must be a file or directory: ${csvPath}`);
  }

  private async validateLoadPaths(csvPath: string, imageDir: string) {
    if (!csvPath) {
      throw new Error("CSV path is required.");
    }
    if (!imageDir) {
      throw new Error("Image directory is required.");
    }

    try {
      await fs.access(csvPath, constants.R_OK);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        throw new Error(`CSV file not found: ${csvPath}`);
      }
      throw error;
    }

    try {
      const imageStat = await fs.stat(imageDir);
      if (!imageStat.isDirectory()) {
        throw new Error(`Image directory must be a folder: ${imageDir}`);
      }
      await fs.access(imageDir, constants.R_OK);
    } catch (error) {
      if (error instanceof Error && error.message.startsWith("Image directory must be a folder")) {
        throw error;
      }
      if ((error as NodeJS.ErrnoException).code === "ENOENT") {
        throw new Error(`Image directory not found: ${imageDir}`);
      }
      throw error;
    }
  }
}
