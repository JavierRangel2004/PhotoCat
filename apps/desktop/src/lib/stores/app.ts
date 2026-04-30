import { writable } from "svelte/store";
import type { Toast } from "../components/ToastRegion.svelte";

export type ViewId = "dashboard" | "inspector" | "pipeline";

export const currentView = writable<ViewId>("dashboard");
export const toasts = writable<Toast[]>([]);

let nextToastId = 1;

export function pushToast(message: string, tone: Toast["tone"] = "neutral", timeout = 3200) {
  const id = nextToastId++;
  toasts.update((items) => [...items, { id, tone, message }]);
  if (typeof window !== "undefined") {
    window.setTimeout(() => {
      toasts.update((items) => items.filter((item) => item.id !== id));
    }, timeout);
  }
}
