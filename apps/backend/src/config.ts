import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(currentDir, "..", "..", "..");

function detectPythonCommand(): string {
  if (process.env.PHOTOCAT_PYTHON_CMD) {
    return process.env.PHOTOCAT_PYTHON_CMD;
  }
  // Prefer venv Python so the correct packages are available.
  const venvPaths =
    process.platform === "win32"
      ? [path.join(repoRoot, "venv", "Scripts", "python.exe")]
      : [path.join(repoRoot, "venv", "bin", "python")];
  for (const venvPython of venvPaths) {
    if (existsSync(venvPython)) {
      return venvPython;
    }
  }
  return "python";
}

export const backendConfig = {
  host: process.env.PHOTOCAT_BACKEND_HOST ?? "127.0.0.1",
  port: Number(process.env.PHOTOCAT_BACKEND_PORT ?? "8797"),
  repoRoot,
  pythonCommand: detectPythonCommand(),
  pythonBridgePath: path.join(repoRoot, "src", "api_bridge.py"),
  pythonMainPath: path.join(repoRoot, "src", "main.py"),
};
