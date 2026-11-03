// Tests the Finesse panel on /experience (needs the review server: npm start in harness/, and Google Chrome).
//
//   node harness/finesse-test.mjs
//
// Opens /experience with the panel on, jumps to Wordle (a first visit: 3.2 s intro, a 7.2 s loop), and checks:
//   - the stage runs on the Finesse clock, and the clock keeps real time at 1x and half of it at 0.5x
//   - Pause holds the clock still; one step forward moves it exactly one frame (1/60 s)
//   - Step back shows an older frame over the live one, and stepping forward again returns to the live frame
//   - the timecode starts at 0 when the scene is set, and the seam counter passes the intro end (3.2 s)
//   - Replay room starts the room's timecode again from 0
//   - with the panel off, the stage page has no Finesse clock at all
// Every check prints as it passes; a lost Chrome fails the run with a message (exit 2) instead of hanging it.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { chromeProfile } from "./scratch.mjs";   // Chrome's profile goes in .cache/scratch.nosync/, never /tmp

const args = process.argv.slice(2);
const flag = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const BASE = flag("--url", "http://127.0.0.1:8765");
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
const check = (ok, text) => { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${text}`); };

const port = 9650 + Math.floor(Math.random() * 140);
const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, "--window-size=1100,900", "--hide-scrollbars",
  `--user-data-dir=${chromeProfile("yig-fin-")}`, "about:blank"], { stdio: "ignore" });
let targets;
for (let i = 0; i < 60; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const errors = [];
const dead = (why) => { console.log(`FAIL  browser: ${why}`); try { proc.kill(); } catch {} process.exit(2); };
ws.onclose = () => dead("the connection to Chrome closed");
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  if (d.method === "Runtime.exceptionThrown") errors.push(d.params.exceptionDetails.text + " " + (d.params.exceptionDetails.exception?.description ?? ""));
  if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") errors.push(d.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
};
const send = (method, params = {}) => new Promise((r) => {
  const i = ++id;
  const timer = setTimeout(() => dead(`no answer to ${method} within 60 s`), 60000);
  pending.set(i, (d) => { clearTimeout(timer); r(d); });
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send("Runtime.enable"); await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1100, height: 900, deviceScaleFactor: 1, mobile: false });

const F = "document.getElementById('frame').contentWindow";       // the stage inside /experience
const clockTime = () => ev(`${F}.__yigClock?.time ?? null`);
const rate = async (ms) => { const a = await clockTime(); await sleep(ms); const b = await clockTime(); return (b - a) / ms; };
const waitFor = async (expr, ms = 30000) => { for (let t = 0; t < ms; t += 100) { if (await ev(expr)) return true; await sleep(100); } return false; };

// ---- the panel on
await send("Page.navigate", { url: `${BASE}/experience?finesse=1&size=375x812&flow=sub&player=wordle-only` });
check(await waitFor(`!!${F}?.yigExperience && !!${F}.__yigClock`, 40000), "Finesse on: the stage is running with the Finesse clock");
check(await ev("!document.getElementById('finesse').hidden && fin.on"), "the panel is showing");
check(await ev(`${F}.document.querySelectorAll('script[src="/finesse-clock.js"]').length === 1`), "the clock was added to the stage page once, before the Rive runtime");

// jump to Wordle: the final tap of the jump sets the scene, which restarts the timecode
await ev("load(0, '2:wordle')");
let setAt = 0;
for (let t = 0; t < 40000 && !setAt; t += 50) { if ((await ev("fin.key")) === "2:wordle") setAt = Date.now(); else await sleep(50); }
check(setAt > 0, "the jump reaches Wordle (File 2, scene wordle)");
await sleep(3500 - (Date.now() - setAt));
const tc = Number(await ev("document.getElementById('fin-time').textContent"));
check(Math.abs(tc - 3.5) <= 0.4, `the timecode started at 0 when the scene was set: ${tc.toFixed(1)} s about 3.5 s later`);
check((await ev("fin.first")) === true && (await ev("fin.passed")) >= 1, `the intro end (3.2 s) was passed as a seam (seams passed ${await ev("fin.passed")})`);
const room = await ev("document.getElementById('fin-list').textContent");
check(/Intro ends at 3\.2 s/.test(room) && /Loop restarts: 10\.4/.test(room), `the panel lists where the intro ends and the loop restarts (${room.slice(0, 80)}…)`);

// ---- the clock
const r1 = await rate(1000);
check(r1 > 0.9 && r1 < 1.1, `1x keeps real time (${r1.toFixed(2)} of real)`);
await ev("document.querySelector('[data-speed=\"0.5\"]').click()");
const rHalf = await rate(1000);
check(rHalf > 0.4 && rHalf < 0.6, `0.5x runs at half speed (${rHalf.toFixed(2)} of real)`);
await ev("document.querySelector('[data-speed=\"1\"]').click()");
await ev("document.getElementById('fin-play').click()");
await sleep(200);
const rPaused = await rate(700);
check(rPaused === 0, `Pause holds the clock still (${rPaused} of real)`);
const t0 = await clockTime();
await ev("document.getElementById('fin-fwd').click()");
await sleep(150);
const dStep = (await clockTime()) - t0;
check(Math.abs(dStep - 1000 / 60) < 0.01, `one step forward moves the clock exactly one frame (${dStep.toFixed(2)} ms)`);
for (let i = 0; i < 6; i++) { await ev("document.getElementById('fin-fwd').click()"); await sleep(60); }
const headTime = await clockTime();
for (let i = 0; i < 3; i++) { await ev("document.getElementById('fin-back').click()"); await sleep(60); }
const shown = await ev(`${F}.__yigClock.shownTime()`);
const ghost = await ev(`(() => { const g = ${F}.document.querySelector('canvas.yig-file[style*="z-index: 5"]'); return !!g && g.style.display === 'block'; })()`);
check(ghost && Math.abs(headTime - shown - 3 * (1000 / 60)) < 1, `three steps back show a frame three behind the live one (${(headTime - shown).toFixed(1)} ms behind) over the live canvas`);
check((await ev(`${F}.__yigClock.time`)) === headTime, "stepping back does not move the live clock");
for (let i = 0; i < 3; i++) { await ev("document.getElementById('fin-fwd').click()"); await sleep(60); }
const back = await ev(`(() => { const g = ${F}.document.querySelector('canvas.yig-file[style*="z-index: 5"]'); return !g || g.style.display === 'none'; })()`);
check(back && (await ev(`${F}.__yigClock.stepsBehind()`)) === 0, "stepping forward again returns to the live frame");
await ev("document.getElementById('fin-play').click()");
check((await rate(500)) > 0.8, "Play runs the clock again");

// ---- Replay room: reloads on the room's first card, so the timecode starts again from 0
await ev(`${F}.__oldPage = true`);                 // marks the stage that is on screen, so the reloaded one can be told apart
await ev("document.getElementById('fin-replay').click()");
let again = 0;
await waitFor(`!${F}?.__oldPage && !!${F}?.yigExperience`, 40000);
for (let t = 0; t < 40000 && !again; t += 50) { if ((await ev("fin.key")) === "2:wordle" && (await ev("fin.first"))) again = Date.now(); else await sleep(50); }
await sleep(1000);
const tcAgain = Number(await ev("document.getElementById('fin-time').textContent"));
check(again > 0 && tcAgain < 2.5, `Replay room starts the room again: the timecode is ${tcAgain.toFixed(1)} s a moment after the scene is set`);
check(errors.length === 0, `no console errors${errors.length ? ": " + errors.slice(0, 2).join(" / ") : ""}`);

// ---- the panel off: the stage is the engineering page, with no clock
await ev(`${F}.__oldPage = true`);
await ev("setFinesse(false)");
check(await waitFor(`!${F}?.__oldPage && !!${F}?.yigExperience`, 40000), "panel off: the stage reloads");
check((await ev(`${F}.__yigClock === undefined && ${F}.document.querySelectorAll('script[src="/finesse-clock.js"]').length === 0`)), "panel off: the stage page has no Finesse clock");
check(await ev("document.getElementById('finesse').hidden"), "panel off: the panel is hidden");

ws.onclose = null; proc.kill(); ws.close();
console.log(`\n${results.filter(Boolean).length} of ${results.length} checks passed`);
process.exit(results.every(Boolean) ? 0 : 1);
