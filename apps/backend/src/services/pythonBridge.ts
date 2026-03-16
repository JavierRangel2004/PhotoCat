import { execFile, spawn, type ChildProcessByStdio } from "node:child_process";
import type { Readable } from "node:stream";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { backendConfig } from "../config.js";

type PythonArgs = string[];

function execPythonJson(args: PythonArgs): Promise<unknown> {
  return new Promise((resolve, reject) => {
    execFile(
      backendConfig.pythonCommand,
      args,
      { cwd: backendConfig.repoRoot, maxBuffer: 16 * 1024 * 1024 },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(stderr || error.message));
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
  corrections: Record<string, { user_genre?: string; user_label?: string }>,
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

export async function getOrganizePreview(
  csvPath: string,
  imageDir: string,
  corrections: Record<string, { user_genre?: string; user_label?: string }>,
) {
  const correctionsPath = await writeCorrectionsTempFile(corrections);
  return execPythonJson([
    backendConfig.pythonBridgePath,
    "organize-preview",
    "--csv-path",
    csvPath,
    "--image-dir",
    imageDir,
    "--corrections-path",
    correctionsPath,
  ]);
}

export function spawnPipeline(args: string[]): ChildProcessByStdio<null, Readable, Readable> {
  return spawn(backendConfig.pythonCommand, [backendConfig.pythonMainPath, ...args], {
    cwd: backendConfig.repoRoot,
    stdio: ["ignore", "pipe", "pipe"],
  });
}

async function writeCorrectionsTempFile(
  corrections: Record<string, { user_genre?: string; user_label?: string }>,
) {
  const filePath = path.join(os.tmpdir(), `photocat-corrections-${Date.now()}.json`);
  await fs.writeFile(filePath, JSON.stringify(corrections, null, 2), "utf8");
  return filePath;
}
