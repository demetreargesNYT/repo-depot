// Text timing test. Drives the real harness page in headless Chrome, running engineering's own integration file,
// and measures when text and icons appear and leave after taps, including taps that land while an intro runs.
//
//   node harness/text-test.mjs                     times 0.5, 1.5, 2.5, 3.0 s, both game orders
//   node harness/text-test.mjs --times 0.5,3.0
//
// Needs the harness server (npm start) and Google Chrome. Checks, per case:
//   A  same-game tap T s into the game's intro: the old card goes at once, and the next card does not start
//      rising before the intro ends (3.2 s after the game's first tap), so it never overlaps the lockup.
//      After the intro it rises about 0.34 s (--yig-clear) after the tap.
//   B  tap to the next game: the old card and icon are gone or leaving at once, the new icon pops and the
//      new first card rises 3.2 s after the tap, with its lines one step (120 ms) after the icon.
//   C  the icon stays put on a game's later cards: no restart of its animation on a same-game tap.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const args = process.argv.slice(2);
const flag = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const TIMES = flag("--times", "0.5,1.5,2.5,3.0").split(",").map(Number);
const BASE = flag("--url", "http://127.0.0.1:8765/");
const INTRO = 3.2, QUICK = 0.34, STEP = 0.12, TOL = 0.12;   // seconds; TOL covers the 40 ms sampling and page scheduling

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
  // any line moving: on Next the first line moves first, on Back the last one does
  const moving = (el, sel) => !!el && [...el.querySelectorAll(sel)].some((n) => { const a = n.getAnimations()[0]; return a ? a.currentTime > a.effect.getComputedTiming().delay + 1 : false; });
  const shown = (el) => !!el && !el.hidden;
  let last = '';
  setInterval(() => {
    const card = [...document.querySelectorAll('.yig-text')].find((e) => !e.hidden);
    const icon = [...document.querySelectorAll('.yig-icon')].find((e) => !e.hidden);
    const popA = icon && icon.querySelector('.yig-pop') && icon.querySelector('.yig-pop').getAnimations()[0];
    const s = {
      at: now(),
      card: card ? card.dataset.copyScene + '#' + (card.dataset.copyCard || '-') : null,
      cardRising: moving(card, '.yig-line, .yig-text > .yig-pop'),
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
    const tap = () => ev("window.__mark('tap'); document.getElementById('next').click()");
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
// Back. One run per game order:
//   D  Back within a game (from card 2 to card 1): text only, reversed. The old card is gone or dropping at once,
//      card 1 comes back down 0.34 s after the tap, its lines bottom first, and the icon's animation is not restarted.
//   E  Back across a game boundary (second game card 1 to the first game's last card), from rest: the old card
//      and icon leave at once, and the first game's icon and last card arrive when the pan ends (1.65 s).
//   F  Back during that pan's Next: the Back waits for the pan to end, then plays; the text follows it.
//   G  Back on the opener does nothing.
const PAN = 1.65;
for (const order of ["wc", "cw"]) {
  const games = order === "wc" ? ["wordle", "connections"] : ["connections", "wordle"];
  const cardsIn = { wordle: 4, connections: 5 };
  const [first, second] = games;
  await send("Page.navigate", { url: BASE });
  await sleep(2600);
  await ev(`(s=>{s.value='${order}';s.dispatchEvent(new Event('change'))})(document.getElementById('order'))`);
  await sleep(2200);
  await ev(INSTALL);
  const press = (id) => ev(`window.__mark('${id}'); document.getElementById('${id}').click()`);
  const wait = (s) => sleep(s * 1000);
  const after = (log, label) => log.filter((e) => e.label === label).map((e) => e.at);

  // G: Back on the opener
  const atOpener = await ev("document.getElementById('back').disabled");
  await ev("window.__harness.state.mod.onBack()");
  await wait(0.4);
  const vmScene = await ev("window.__harness.state.mod.yig.viewModelInstance.number('scene').value");
  const openerShown = await ev("!document.querySelector('[data-copy-scene=\"opener\"]').hidden");
  check(atOpener && vmScene === 0 && openerShown, `G  ${first} first: Back on the opener does nothing (button disabled ${atOpener}, scene ${vmScene}, opener copy shown ${openerShown})`);

  // D: into the first game, on to card 2, then Back to card 1
  await press("next"); await wait(INTRO + 0.6);
  await press("next"); await wait(1.0);
  await ev("window.__log.length = 0");
  await press("back"); await wait(1.4);
  let log = await ev("window.__log");
  const tb = after(log, "back")[0];
  const gone2 = log.find((e) => e.at >= tb && e.card !== first + "#2");
  const back1 = log.find((e) => e.card === first + "#1" && e.cardRising);
  const iconStarts = new Set(log.filter((e) => e.icon === first && e.iconStart !== null).map((e) => Math.round(e.iconStart)));
  const order1 = await ev(`(() => { const el = document.querySelector('[data-copy-scene="${first}"][data-copy-card="1"]');
    const ls = [...el.querySelectorAll('.yig-line')].map((l) => getComputedStyle(l).animationName + '@' + parseFloat(getComputedStyle(l).animationDelay));
    return { back: el.classList.contains('yig-back'), lines: ls }; })()`);
  const delays = order1.lines.map((s) => Number(s.split("@")[1]));
  const label = `${first}: Back from card 2 to card 1`;
  check(!!gone2 && gone2.at - tb <= 0.15, `D  ${label}: card 2 is gone or dropping within ${fmt(gone2 ? gone2.at - tb : null)}`);
  check(!!back1 && Math.abs(back1.at - tb - QUICK) <= TOL, `D  ${label}: card 1 comes back ${fmt(back1 ? back1.at - tb : null)} after the tap (want ${QUICK} s)`);
  check(order1.back && order1.lines.every((s) => s.startsWith("yig-descend")), `D  ${label}: card 1's lines come down from above (${order1.lines.map((s) => s.split("@")[0]).join(", ")})`);
  check(delays.every((d, i) => i === 0 || d <= delays[i - 1]), `D  ${label}: bottom line first (delays ${delays.join(", ")} s)`);
  check(iconStarts.size <= 1, `D  ${label}: the icon's animation was not restarted (${iconStarts.size} start(s))`);

  // E: run to the second game, let it settle, then Back across the boundary from rest
  for (let i = 2; i <= cardsIn[first]; i++) { await press("next"); await wait(0.4); }
  await press("next"); await wait(INTRO + 0.8);
  await ev("window.__log.length = 0");
  await press("back"); await wait(PAN + 1.0);
  log = await ev("window.__log");
  const te = after(log, "back")[0];
  const goneE = log.find((e) => e.at >= te && e.card !== second + "#1" && e.icon !== second);
  const iconE = log.find((e) => e.icon === first && e.iconPopping);
  const cardE = log.find((e) => e.card === first + "#" + cardsIn[first] && e.cardRising);
  const lE = `${second} card 1 back to ${first} card ${cardsIn[first]}, from rest`;
  check(!!goneE && goneE.at - te <= 0.15, `E  ${lE}: the old card and icon are gone or leaving within ${fmt(goneE ? goneE.at - te : null)}`);
  check(!!iconE && Math.abs(iconE.at - te - PAN) <= TOL, `E  ${lE}: ${first}'s icon arrives ${fmt(iconE ? iconE.at - te : null)} after the tap (want ${PAN} s, the end of the pan)`);
  check(!!cardE && Math.abs(cardE.at - te - PAN - STEP) <= TOL, `E  ${lE}: its last card arrives ${fmt(cardE ? cardE.at - te : null)} after the tap (want ${(PAN + STEP).toFixed(2)} s)`);

  // F: Next back into the second game, then Back 0.5 s into that pan: it waits for the pan, then plays
  await press("next"); await wait(0.5);
  await ev("window.__log.length = 0");
  await press("back"); await wait(PAN + PAN + 0.6);
  log = await ev("window.__log");
  const tf = after(log, "back")[0];
  const vmF = await ev("window.__harness.state.mod.yig.viewModelInstance.number('scene').value");
  const cardF = log.find((e) => e.card === first + "#" + cardsIn[first] && e.cardRising);
  const wantF = (PAN - 0.5) + PAN + STEP;
  const lF = `Back 0.5 s into the Next pan to ${second}`;
  check(vmF === (first === "wordle" ? 1 : 2), `F  ${lF}: ends on ${first} (scene ${vmF})`);
  check(!!cardF && Math.abs(cardF.at - tf - wantF) <= TOL + 0.05, `F  ${lF}: waits for the pan, then ${first}'s last card arrives ${fmt(cardF ? cardF.at - tf : null)} after the tap (want ${wantF.toFixed(2)} s)`);
}

proc.kill(); ws.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log((r.ok ? "PASS  " : "FAIL  ") + r.text); }
console.log(`\n${results.length - failed} of ${results.length} checks passed`);
process.exit(failed ? 1 : 0);
