/**
 * Browser-safe path helpers (no node:path). Used for organize defaults and display.
 */

/** Trim, normalize separators to `/`, fix common macOS paste of `\Users\...`. */
export function normalizeOrganizePath(input: string): string {
  let s = String(input ?? "").trim();
  if (!s) return "";
  s = s.replace(/\\/g, "/");
  // Pasted Windows-style absolute home path on macOS
  if (s.startsWith("/Users/")) {
    return s;
  }
  if (/^Users\/[^/]+/.test(s)) {
    return `/${s}`;
  }
  if (s.startsWith("Users/")) {
    return `/${s}`;
  }
  return s;
}

/** Directory portion using both `/` and `\` as separators (before normalize). */
export function dirnameForPath(filePath: string): string {
  const normalized = String(filePath ?? "").replace(/\\/g, "/");
  const i = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
  if (i < 0) return "";
  return normalized.slice(0, i);
}

export function joinPosix(dir: string, ...segments: string[]): string {
  const base = String(dir ?? "")
    .trim()
    .replace(/[\\/]+$/, "");
  const rest = segments
    .map((s) => String(s ?? "").replace(/^[\\/]+/, "").replace(/\\/g, "/"))
    .filter(Boolean)
    .join("/");
  if (!base) return rest;
  if (!rest) return base;
  return `${base}/${rest}`;
}

export function defaultOutputDirFromCsv(csvPath: string): string {
  const dir = dirnameForPath(csvPath);
  if (!dir) return "";
  return joinPosix(normalizeOrganizePath(dir), "photocat_portfolio_ready");
}
