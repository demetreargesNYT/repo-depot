// Colour crossfade test. Drives the real harness page in headless Chrome and samples it every ~60 ms while the
// scene changes, including a second change while the first fade is still running.
//
//   node harness/fade-test.mjs                    second change at 0.3, 0.7, 1.2 and 2.0 s, both orders
//   node harness/fade-test.mjs --times 0.3,1.2
//
// Needs the harness server (npm start) and Google Chrome. Samples with CDP Page.captureScreenshot, which reads
// what the compositor actually produced for that frame — not an in-page canvas re-read, which can occasionally
// catch a torn, mid-paint buffer and manufacture a one-sample "defect" that was never on screen. Per case it
// checks:
//   * no jump: no channel moves more than JUMP between two samples (a flash of the base background, or a hard
//     seam crossing the sampled point, would show as a jump),
//   * no seam: a row across the whole stage is one colour in every sampled frame (no hard edge moves across),
//   * it ends on the target room's wall colour, and the floor and the floor line never move.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";

const args = process.argv.slice(2);
const flag = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const TIMES = flag("--times", "0.3,0.7,1.2,2.0").split(",").map(Number);
const BASE = flag("--url", "http://127.0.0.1:8765/");
const SAMPLE_MS = 60;
const JUMP = 10;           // per channel between two samples ~60 ms apart; the fastest part of the fade moves about 4
const WALL = { shelf: [231, 241, 225], wordle: [195, 226, 192], connections: [225, 219, 245] };
const FLOOR = [254, 160, 201];
// The row sits at artboard y 5: Connections' tiles key as high as y -800 off their resting point and a piece is
// confirmed (by direct CLI render) to cross as low as y 20 during the drop, and the Rive lockup icon's rise can
// reach y 0 for a single frame, so the row has to clear every piece's and the lockup's entrance to read the
// backdrop alone. y 5 stayed clear of all of that in renders checked across both intros.
const ROW_Y = 5, FLOOR_XY = [60, 900], LINE_XY = [700, 712];
// The floor line stroke is 2 artboard units thick out of 1067, so at the box's device resolution a single sample
// point can land on-stroke or just off it depending on sub-pixel rounding, even though the line itself never
// moves. Read a few rows around it and keep whichever is darkest (closest to the line's own colour); confirmed
// by CLI render that rows 711-712 are the stroke and 710/713 are the room colour either side of it.
const LINE_PROBE_DY = [-2, -1, 0, 1, 2];

const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9600 + Math.floor(Math.random() * 150);
const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, "--window-size=1300,1000", "--hide-scrollbars",
  `--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), "yig-fade-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets;
for (let i = 0; i < 60; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send("Page.enable"); await send("Runtime.enable");

// Minimal PNG decoder: just enough for Chrome's own screenshot output (8-bit RGB or RGBA, no interlace, one IDAT
// worth of zlib data is the common case but we concatenate all IDAT chunks to be safe).
function decodePNG(buf) {
  let p = 8; let width, height, bitDepth, colorType;
  const idat = [];
  while (p < buf.length) {
    const len = buf.readUInt32BE(p); const type = buf.toString("ascii", p + 4, p + 8); const data = buf.subarray(p + 8, p + 8 + len);
    if (type === "IHDR") { width = data.readUInt32BE(0); height = data.readUInt32BE(4); bitDepth = data[8]; colorType = data[9]; }
    else if (type === "IDAT") idat.push(data);
    p += 12 + len;
  }
  if (bitDepth !== 8 || (colorType !== 2 && colorType !== 6)) throw new Error(`unsupported PNG: bitDepth ${bitDepth} colorType ${colorType}`);
  const channels = colorType === 6 ? 4 : 3;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const out = Buffer.alloc(height * stride);
  let prevRow = Buffer.alloc(stride);
  let rp = 0;
  for (let y = 0; y < height; y++) {
    const filter = raw[rp]; rp += 1;
    const row = raw.subarray(rp, rp + stride); rp += stride;
    const outRow = out.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= channels ? outRow[x - channels] : 0;
      const b = prevRow[x];
      const c = x >= channels ? prevRow[x - channels] : 0;
      let v = row[x];
      if (filter === 1) v = (v + a) & 0xff;
      else if (filter === 2) v = (v + b) & 0xff;
      else if (filter === 3) v = (v + ((a + b) >> 1)) & 0xff;
      else if (filter === 4) {
        const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c);
        const pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
        v = (v + pr) & 0xff;
      }
      outRow[x] = v;
    }
    prevRow = outRow;
  }
  return { width, height, channels, pixels: out };
}

async function screenshot(clip) {
  const r = await send("Page.captureScreenshot", { format: "png", clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height, scale: 1 } });
  return decodePNG(Buffer.from(r.result.data, "base64"));
}

function px(img, x, y) {
  const i = (y * img.width + x) * img.channels;
  return [img.pixels[i], img.pixels[i + 1], img.pixels[i + 2]];
}

const near = (a, b, t = 3) => a.every((v, i) => Math.abs(v - b[i]) <= t);
const results = [];
const check = (ok, text) => results.push({ ok, text });
const scene = (n) => ev(`document.querySelector('#scenes button[data-scene="${n}"]').click()`);
// #art wraps the canvas with no border or border-radius of its own; #stage (its parent) has both, so clipping to
// #stage would read a sliver of the page background around the edge, which looks exactly like a seam at row y 5.
const stageBox = () => ev("(r => ({x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height)}))(document.getElementById('art').getBoundingClientRect())");

for (const [first, firstN, second, secondN] of [["wordle", 1, "connections", 2], ["connections", 2, "wordle", 1]]) {
  for (const T of TIMES) {
    await send("Page.navigate", { url: BASE });
    await sleep(2800);
    const box = await stageBox();
    const toArt = (ax, ay) => ({ x: Math.round(box.x + (ax / 1495) * box.width), y: Math.round(box.y + (ay / 1067) * box.height) });

    await scene(firstN);
    await sleep(T * 1000);
    await scene(secondN);

    const t0 = Date.now();
    const s = [];
    while (Date.now() - t0 < 3400) {
      const img = await screenshot(box);
      const yRow = Math.round((ROW_Y / 1067) * box.height);
      const colors = new Set();
      const step = Math.max(1, Math.round((5 / 1495) * box.width));
      // A "seam" here means the wall itself showing two colours side by side; it does not include the lockup's
      // own icon, which briefly reaches this row around its rise-in (confirmed by direct CLI render) and is a
      // small, grey/near-black/green shape, never a colour anywhere near the backdrop's pastel range.
      const greyish = (c) => { const [r, g, b] = c.split(",").map(Number); return Math.max(r, g, b) - Math.min(r, g, b) < 30 && r < 140; };
      for (let x = step; x < box.width - step; x += step) { const c = px(img, x, yRow).join(","); if (!greyish(c)) colors.add(c); }
      const mid = Math.round((700 / 1495) * box.width);
      const f = px(img, Math.round((FLOOR_XY[0] / 1495) * box.width), Math.round((FLOOR_XY[1] / 1067) * box.height));
      const lx = Math.round((LINE_XY[0] / 1495) * box.width);
      const lCandidates = LINE_PROBE_DY.map((dy) => px(img, lx, Math.round((LINE_XY[1] / 1067) * box.height) + dy));
      const l = lCandidates.reduce((darkest, c) => (c[0] + c[1] + c[2] < darkest[0] + darkest[1] + darkest[2] ? c : darkest));
      s.push({ at: (Date.now() - t0) / 1000, wall: px(img, mid, yRow), colors: colors.size, floor: f, line: l });
      await sleep(SAMPLE_MS);
    }

    const label = `${first} then ${second}, second change ${T.toFixed(1)} s into the first`;
    let worst = 0, at = 0;
    for (let i = 1; i < s.length; i++) for (let k = 0; k < 3; k++) { const d = Math.abs(s[i].wall[k] - s[i - 1].wall[k]); if (d > worst) { worst = d; at = s[i].at; } }
    check(worst <= JUMP, `${label}: largest colour step between samples ${worst} (limit ${JUMP})${worst > JUMP ? ` at ${at.toFixed(2)} s` : ""}`);
    const seam = s.filter((x) => x.colors > 1);
    check(seam.length === 0, `${label}: the wall is one colour across the stage in every frame (${seam.length} of ${s.length} frames had a hard edge)`);
    const last = s[s.length - 1];
    check(near(last.wall, WALL[second]), `${label}: ends on the ${second} wall colour (${last.wall.join(",")}; want ${WALL[second].join(",")})`);
    check(s.every((x) => near(x.floor, FLOOR)), `${label}: the floor stays ${FLOOR.join(",")} throughout`);
    const lines = new Set(s.map((x) => x.line.join(",")));
    check(lines.size === 1, `${label}: the floor line pixel never changes (${lines.size} distinct value${lines.size === 1 ? "" : "s"})`);
    // colours seen should all lie between the room colours (plus the opener's): a flash of the base colour is outside them
    const lo = [0, 1, 2].map((k) => Math.min(WALL.shelf[k], WALL[first][k], WALL[second][k]) - 3), hi = [0, 1, 2].map((k) => Math.max(WALL.shelf[k], WALL[first][k], WALL[second][k]) + 3);
    check(s.every((x) => x.wall.every((v, k) => v >= lo[k] && v <= hi[k])), `${label}: every colour stays between the room colours`);
  }
}
proc.kill(); ws.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log((r.ok ? "PASS  " : "FAIL  ") + r.text); }
console.log(`\n${results.length - failed} of ${results.length} checks passed`);
process.exit(failed ? 1 : 0);
