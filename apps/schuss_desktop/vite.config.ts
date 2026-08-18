import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { createInterface } from "node:readline";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const APP_ROOT = fileURLToPath(new URL(".", import.meta.url));
const REPOSITORY_ROOT = resolve(APP_ROOT, "../..");
const BRIDGE_SCRIPT = resolve(APP_ROOT, "bridge/desktop_core_bridge.py");
const MAX_REQUEST_BYTES = 262_144;

type PendingExchange = {
  resolve: (line: string) => void;
  reject: (error: Error) => void;
};

class DevelopmentCoreBridge {
  private readonly child: ChildProcessWithoutNullStreams;
  private readonly pending: PendingExchange[] = [];
  private ended = false;

  constructor() {
    this.child = spawn(process.env.SCHUSS_DESKTOP_PYTHON ?? "python3", [BRIDGE_SCRIPT], {
      cwd: REPOSITORY_ROOT,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
      stdio: ["pipe", "pipe", "pipe"],
    });
    const lines = createInterface({ input: this.child.stdout });
    lines.on("line", (line) => {
      this.pending.shift()?.resolve(line);
    });
    this.child.once("exit", () => {
      this.ended = true;
      const error = new Error("The local Schuss core bridge ended unexpectedly.");
      for (const exchange of this.pending.splice(0)) {
        exchange.reject(error);
      }
    });
  }

  request(value: unknown): Promise<string> {
    if (this.ended) {
      return Promise.reject(new Error("The local Schuss core bridge is unavailable."));
    }
    return new Promise((resolveLine, rejectLine) => {
      const exchange = { resolve: resolveLine, reject: rejectLine };
      this.pending.push(exchange);
      this.child.stdin.write(`${JSON.stringify(value)}\n`, (error) => {
        if (error) {
          const index = this.pending.indexOf(exchange);
          if (index >= 0) this.pending.splice(index, 1);
          exchange.reject(new Error("The local Schuss core request could not be sent."));
        }
      });
    });
  }

  close(): void {
    this.child.kill();
  }
}

function readJsonBody(request: import("node:http").IncomingMessage): Promise<unknown> {
  return new Promise((resolveBody, rejectBody) => {
    const chunks: Buffer[] = [];
    let size = 0;
    request.on("data", (chunk: Buffer) => {
      size += chunk.length;
      if (size > MAX_REQUEST_BYTES) {
        rejectBody(new Error("Request exceeds the desktop bridge limit."));
        request.destroy();
        return;
      }
      chunks.push(chunk);
    });
    request.on("end", () => {
      try {
        resolveBody(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch {
        rejectBody(new Error("Request is not valid JSON."));
      }
    });
    request.on("error", rejectBody);
  });
}

function developmentBridge(): Plugin {
  return {
    name: "schuss-desktop-development-bridge",
    configureServer(server) {
      const bridge = new DevelopmentCoreBridge();
      server.httpServer?.once("close", () => bridge.close());
      server.middlewares.use("/__schuss/operation", async (request, response) => {
        if (request.method !== "POST") {
          response.statusCode = 405;
          response.setHeader("Allow", "POST");
          response.end("Method not allowed");
          return;
        }
        try {
          const body = await readJsonBody(request);
          const line = await bridge.request(body);
          const parsed = JSON.parse(line) as { schema_version?: string };
          response.statusCode =
            parsed.schema_version === "schuss-desktop-bridge-error-v1" ? 400 : 200;
          response.setHeader("Content-Type", "application/json; charset=utf-8");
          response.setHeader("Cache-Control", "no-store");
          response.end(`${line}\n`);
        } catch {
          response.statusCode = 502;
          response.setHeader("Content-Type", "application/json; charset=utf-8");
          response.end(
            JSON.stringify({
              error: {
                code: "BRIDGE_DEVELOPMENT_TRANSPORT_FAILED",
                message: "The local Schuss core bridge is unavailable.",
              },
              schema_version: "schuss-desktop-bridge-error-v1",
            }),
          );
        }
      });
    },
  };
}

export default defineConfig({
  clearScreen: false,
  plugins: [react(), developmentBridge()],
  server: {
    host: "127.0.0.1",
    port: 1420,
    strictPort: true,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
});
