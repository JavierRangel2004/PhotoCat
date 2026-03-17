import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(currentDir, "..", "..", "..");

export const backendConfig = {
  host: process.env.PHOTOCAT_BACKEND_HOST ?? "127.0.0.1",
  port: Number(process.env.PHOTOCAT_BACKEND_PORT ?? "8797"),
  repoRoot,
  pythonCommand: process.env.PHOTOCAT_PYTHON_CMD ?? "python",
  pythonBridgePath: path.join(repoRoot, "src", "api_bridge.py"),
  pythonMainPath: path.join(repoRoot, "src", "main.py"),
};
