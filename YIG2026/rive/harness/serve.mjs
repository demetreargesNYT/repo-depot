// Local server for the review harness. Serves the page, the pinned Rive web runtime, the engineering
// files as-is, and the chapter's built .riv at the path engineering's code loads it from.
// It rebuilds the .riv with the Rive CLI whenever scene.rml is newer than the build.
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const chapter = process.env.CHAPTER || "ch2";
const port = Number(process.env.PORT || 8765);
const rive = process.env.RIVE_BIN || path.join(os.homedir(), ".rive/bin/rive");
const projectDir = path.join(repo, "chapters", chapter);

const roots = {
  "/vendor/rive/": path.join(here, "node_modules/@rive-app/canvas"),
  "/engineering/": path.join(repo, "engineering"),
  "/art/": path.join(repo, "art"),
  "/fonts/": path.join(here, "fonts"),
};

// The runtime's rive.js is UMD: it sets window.rive when loaded as a classic script. Engineering's code
// does `import { Rive } from "@rive-app/canvas"`, so the import map points that name here.
const esmShim = `const r = window.rive;
export const { Rive, Layout, Fit, Alignment, RuntimeLoader, EventType, StateMachineInputType } = r;
export default r;
`;

const pageFiles = new Set(["harness.js", "text-layer.css", "copy.html"]);

const types = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".wasm": "application/wasm", ".svg": "image/svg+xml",
  ".png": "image/png", ".woff2": "font/woff2", ".riv": "application/octet-stream", ".map": "application/json",
};

function newestBuild() {
  const dir = path.join(projectDir, "build");
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".riv")).map((f) => path.join(dir, f));
  files.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  return files[0] || null;
}

let building = null;
function ensureBuilt() {
  const scene = fs.statSync(path.join(projectDir, "scene.rml")).mtimeMs;
  const built = newestBuild();
  if (built && fs.statSync(built).mtimeMs >= scene) return Promise.resolve({ built, rebuilt: false });
  building ??= new Promise((resolve, reject) => {
    execFile(rive, [projectDir, "--once"], (err, stdout, stderr) => {
      building = null;
      if (err) return reject(new Error(`rive --once failed:\n${stdout}\n${stderr}`));
      resolve({ built: newestBuild(), rebuilt: true });
    });
  });
  return building;
}

function sendFile(res, file) {
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404).end("not found"); return; }
    res.writeHead(200, { "content-type": types[path.extname(file)] || "application/octet-stream", "cache-control": "no-store" });
    res.end(data);
  });
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const p = decodeURIComponent(url.pathname);
  try {
    if (p === "/" || p === "/index.html") return sendFile(res, path.join(here, "index.html"));
    if (pageFiles.has(p.slice(1))) return sendFile(res, path.join(here, p.slice(1)));
    if (p === "/vendor/rive-esm.js") {
      res.writeHead(200, { "content-type": "text/javascript", "cache-control": "no-store" });
      return res.end(esmShim);
    }
    if (p === "/yig/chapter-2.riv") {
      const { built } = await ensureBuilt();
      return sendFile(res, built);
    }
    if (p === "/api/riv") {
      const { built, rebuilt } = await ensureBuilt();
      const st = fs.statSync(built);
      res.writeHead(200, { "content-type": "application/json", "cache-control": "no-store" });
      return res.end(JSON.stringify({ chapter, file: path.relative(repo, built), bytes: st.size, builtAt: st.mtime.toISOString(), rebuilt }));
    }
    for (const [prefix, root] of Object.entries(roots)) {
      if (!p.startsWith(prefix)) continue;
      const file = path.resolve(root, p.slice(prefix.length));
      if (file !== root && !file.startsWith(root + path.sep)) break; // no path traversal
      return sendFile(res, file);
    }
    res.writeHead(404).end("not found");
  } catch (e) {
    res.writeHead(500, { "content-type": "text/plain" }).end(String(e.message || e));
  }
}).listen(port, "127.0.0.1", () => {
  console.log(`harness for ${chapter}: http://127.0.0.1:${port}/`);
});
