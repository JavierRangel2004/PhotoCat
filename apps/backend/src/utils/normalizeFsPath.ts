import path from "node:path";

/** Normalize user/clipboard paths so backslashes become slashes before path.resolve (POSIX). */
export function normalizeFsPathForResolve(input: string): string {
  return String(input ?? "")
    .trim()
    .replace(/\\/g, "/");
}

/** Resolve to an absolute path; input should be trimmed and slashes normalized. */
export function resolveAbsolutePath(input: string): string {
  const s = normalizeFsPathForResolve(input);
  if (!s) return "";
  return path.resolve(s);
}
