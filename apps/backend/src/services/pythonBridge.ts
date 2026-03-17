import { execFile, spawn, type ChildProcessByStdio } from "node:child_process";
import type { Readable } from "node:stream";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { backendConfig } from "../config.js";

type PythonArgs = string[];

function parseBridgeErrorPayload(output: string) {
  const trimmed = output.trim();
  if (!trimmed) return null;
  try {
    const parsed = JSON.parse(trimmed) as { error?: string; message?: string };
    return parsed.error ?? parsed.message ?? null;
  } catch {
    return null;
  }
}

function execPythonJson(args: PythonArgs): Promise<unknown> {
  return new Promise((resolve, reject) => {
    execFile(
      backendConfig.pythonCommand,
      args,
      { cwd: backendConfig.repoRoot, maxBuffer: 16 * 1024 * 1024 },
      (error, stdout, stderr) => {
        if (error) {
          const bridgeError =
            parseBridgeErrorPayload(stdout) ??
            parseBridgeErrorPayload(stderr) ??
            (stderr.trim() || null) ??
            error.message;
          reject(new Error(bridgeError));
          return;
        }
        try {
          resolve(JSON.parse(stdout));
        } catch (parseError) {
          reject(new Error(`Invalid JSON from Python bridge: ${String(parseError)}`));
        }
      },
    );
  });
}

export async function loadReviewSession(csvPath: string, imageDir: string) {
  return execPythonJson([backendConfig.pythonBridgePath, "load-session", "--csv-path", csvPath, "--image-dir", imageDir]);
}

export async function exportCorrectedCsv(
  csvPath: string,
  imageDir: string,
  corrections: Record<string, { user_genre?: string; user_label?: string; user_portfolio_category?: string }>,
) {
  const correctionsPath = await writeCorrectionsTempFile(corrections);
  return execPythonJson([
    backendConfig.pythonBridgePath,
    "export-corrected",
    "--csv-path",
    csvPath,
    "--image-dir",
    imageDir,
    "--corrections-path",
    correctionsPath,
  ]);
}

export async function organizeFromCsvPreview(csvPath: string, outputDir: string) {
  return execPythonJson([
    backendConfig.pythonBridgePath,
    "organize-from-csv-preview",
    "--csv-path",
    csvPath,
    "--output-dir",
    outputDir,
  ]);
}

export async function organizeFromCsvCommit(
  csvPath: string,
  outputDir: string,
  options: { dryRun?: boolean; includeExcluded?: boolean } = {},
) {
  const args = [
    backendConfig.pythonBridgePath,
    "organize-from-csv-commit",
    "--csv-path",
    csvPath,
    "--output-dir",
    outputDir,
  ];
  if (options.dryRun) args.push("--dry-run");
  if (options.includeExcluded === false) args.push("--no-include-excluded");
  else if (options.includeExcluded === true) args.push("--include-excluded");
  return execPythonJson(args);
}

export async function restoreFromManifest(manifestPath: string, dryRun = false) {
  const args = [
    backendConfig.pythonBridgePath,
    "restore-from-manifest",
    "--manifest-path",
    manifestPath,
  ];
  if (dryRun) args.push("--dry-run");
  return execPythonJson(args);
}

export type SpawnedPipeline = {
  process: ChildProcessByStdio<null, Readable, Readable>;
  command: string[];
};

export function spawnPipeline(args: string[]): SpawnedPipeline {
  const command = [backendConfig.pythonCommand, "-u", backendConfig.pythonMainPath, ...args];
  const process = spawn(command[0], command.slice(1), {
    cwd: backendConfig.repoRoot,
    stdio: ["ignore", "pipe", "pipe"],
  });
  return { process, command };
}

async function writeCorrectionsTempFile(
  corrections: Record<string, { user_genre?: string; user_label?: string; user_portfolio_category?: string }>,
) {
  const filePath = path.join(os.tmpdir(), `photocat-corrections-${Date.now()}.json`);
  await fs.writeFile(filePath, JSON.stringify(corrections, null, 2), "utf8");
  return filePath;
}
