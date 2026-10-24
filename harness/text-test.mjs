// Text timing test. Drives the real harness page in headless Chrome, running engineering's own integration file,
// and measures when text and icons appear and leave after taps, including taps that land while an intro runs.
//
//   node harness/text-test.mjs                     times 0.5, 1.5, 2.5, 3.0 s, both game orders
//   node harness/text-test.mjs --times 0.5,3.0
//
// Needs the harness server (npm start) and Google Chrome. Checks, per case:
//   A  same-game tap T s into the game's intro: the old card goes at once, and the next card does not start
//      rising before the intro ends (3.2 s after the game's first tap), so it never overlaps the lockup.
//      After the intro it rises about 0.3 s after the tap.
//   B  tap to the next game: the old card and icon are gone or leaving at once, the new icon pops and the
//      new first card rises 3.2 s after the tap, with its lines one step (70 ms) after the icon.
//   C  the icon stays put on a game's later cards: no restart of its animation on a same-game tap.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const TIMES = flag("--times", "0.5,1.5,2.5,3.0").split(",").map(Number);
const BASE = flag("--url", "http://127.0.0.1:8765/");
const INTRO = 3.2, QUICK = 0.3, STEP = 0.07, TOL = 0.12;   // seconds; TOL covers the 40 ms sampling and page scheduling

const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9800 + Math.floor(Math.random() * 150);
const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, "--window-size=1300,1000", "--hide-scrollbars",
  `--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), "yig-text-"))}`, "about:blank"], { stdio: "ignore" });
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

// One in-page sampler: every 25 ms it records, for the visible card and icon, whether each is shown and when its
// first animation actually starts moving (currentTime past its delay). Times are seconds since the page called mark().
const INSTALL = `(() => {
  window.__t0 = performance.now(); window.__log = [];
  const now = () => (performance.now() - window.__t0) / 1000;
  window.__mark = (label) => window.__log.push({ at: now(), label });
  const moving = (el, sel) => { const n = el && el.querySelector(sel); const a = n && n.getAnimations()[0]; return a ? a.currentTime > a.effect.getComputedTiming().delay + 1 : false; };
  const shown = (el) => !!el && !el.hidden;
  let last = '';
  setInterval(() => {
    const card = [...document.querySelectorAll('.yig-text')].find((e) => !e.hidden);
    const icon = [...document.querySelectorAll('.yig-icon')].find((e) => !e.hidden);
    const popA = icon && icon.querySelector('.yig-pop') && icon.querySelector('.yig-pop').getAnimations()[0];
    const s = {
      at: now(),
      card: card ? card.dataset.copyScene + '#' + (card.dataset.copyCard || '-') : null,
      cardRising: moving(card, '.yig-line'),
      cardOut: !!card && card.classList.contains('yig-out'),
      icon: icon ? icon.dataset.iconScene : null,
      iconAnim: popA ? popA.animationName : null,
      iconPopping: moving(icon, '.yig-pop'),
      iconStart: popA ? popA.startTime : null,
    };
    const key = JSON.stringify([s.card, s.cardRising, s.cardOut, s.icon, s.iconAnim, s.iconPopping, s.iconStart]);
    if (key !== last) { window.__log.push(s); last = key; }
  }, 25);
})()`;

const results = [];
const check = (ok, text) => results.push({ ok, text });
const fmt = (v) => (v === undefined || v === null ? "never" : v.toFixed(2) + " s");

for (const order of ["wc", "cw"]) {
  const games = order === "wc" ? ["wordle", "connections"] : ["connections", "wordle"];
  const cardsIn = { wordle: 4, connections: 5 };
  for (const T of TIMES) {
    await send("Page.navigate", { url: BASE });
    await sleep(2600);
    await ev(`(s=>{s.value='${order}';s.dispatchEvent(new Event('change'))})(document.getElementById('order'))`);
    await sleep(2200);
    await ev(INSTALL);
    const tap = () => ev("window.__mark('tap'); document.getElementById('tap').click()");
    const wait = (s) => sleep(s * 1000);
    const at = (s) => ev("window.__t0 + " + s * 1000).then(() => s);
    const first = games[0], second = games[1];

    // tap 1 starts the first game; tap 2 (same game, next card) lands T s into its intro
    await tap(); await wait(T); await tap();
    await wait(INTRO + 1.5);
    const log = await ev("window.__log");
    const taps = log.filter((e) => e.label === "tap").map((e) => e.at);
    const rise2 = log.find((e) => e.card === first + "#2" && e.cardRising && e.at >= taps[1]);
    const gone1 = log.find((e) => e.at >= taps[1] && e.card !== first + "#1");
    const label = `${first} then ${second}, same-game tap ${T.toFixed(1)} s into the intro`;
    // A: the next card never starts rising before the intro has ended
    const startedAt = rise2 ? rise2.at - taps[0] : null;
    const expect = Math.max(INTRO, T + QUICK);
    check(startedAt !== null && startedAt >= INTRO - TOL, `A  ${label}: card 2 starts rising ${fmt(startedAt)} after the game's first tap (not before ${INTRO} s)`);
    check(startedAt !== null && Math.abs(startedAt - expect) <= TOL + 0.1, `A  ${label}: ...and no later than ${expect.toFixed(1)} s (it was ${fmt(startedAt)})`);
    check(!!gone1 && gone1.at - taps[1] <= 0.15, `A  ${label}: card 1 is gone within ${fmt(gone1 ? gone1.at - taps[1] : null)} of the tap`);

    // C: the icon's animation did not restart on the same-game tap
    const iconStarts = new Set(log.filter((e) => e.icon === first && e.iconStart !== null).map((e) => Math.round(e.iconStart)));
    check(iconStarts.size <= 1, `C  ${label}: the icon's animation started ${iconStarts.size} time(s) across cards 1 and 2 (want 1)`);

    // B: run through the rest of the game, then tap to the next game, and time it
    for (let i = 3; i <= cardsIn[first]; i++) { await wait(0.35); await tap(); }
    await wait(0.4);
    await ev("window.__log.length = 0");
    await tap();
    await wait(INTRO + 1.2);
    const log2 = await ev("window.__log");
    const t5 = log2.find((e) => e.label === "tap").at;
    const oldGone = log2.find((e) => e.at >= t5 && e.card !== first + "#" + cardsIn[first]);
    const iconPop = log2.find((e) => e.icon === second && e.iconPopping);
    const cardRise = log2.find((e) => e.card === second + "#1" && e.cardRising);
    const nl = `${first} to ${second}, tap after the last card (tapped ${T.toFixed(1)} s into the first intro)`;
    check(!!oldGone && oldGone.at - t5 <= 0.15, `B  ${nl}: old card gone within ${fmt(oldGone ? oldGone.at - t5 : null)}`);
    check(!!iconPop && Math.abs(iconPop.at - t5 - INTRO) <= TOL, `B  ${nl}: new icon pops ${fmt(iconPop ? iconPop.at - t5 : null)} after the tap (want ${INTRO} s)`);
    check(!!cardRise && Math.abs(cardRise.at - t5 - (INTRO + STEP)) <= TOL, `B  ${nl}: new first card rises ${fmt(cardRise ? cardRise.at - t5 : null)} after the tap (want ${(INTRO + STEP).toFixed(2)} s, one step after the icon)`);
    check(!!iconPop && !!cardRise && cardRise.at >= iconPop.at - 0.03, `B  ${nl}: the card does not rise before the icon pops`);
  }
}
proc.kill(); ws.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log((r.ok ? "PASS  " : "FAIL  ") + r.text); }
console.log(`\n${results.length - failed} of ${results.length} checks passed`);
process.exit(failed ? 1 : 0);
