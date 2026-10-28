// Local server for the review harness. Serves the example page (index.html) with the same file names it has in
// the handoff folder: chapter-2-integration.js and yig-text-motion.css from engineering/ as-is, and the chapter's
// built .riv as chapter-2.riv. It rebuilds the .riv with the Rive CLI whenever scene.rml is newer than the build.
// The only addition is a link to the NYT fonts, so the review shows real type; the handoff page falls back cleanly.
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

// the page's own relative URLs, mapped to where the files live in this repo
const files = {
  "/chapter-2-integration.js": path.join(repo, "engineering", "chapter-2-integration.js"),
  "/yig-text-motion.css": path.join(repo, "engineering", "yig-text-motion.css"),
  "/review.js": path.join(here, "review.js"),
};
const fontsRoot = path.join(here, "fonts");

const types = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml",
  ".png": "image/png", ".woff2": "font/woff2", ".riv": "application/octet-stream",
};

function newestBuild() {
  const dir = path.join(projectDir, "build");
  if (!fs.existsSync(dir)) return null;
  const builds = fs.readdirSync(dir).filter((f) => f.endsWith(".riv")).map((f) => path.join(dir, f));
  builds.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  return builds[0] || null;
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

function sendPage(res) {
  fs.readFile(path.join(here, "index.html"), "utf8", (err, html) => {
    if (err) { res.writeHead(500).end(String(err.message)); return; }
    res.writeHead(200, { "content-type": types[".html"], "cache-control": "no-store" });
    // review.js (hash jump, Replay) is ours alone: it is injected here and is not in index.html, so it never ships
    res.end(html.replace("</head>", '<link rel="stylesheet" href="/fonts/fonts.css">\n</head>')
      .replace("</body>", '<script type="module" src="/review.js"></script>\n</body>'));
  });
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const p = decodeURIComponent(url.pathname);
  try {
    if (p === "/" || p === "/index.html") return sendPage(res);
    if (p in files) return sendFile(res, files[p]);
    if (p === "/chapter-2.riv") {
      const { built } = await ensureBuilt();
      return sendFile(res, built);
    }
    if (p.startsWith("/fonts/")) {
      const file = path.resolve(fontsRoot, p.slice("/fonts/".length));
      if (file.startsWith(fontsRoot + path.sep)) return sendFile(res, file); // no path traversal
    }
    res.writeHead(404).end("not found");
  } catch (e) {
    res.writeHead(500, { "content-type": "text/plain" }).end(String(e.message || e));
  }
}).listen(port, "127.0.0.1", () => {
  console.log(`harness for ${chapter}: http://127.0.0.1:${port}/`);
});
