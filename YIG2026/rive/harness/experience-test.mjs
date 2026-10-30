// Browser test for the full-experience stage (experience-stage.html), in headless Chrome with the real Rive runtime
// (engineering's, 2.27.3).
//
//   node harness/experience-test.mjs                       both flows, at phone and desktop sizes
//
// Needs the harness server (npm start) and Chrome. Checks, per flow: Next through every card and Back to Start, and
// after each tap the file on screen, its scene and the copy are that card's; Back across both file boundaries lands
// in the earlier file; each .riv is fetched once (earlier files stay loaded, later ones load ahead); a Back during a
// pan waits for it; the tap on a subscriber's last Chapter 2 card plays both moves (out to the empty Chapter 3 room,
// then Chapter 3's room) and Back plays them in reverse; at desktop width the arrows show and work and the tap zones are hidden, at phone width the
// reverse; no console errors.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const BASE = flag("--url", "http://127.0.0.1:8765");
const INTRO = 3.2, PAN = 1.65;
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
const check = (ok, text) => { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${text}`); };

async function browser(width, height) {
  const port = 9650 + Math.floor(Math.random() * 140);
  const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, `--window-size=${width},${height}`, "--hide-scrollbars",
    `--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), "yig-exp-"))}`, "about:blank"], { stdio: "ignore" });
  let targets;
  for (let i = 0; i < 60; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (targets.length) break; } catch {} await sleep(200); }
  const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pending = new Map(); const errors = []; const rivs = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
    if (d.method === "Runtime.exceptionThrown") errors.push(d.params.exceptionDetails.text + " " + (d.params.exceptionDetails.exception?.description ?? ""));
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") errors.push(d.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
    if (d.method === "Network.requestWillBeSent" && d.params.request.url.endsWith(".riv")) rivs.push(d.params.request.url.split("/").pop());
  };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
  await send("Runtime.enable"); await send("Network.enable"); await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  return { ev, errors, rivs, close: () => { ws.close(); proc.kill(); }, nav: (url) => send("Page.navigate", { url }) };
}

const shownCopy = "[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.dataset.copyFrame).join(',')";

for (const flow of ["sub", "anon"]) {
  for (const [w, h, label] of [[430, 932, "phone"], [1440, 900, "desktop"]]) {
    const b = await browser(w, h);
    await b.nav(`${BASE}/experience-stage?flow=${flow}&player=wordle-only`);
    for (let i = 0; i < 150 && !(await b.ev("!!window.yigExperience")); i++) await sleep(100);
    const cards = await b.ev("window.yigExperience.cards.map((c) => ({ file: c.file, scene: c.scene }))");
    const st = () => b.ev("window.yigExperience.state()");
    const tag = `${flow} · ${label} ${w}x${h}`;
    // Loading hands over to Start by itself once File 1 is in
    for (let i = 0; i < 80 && (await st()).frame === 0; i++) await sleep(100);
    await sleep(INTRO * 1000 + 500);
    let s = await st();
    check(s.frame === 1 && s.scenes[0] === "start", `${tag}: Loading hands over to Start (card ${s.frame}, scene ${s.scenes[0]})`);

    const arrows = await b.ev(`(() => { const v = (id) => getComputedStyle(document.getElementById(id)).display !== 'none'; return { arrow: v('arrow-next'), tap: v('tap-next') }; })()`);
    if (label === "desktop") check(arrows.arrow && !arrows.tap, `${tag}: the arrows show and the tap zones don't (arrows ${arrows.arrow}, tap zones ${arrows.tap})`);
    else check(!arrows.arrow && arrows.tap, `${tag}: the tap zones show and the arrows don't (arrows ${arrows.arrow}, tap zones ${arrows.tap})`);
    const next = label === "desktop" ? "arrow-next" : "tap-next";
    const back = label === "desktop" ? "arrow-back" : "tap-back";

    const bad = [];
    // crossing files from a card that isn't on the empty room (the subscriber's last Chapter 2 card, and Back to it)
    // plays two moves, one after the other
    const ENDS = { 1: "ad", 2: "to-chapter-3" };
    const settle = (i, from, forward) => {
      const moved = cards[i].file !== cards[from].file || cards[i].scene !== cards[from].scene;
      const edge = forward ? cards[from] : cards[i];
      const extra = cards[i].file !== cards[from].file && edge.scene !== ENDS[edge.file] ? PAN : 0;
      return !moved ? 900 : forward ? (INTRO + extra + 0.6) * 1000 : (PAN + extra + 0.7) * 1000;
    };
    const verify = async (i, how) => {
      const x = await st();
      const copy = await b.ev(shownCopy);
      if (x.frame !== i || x.shown !== cards[i].file || x.scenes[cards[i].file - 1] !== cards[i].scene || copy !== String(i)) {
        bad.push(`${how} to ${i} (${cards[i].file}:${cards[i].scene}): card ${x.frame}, file ${x.shown}, scene ${x.scenes[x.shown - 1]}, copy ${copy || "none"}`);
      }
    };
    for (let i = 2; i < cards.length; i++) {
      await b.ev(`document.getElementById('${next}').click()`);
      await sleep(settle(i, i - 1, true));
      await verify(i, "Next");
    }
    check(!bad.length, `${tag}: Next through all ${cards.length} cards: the right file, scene and copy each time${bad.length ? ": " + bad.slice(0, 3).join(" / ") : ""}`);
    check(JSON.stringify([...b.rivs].sort()) === JSON.stringify(["chapter-2.riv", "chapters-3-4-end.riv", "start-chapter-1.riv"]),
      `${tag}: each .riv was fetched once, the next ones ahead of time (${b.rivs.join(", ")})`);
    bad.length = 0;
    for (let i = cards.length - 2; i >= 1; i--) {
      await b.ev(`document.getElementById('${back}').click()`);
      await sleep(settle(i, i + 1, false));
      await verify(i, "Back");
    }
    check(!bad.length, `${tag}: Back all the way to Start, across both file boundaries: the right file, scene and copy each time${bad.length ? ": " + bad.slice(0, 3).join(" / ") : ""}`);
    check(b.rivs.length === 3, `${tag}: Back across files reloaded nothing (${b.rivs.length} .riv requests)`);
    await b.ev(`document.getElementById('${back}').click()`);
    await sleep(600);
    s = await st();
    check(s.frame === 1, `${tag}: Back on Start does nothing; Loading never comes back (card ${s.frame})`);

    // a Back during the Next pan into File 2 waits for the pan, then lands back in File 1
    const firstOf2 = cards.findIndex((c) => c.file === 2);
    for (let i = 2; i < firstOf2; i++) { await b.ev(`document.getElementById('${next}').click()`); await sleep(120); }
    await sleep((INTRO + 0.6) * 1000);
    await b.ev(`document.getElementById('${next}').click()`);
    await sleep(500);
    await b.ev(`document.getElementById('${back}').click()`);
    await sleep(200);
    const mid = await st();
    await sleep((PAN + PAN + 0.8) * 1000);
    const end = await st();
    check(mid.frame === firstOf2 && end.frame === firstOf2 - 1 && end.shown === 1,
      `${tag}: a Back 0.5 s into the pan into File 2 waits (card ${mid.frame}), then lands on File 1's last card (card ${end.frame}, file ${end.shown})`);
    check(b.errors.length === 0, `${tag}: no console errors${b.errors.length ? ": " + b.errors.slice(0, 2).join(" / ") : ""}`);
    b.close();
  }
}
console.log(`\n${results.filter(Boolean).length} of ${results.length} checks passed`);
process.exit(results.every(Boolean) ? 0 : 1);
