// Smoke test for the per-file review page (file-review.html), in headless Chrome with the real Rive web runtime.
//
//   node harness/file-review-test.mjs [--url http://127.0.0.1:8765/file1]      needs the harness server (npm start) and Chrome
//   node harness/file-review-test.mjs --url http://127.0.0.1:8765/file3?top=connections
//
// Checks: the page loads without console errors; the file opens on its first card's scene; Next visits every card, with the
// scene the file reports after each tap; Back returns through every card to the first; a Back tapped during a pan waits for
// the pan and still lands; each card's copy shows once its room has settled. Timing of motion and feel is for Demetre to
// judge in the page.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const args = process.argv.slice(2);
const URL_ = args.includes("--url") ? args[args.indexOf("--url") + 1] : "http://127.0.0.1:8765/file1";
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9600 + Math.floor(Math.random() * 150);
const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, "--window-size=1300,1000", "--hide-scrollbars",
  `--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), "yig-f1-"))}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets;
for (let i = 0; i < 60; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const errors = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  if (d.method === "Runtime.exceptionThrown") errors.push(d.params.exceptionDetails.text + " " + (d.params.exceptionDetails.exception?.description ?? ""));
  if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") errors.push(d.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
};
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: URL_ });
let results = [];
const check = (ok, text) => { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${text}`); };

for (let i = 0; i < 150; i++) { await sleep(100); if (await ev("typeof vm !== 'undefined' && !!vm")) break; }
await sleep(800);
const scene = () => ev("vm.enum('scene').value");
const dir = () => ev("vm.enum('direction').value");
const shown = () => ev("[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.textContent.trim().slice(0, 28)).join('|')");
const SCENES = await ev("FLOW.map((f) => f.scene)");
const top = await ev("TOP");
if (top) check((await ev("vm.enum('topGame').value")) === top, `the file's topGame is the page's choice (${top})`);
check((await scene()) === SCENES[0], `the file opens on ${SCENES[0]} (${await scene()})`);

for (let i = 1; i < SCENES.length; i++) {
  const want = SCENES[i], moves = want !== SCENES[i - 1];
  await ev("document.getElementById('tap-next').click()");
  await sleep(300);
  check((await scene()) === want && (!moves || (await dir()) === "forward"), `Next: scene ${await scene()} (want ${want})${moves ? ", direction " + (await dir()) : ", the room stays"}`);
  await sleep(moves ? 3600 : 900);   // the pan and the intro are over, or the old copy has cleared
  check((await shown()) !== "", `its copy is on screen once the room has settled (${await shown()})`);
}
// Back all the way: each Back waits for the previous pan if one is running, so give each one the pan's time
for (let i = SCENES.length - 2; i >= 0; i--) {
  const want = SCENES[i], moves = want !== SCENES[i + 1];
  await ev("document.getElementById('tap-back').click()");
  await sleep(300);
  check((await scene()) === want && (!moves || (await dir()) === "back"), `Back: scene ${await scene()} (want ${want})${moves ? ", direction " + (await dir()) : ", the room stays"}`);
  await sleep(moves ? 2000 : 600);
}
// a Back during a Next pan waits for the pan to end, then lands
await ev("document.getElementById('tap-next').click()");
await sleep(500);
await ev("document.getElementById('tap-back').click()");
await sleep(200);
check((await scene()) === SCENES[1], `a Back 0.5 s into a pan has not turned the room around yet (scene ${await scene()})`);
await sleep(2200);
check((await scene()) === SCENES[0], `...and it lands once the pan is over (scene ${await scene()})`);
check(errors.length === 0, `no console errors${errors.length ? ": " + errors.slice(0, 3).join(" / ") : ""}`);
console.log(`\n${results.filter(Boolean).length} of ${results.length} checks passed`);
ws.close(); proc.kill();
process.exit(results.every(Boolean) ? 0 : 1);
