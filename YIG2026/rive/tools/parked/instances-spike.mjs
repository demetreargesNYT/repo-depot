// Spike for the one-integration plan: what do several live Rive instances cost, and what does a cold start at a
// chosen scene look like? Drives the real harness page in headless Chrome, so it uses the same runtime and .riv.
//
//   node tools/parked/instances-spike.mjs            needs the harness server (cd harness && npm start) and Google Chrome
//
// It reports, for 1 to 4 instances of chapter-2.riv alive at once (the page's own is the first; the others are
// paused and hidden, the way the integration would keep an earlier or later file):
//   * JS heap and WebAssembly memory after each is added, and after all are cleaned up;
//   * whether a paused instance keeps its scene while another plays, and plays on from it when resumed;
//   * a cold start: a new instance whose scene is set to "wordle" before it first plays. It shows what the first
//     frames look like (the wall is read from the canvas at 0.1 s and 2.5 s), which is why the plan keeps earlier
//     files alive instead of reloading them for Back.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const BASE = process.argv.includes("--url") ? process.argv[process.argv.indexOf("--url") + 1] : "http://127.0.0.1:8765/";
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9400 + Math.floor(Math.random() * 150);
// precise memory info makes performance.memory exact instead of bucketed
const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, "--window-size=1300,1000", "--enable-precise-memory-info",
  `--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), "yig-spike-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets;
for (let i = 0; i < 60; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails)); return r.result?.result?.value; };
await send("Page.enable"); await send("Runtime.enable"); await send("HeapProfiler.enable");
const mem = async () => { await send("HeapProfiler.collectGarbage"); return ev("window.__mem()"); };   // collect first, so garbage isn't counted
await send("Page.navigate", { url: BASE });
for (let i = 0; i < 150; i++) { await sleep(100); if (await ev("!!window.yigExample?.yig?.viewModelInstance")) break; }
await sleep(1500);

// helpers that run in the page
await ev(`(() => {
  window.__mem = async () => {
    await new Promise((r) => setTimeout(r, 300));
    const mod = await new Promise((r) => window.rive.RuntimeLoader.getInstance(r));
    const wasm = (mod.HEAPU8 ? mod.HEAPU8.length : (mod.wasmMemory || mod.asm?.memory)?.buffer.byteLength) || 0;
    return { jsHeapMB: +(performance.memory.usedJSHeapSize / 1048576).toFixed(2), wasmMB: +(wasm / 1048576).toFixed(2) };
  };
  window.__extra = [];
  window.__add = async (autoplay, scene) => {
    const buf = await (await fetch("/chapter-2.riv")).arrayBuffer();
    const canvas = document.createElement("canvas"); canvas.width = 1495; canvas.height = 1067;
    canvas.style.cssText = "position:absolute;left:0;top:0;width:200px;visibility:hidden";
    document.body.appendChild(canvas);
    const r = await new Promise((resolve, reject) => {
      const inst = new window.rive.Rive({ buffer: buf, canvas, stateMachines: "Backdrop", autoplay, autoBind: true,
        onLoad: () => { inst.resizeDrawingSurfaceToCanvas(); if (scene) inst.viewModelInstance.enum("scene").value = scene; resolve(inst); },
        onLoadError: reject });
    });
    window.__extra.push({ r, canvas });
    return window.__extra.length;
  };
  window.__wall = (canvas) => { const c = document.createElement("canvas"); c.width = 8; c.height = 8; const x = c.getContext("2d");
    x.drawImage(canvas, 40, 40, 8, 8, 0, 0, 8, 8); const p = x.getImageData(4, 4, 1, 1).data; return [p[0], p[1], p[2]]; };
})()`);

const rows = [];
rows.push({ live: 1, ...(await mem()) });
for (let n = 2; n <= 4; n++) { await ev("window.__add(false)"); rows.push({ live: n, ...(await mem()) }); }

// paused instances keep their scene while the page's own instance plays, and resume from it
await ev(`window.__extra[0].r.viewModelInstance.enum("direction").value = "forward"; window.__extra[0].r.viewModelInstance.enum("scene").value = "connections"; 0`);
const pausedScene = await ev(`window.__extra[0].r.viewModelInstance.enum("scene").value`);
await ev(`window.yigExample.onTap(); window.yigExample.onTap(); 0`); // the page's own instance moves on
await sleep(1500);
const stillPaused = await ev(`window.__extra[0].r.viewModelInstance.enum("scene").value`);

// cold start at a chosen scene: a new instance, scene set before it first plays
await ev(`window.__extra.forEach((e) => { e.r.cleanup(); e.canvas.remove(); }); window.__extra = []; 0`);
await ev(`window.__add(false, "wordle")`);
await ev(`window.__extra[0].r.play(); 0`);
await sleep(100);
const early = await ev(`window.__wall(window.__extra[0].canvas)`);
await sleep(2500);
const late = await ev(`window.__wall(window.__extra[0].canvas)`);
await ev(`window.__extra.forEach((e) => { e.r.cleanup(); e.canvas.remove(); }); window.__extra = []; 0`);
rows.push({ live: "1 (extras cleaned up; the page itself had played)", ...(await mem()) });

console.log("instances alive   JS heap (MB)   WebAssembly memory (MB)");
for (const r of rows) console.log(`${String(r.live).padEnd(17)} ${String(r.jsHeapMB).padEnd(14)} ${r.wasmMB}`);
console.log(`\npaused instance kept its scene while the page's own instance moved on: ${pausedScene} set, ${stillPaused} after 1.5 s (want ${pausedScene})`);
console.log(`cold start at "wordle" (scene set before the first play): wall RGB ${early} at 0.1 s, ${late} at 2.6 s; Wordle's wall is 195,226,192 and the default start is 241,236,192`);
ws.close(); proc.kill();
