import { spawn } from "node:child_process";
import net from "node:net";

const BACKEND_HOST = process.env.PHOTOCAT_BACKEND_HOST ?? "127.0.0.1";
const PREFERRED_BACKEND_PORT = Number(process.env.PHOTOCAT_BACKEND_PORT ?? "8797");
const PREFERRED_DESKTOP_PORT = Number(process.env.PHOTOCAT_DESKTOP_PORT ?? "4173");

const children = [];

function isPortAvailable(host, port) {
  return new Promise((resolve) => {
    const server = net.createServer();

    server.once("error", () => {
      resolve(false);
    });

    server.once("listening", () => {
      server.close(() => resolve(true));
    });

    server.listen(port, host);
  });
}

async function findAvailablePort(host, preferredPort, maxAttempts = 20) {
  for (let offset = 0; offset < maxAttempts; offset += 1) {
    const candidate = preferredPort + offset;
    if (await isPortAvailable(host, candidate)) {
      return candidate;
    }
  }

  throw new Error(`Could not find an open port near ${host}:${preferredPort}`);
}

function startProcess(name, args, runtimeEnv) {
  const command =
    process.platform === "win32"
      ? process.env.ComSpec ?? "C:\\Windows\\System32\\cmd.exe"
      : "npm";
  const commandArgs =
    process.platform === "win32" ? ["/d", "/s", "/c", "npm", ...args] : args;

  const child = spawn(command, commandArgs, {
    stdio: "inherit",
    shell: false,
    env: runtimeEnv,
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      shutdown(signal);
      return;
    }

    if (code && code !== 0) {
      process.exitCode = code;
      shutdown("SIGTERM");
    }
  });

  children.push({ name, child });
}

function shutdown(signal) {
  for (const { child } of children) {
    if (!child.killed) {
      child.kill(signal);
    }
  }
}

process.on("SIGINT", () => {
  shutdown("SIGINT");
  process.exit(0);
});

process.on("SIGTERM", () => {
  shutdown("SIGTERM");
  process.exit(0);
});

async function main() {
  const backendPort = await findAvailablePort(BACKEND_HOST, PREFERRED_BACKEND_PORT);
  const desktopPort = await findAvailablePort("127.0.0.1", PREFERRED_DESKTOP_PORT);
  const desktopUrl = process.env.PHOTOCAT_DESKTOP_URL ?? `http://127.0.0.1:${desktopPort}`;
  const apiBaseUrl =
    process.env.VITE_PHOTOCAT_API_BASE_URL ?? `http://${BACKEND_HOST}:${backendPort}`;

  if (backendPort !== PREFERRED_BACKEND_PORT) {
    console.log(
      `[photocat] preferred backend port ${PREFERRED_BACKEND_PORT} is busy, using ${backendPort}`,
    );
  }

  if (desktopPort !== PREFERRED_DESKTOP_PORT) {
    console.log(
      `[photocat] preferred frontend port ${PREFERRED_DESKTOP_PORT} is busy, using ${desktopPort}`,
    );
  }

  const runtimeEnv = {
    ...process.env,
    PHOTOCAT_BACKEND_HOST: BACKEND_HOST,
    PHOTOCAT_BACKEND_PORT: String(backendPort),
    PHOTOCAT_DESKTOP_PORT: String(desktopPort),
    PHOTOCAT_DESKTOP_URL: desktopUrl,
    VITE_PHOTOCAT_API_BASE_URL: apiBaseUrl,
  };

  console.log(
    `[photocat] starting backend on http://${BACKEND_HOST}:${backendPort} and frontend on ${desktopUrl}`,
  );

  startProcess("backend", ["--workspace", "@photocat/backend", "run", "dev"], runtimeEnv);
  startProcess("desktop", ["--workspace", "@photocat/desktop", "run", "dev"], runtimeEnv);
}

main().catch((error) => {
  console.error("[photocat] failed to prepare dev ports:", error);
  process.exit(1);
});
