import type { ReviewItem, ReviewSession, UserLabel } from "../../../../shared/types/review.js";
import { exportCorrectedCsv, getOrganizePreview, loadReviewSession } from "./pythonBridge.js";

type CorrectionEntry = {
  user_genre?: string;
  user_label?: UserLabel;
};

type PythonSessionPayload = ReviewSession;

export class ReviewSessionService {
  private session: ReviewSession | null = null;
  private corrections: Record<string, CorrectionEntry> = {};

  async load(csvPath: string, imageDir: string) {
    const payload = (await loadReviewSession(csvPath, imageDir)) as PythonSessionPayload;
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
    this.corrections[item.filename] = {
      ...this.corrections[item.filename],
      user_genre: genre,
    };
    return item;
  }

  setLabel(itemId: string, label: UserLabel) {
    const item = this.requireItem(itemId);
    item.userLabel = label;
    this.corrections[item.filename] = {
      ...this.corrections[item.filename],
      user_label: label,
    };
    return item;
  }

  async exportCorrected() {
    const session = this.requireSession();
    return exportCorrectedCsv(session.csvPath, session.imageDir, this.corrections);
  }

  async organizePreview() {
    const session = this.requireSession();
    return getOrganizePreview(session.csvPath, session.imageDir, this.corrections);
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
}
