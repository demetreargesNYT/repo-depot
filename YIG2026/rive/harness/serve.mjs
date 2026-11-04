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
import { ROOT as SCRATCH_ROOT } from "./scratch.mjs";   // the finesse notes live in its finesse-notes/, shared by every session

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const chapter = process.env.CHAPTER || "ch2";
const port = Number(process.env.PORT || 8765);
const rive = process.env.RIVE_BIN || path.join(os.homedir(), ".rive/bin/rive");
const projectDir = path.join(repo, "chapters", chapter);
// every Rive file the review pages can ask for, by the URL they use. Each is rebuilt with the CLI when its scene.rml is newer.
const rivs = {
  "/chapter-2.riv": path.join(repo, "chapters", "ch2"),
  "/start-chapter-1.riv": path.join(repo, "chapters", "ch1"),
  "/chapters-3-4-end.riv": path.join(repo, "chapters", "ch3"),
};
// the review page: the whole experience across all three files (/experience wraps /experience-stage in a screen-size frame).
// It is the only review page; the per-file pages were retired.
const pages = { "/experience": "experience.html", "/experience-stage": "experience-stage.html" };

// the page's own relative URLs, mapped to where the files live in this repo
const files = {
  "/chapter-2-integration.js": path.join(repo, "engineering", "chapter-2-integration.js"),
  "/yig-text-motion.css": path.join(repo, "engineering", "yig-text-motion.css"),
  "/review.js": path.join(here, "review.js"),
  "/yig-integration.js": path.join(repo, "engineering", "yig-integration.js"),
  "/yig-framing.css": path.join(here, "yig-framing.css"),
  "/finesse-clock.js": path.join(here, "finesse-clock.js"),   // the Finesse panel's clock; added to the stage page only with ?finesse=1
  "/finesse-pins.js": path.join(here, "finesse-pins.js"),     // the pin comments' stage side; the same
};
const fontsRoot = path.join(here, "fonts");
const artRoot = path.join(repo, "art", "global");   // the game icons and the desktop arrow

const types = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml",
  ".png": "image/png", ".woff2": "font/woff2", ".riv": "application/octet-stream",
};

function newestBuild(project = projectDir) {
  const dir = path.join(project, "build");
  if (!fs.existsSync(dir)) return null;
  const builds = fs.readdirSync(dir).filter((f) => f.endsWith(".riv")).map((f) => path.join(dir, f));
  builds.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  return builds[0] || null;
}

const building = new Map();
function ensureBuilt(project = projectDir) {
  const scene = fs.statSync(path.join(project, "scene.rml")).mtimeMs;
  const built = newestBuild(project);
  if (built && fs.statSync(built).mtimeMs >= scene) return Promise.resolve({ built, rebuilt: false });
  if (!building.has(project)) {
    building.set(project, new Promise((resolve, reject) => {
      execFile(rive, [project, "--once"], (err, stdout, stderr) => {
        building.delete(project);
        if (err) return reject(new Error(`rive --once failed:\n${stdout}\n${stderr}`));
        resolve({ built: newestBuild(project), rebuilt: true });
      });
    }));
  }
  return building.get(project);
}

function sendFile(res, file) {
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404).end("not found"); return; }
    res.writeHead(200, { "content-type": types[path.extname(file)] || "application/octet-stream", "cache-control": "no-store" });
    res.end(data);
  });
}

// JSON the Finesse panel reads from the three scene.rml files, rerun only when one changes: each room's intro and loop lengths
// (tools/room_timing.py) and each file's named pieces, for the pins (tools/room_pieces.py)
const sceneCache = new Map();
function fromScenes(tool) {
  const key = Object.values(rivs).map((dir) => fs.statSync(path.join(dir, "scene.rml")).mtimeMs).join("-");
  if (sceneCache.get(tool)?.key === key) return Promise.resolve(sceneCache.get(tool).json);
  return new Promise((resolve, reject) => {
    execFile("python3", [path.join(repo, "tools", tool)], { maxBuffer: 16 << 20 }, (err, stdout, stderr) => {
      if (err) return reject(new Error(`${tool} failed:\n${stderr}`));
      sceneCache.set(tool, { key, json: stdout });
      resolve(stdout);
    });
  });
}

// ---- "Send to Claude" on the Finesse panel: the pins go into one notes file per chapter, .cache/scratch.nosync/finesse-notes/ch<N>.md
// (a new section per send, appended), with a JSON block of the exact values, and each pin's still next to it as
// ch<N>-<sent>-pin-<n>.png. The notes keep the numbers the pins had in the panel when sent, so each send starts again at 1;
// the send's time in the still's name keeps one send's stills from replacing another's.
// A test may name its own folder (finesse-notes-<something>), so it never writes into Demetre's notes.
const NOTES_HEAD = (ch) => `# Finesse notes · ${ch} (File ${ch.slice(2)})

Pins Demetre dropped on the stage in /experience (the Finesse panel's Comment mode), one section per send, the newest last.
A pin's moment is the Finesse panel's timecode: seconds since the scene was set. Positions are artboard units (1495 × 1067;
the floor line is y 712). "Under the pin" comes from the build: each named piece hidden in turn, and the ones whose hiding
changes the pixels at the pin (near: within 40 units, with the distance, the closest five here). Each still is the animation only (no HTML copy),
one pixel per artboard unit, with the pin drawn as a ring and the window's crop as a dashed box. Each send's notes are
numbered as the pins were in the panel when it was sent, from 1.
When a note is done, its Status line becomes "Status: done: <one-line reply>".
`;
const two = (v) => String(v).padStart(2, "0");
const stamp = (d) => `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())} ${two(d.getHours())}:${two(d.getMinutes())}`;
function noteMd(p, still) {
  const where = p.loop?.part === "intro" ? `, in the intro (${p.loop.at.toFixed(2)} s of ${p.loop.of.toFixed(2)} s)`
    : p.loop?.part === "loop" ? `, in the loop at ${p.loop.at.toFixed(2)} s of ${p.loop.of.toFixed(2)} s (pass ${p.loop.pass})` : "";
  const visit = p.firstVisit ? "first visit" : "a return visit (the room came back already built, so its loop kept its first-visit timing)";
  const piece = (v) => `${v.name}${v.in ? ` in ${v.in}` : ""}`;
  const pieces = !p.pieces ? "not worked out (a step-back frame, or no frame to test)"
    : (p.pieces.under.length ? p.pieces.under.map(piece).join(", ") : "no named piece")
      + (p.pieces.near.length ? ` · near: ${p.pieces.near.slice(0, 5).map((v) => `${piece(v)} (${v.d})`).join(", ")}${p.pieces.near.length > 5 ? ", … (all in the JSON)" : ""}` : "");
  const quote = (p.note || "(no note)").split("\n").map((l) => `> ${l}`).join("\n");
  // the room's own frame first, then the time since the scene was set in brackets (as pinWhen() in experience.html)
  const frames = p.loop ? Math.round(p.loop.of * 60) : 0;
  const when = p.loop ? `${p.loop.part === "intro" ? "Intro" : "Loop"} frame ${Math.round(p.loop.at * 60) % frames} of ${frames} (${p.loop.at.toFixed(2)} s) [${p.tc.toFixed(2)} s]` : `${p.tc.toFixed(2)} s`;
  return `### Note ${p.n} · ${p.room || p.scene} · ${when}
Status: open

${quote}

- Room: ${p.room || "(no room)"} (scene \`${p.scene}\`, File ${p.file}) · ${p.chapter} · card ${p.card.index} of ${p.card.of}${p.card.label ? ` (“${p.card.label}”)` : ""}
- Moment: ${p.tc.toFixed(2)} s after the scene was set (frame ${p.frame}), ${visit}${where}${p.historyFrame ? " (a step-back frame)" : ""}
- Where: x ${Math.round(p.x)}, y ${Math.round(p.y)}
- Under the pin: ${pieces}
- Still: ${still ? `[${still}](${still})` : "none"}
- Seen at: ${p.size}${p.riveOnly ? ", Rive only" : ", with the HTML"}; ${p.settings.flow === "anon" ? "anon" : `subscriber, ${p.settings.player}`}
`;
}
function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    const parts = [];
    let size = 0;
    req.on("data", (c) => { size += c.length; if (size > limit) { reject(new Error("too large")); req.destroy(); } else parts.push(c); });
    req.on("end", () => resolve(Buffer.concat(parts).toString("utf8")));
    req.on("error", reject);
  });
}
async function saveNotes(req, res) {
  const body = JSON.parse(await readBody(req, 512 << 20));
  const folder = body.folder || "finesse-notes";
  if (!/^finesse-notes(-[a-z0-9-]+)?$/.test(folder)) throw new Error(`bad folder ${folder}`);
  const pins = Array.isArray(body.pins) ? body.pins : [];
  for (const p of pins) {
    if (!/^ch[123]$/.test(p.notes) || !Number.isInteger(p.n) || p.n < 1) throw new Error(`bad pin ${JSON.stringify({ notes: p.notes, n: p.n })}`);
  }
  const dir = path.join(SCRATCH_ROOT, folder);
  fs.mkdirSync(dir, { recursive: true });
  const files = {};
  const now = new Date(), sent = stamp(now);
  const tag = `${now.getFullYear()}${two(now.getMonth() + 1)}${two(now.getDate())}-${two(now.getHours())}${two(now.getMinutes())}${two(now.getSeconds())}`;
  for (const ch of [...new Set(pins.map((p) => p.notes))].sort()) {
    const mine = pins.filter((p) => p.notes === ch).sort((a, b) => a.n - b.n);
    const values = [];
    let md = `\n## Sent ${sent}\n\n`;
    for (const p of mine) {
      const { still, ...rest } = p;
      let name = null;
      if (typeof still === "string" && still.startsWith("data:image/png;base64,")) {
        name = `${ch}-${tag}-pin-${p.n}.png`;
        fs.writeFileSync(path.join(dir, name), Buffer.from(still.slice("data:image/png;base64,".length), "base64"));
      }
      values.push({ ...rest, still: name });
      md += `${noteMd(p, name)}\n`;
    }
    md += `Exact values for this send:\n\n\`\`\`json\n${JSON.stringify(values, null, 1)}\n\`\`\`\n`;
    const file = path.join(dir, `${ch}.md`);
    if (!fs.existsSync(file)) fs.writeFileSync(file, NOTES_HEAD(ch));
    fs.appendFileSync(file, md);
    files[ch] = { notes: path.relative(repo, file), count: mine.length, stills: values.map((v) => v.still).filter(Boolean) };
  }
  res.writeHead(200, { "content-type": "application/json", "cache-control": "no-store" });
  res.end(JSON.stringify({ saved: pins.map((p) => p.n), files }));
}

function sendPage(res, name = "index.html", finesse = false) {
  fs.readFile(path.join(here, name), "utf8", (err, html) => {
    if (err) { res.writeHead(500).end(String(err.message)); return; }
    res.writeHead(200, { "content-type": types[".html"], "cache-control": "no-store" });
    // review.js (hash jump, Replay) is ours alone: it is injected here and is not in index.html, so it never ships
    const withFonts = html.replace("</head>", '<link rel="stylesheet" href="/fonts/fonts.css">\n</head>');
    // the Finesse clock goes in before the Rive runtime, and only when the panel asked for it (?finesse=1)
    // and the pins' stage side right after the runtime, before the import map hands the runtime to the integration
    const stage = finesse && name === "experience-stage.html"
      ? withFonts.replace("<head>", '<head>\n<script src="/finesse-clock.js"></script>')
        .replace('<script type="importmap">', '<script src="/finesse-pins.js"></script>\n<script type="importmap">')
      : withFonts;
    res.end(name === "index.html" ? withFonts.replace("</body>", '<script type="module" src="/review.js"></script>\n</body>') : stage);
  });
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const p = decodeURIComponent(url.pathname);
  try {
    if (p === "/" || p === "/index.html") return sendPage(res);
    if (p in pages) return sendPage(res, pages[p], url.searchParams.get("finesse") === "1");
    if (p === "/room-timing" || p === "/room-pieces") {
      res.writeHead(200, { "content-type": "application/json", "cache-control": "no-store" });
      return res.end(await fromScenes(p === "/room-timing" ? "room_timing.py" : "room_pieces.py"));
    }
    if (p === "/finesse-notes" && req.method === "POST") return await saveNotes(req, res);
    if (p in files) return sendFile(res, files[p]);
    if (p === "/builds") {   // when each file was last built, so /experience can reload itself on a newer build
      const out = {};
      for (const [name, dir] of Object.entries(rivs)) {
        const { built } = await ensureBuilt(dir);
        out[name] = `${fs.statSync(built).mtimeMs}-${fs.statSync(built).size}`;
      }
      res.writeHead(200, { "content-type": "application/json", "cache-control": "no-store" });
      return res.end(JSON.stringify(out));
    }
    if (p in rivs) {
      const { built } = await ensureBuilt(rivs[p]);
      return sendFile(res, built);
    }
    if (p.startsWith("/fonts/")) {
      const file = path.resolve(fontsRoot, p.slice("/fonts/".length));
      if (file.startsWith(fontsRoot + path.sep)) return sendFile(res, file); // no path traversal
    }
    if (p.startsWith("/assets/") && p.endsWith(".svg")) {   // the review pages' own art (the Figma logo)
      const root = path.join(here, "assets"), file = path.resolve(root, p.slice("/assets/".length));
      if (file.startsWith(root + path.sep)) return sendFile(res, file); // no path traversal
    }
    if (p.startsWith("/art/global/") && p.endsWith(".svg")) {
      const file = path.resolve(artRoot, p.slice("/art/global/".length));
      if (file.startsWith(artRoot + path.sep)) return sendFile(res, file); // no path traversal
    }
    res.writeHead(404).end("not found");
  } catch (e) {
    res.writeHead(500, { "content-type": "text/plain" }).end(String(e.message || e));
  }
}).listen(port, "127.0.0.1", () => {
  console.log(`harness for ${chapter}: http://127.0.0.1:${port}/`);
});
