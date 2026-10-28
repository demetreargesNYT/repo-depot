// Text timing test. Drives the example page (index.html) in headless Chrome, running engineering's own integration
// file, and measures when text and icons appear and leave after taps, including taps that land while an intro runs.
// Each case loads the page with its own test player (window.__yigTestPlayer, injected before the page's script runs).
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
//   D-G Back, H community cards, I starting words, J and L a game that isn't built yet, K a full run-through,
//   M the first tap (empty Chapter 1 room to the opener), N the ending (last game to Chapter 3): see below.
//
// The card list is { game: "chapter1" } (the room the file opens on, no copy), the opener, the games, then
// { game: "chapter3" } (the empty Chapter 3 backdrop the file ends on). Cases that time a game's first visit
// first spend a tap on the opener (openerStep below), so they start where a player does.
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
let id = 0; const pending = new Map(); const warnings = [];
// J and L need a game that isn't built in the .riv yet. Every game is built now, so those cases ask for the
// integration file with "strands" taken out of its BUILT list: the page's request for it is answered here with the
// edited copy (the file on disk is not touched). It is the same code path engineering would hit for a new game.
let unbuilt = false;
async function answer(d) {
  const { requestId, request } = d.params;
  if (!unbuilt) return send("Fetch.continueRequest", { requestId });
  const src = await (await fetch(request.url)).text();
  const body = src.replace(/^const BUILT = new Set\(\[.*$/m, (line) => line.replace('"strands", ', ""));
  if (body === src) throw new Error("text-test: could not find strands in the BUILT list");
  return send("Fetch.fulfillRequest", { requestId, responseCode: 200, responseHeaders: [{ name: "content-type", value: "text/javascript" }, { name: "cache-control", value: "no-store" }], body: Buffer.from(body).toString("base64") });
}
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.method === "Fetch.requestPaused") answer(d);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  if (d.method === "Runtime.consoleAPICalled" && d.params.type === "warning") warnings.push(d.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
};
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send("Page.enable"); await send("Runtime.enable");
await send("Fetch.enable", { patterns: [{ urlPattern: "*chapter-2-integration.js*", requestStage: "Request" }] });

// The test player: both games with 10+ solves and every stat above 0, so each gets all its own cards
// (Wordle 4, Connections 5), and three starting words. Cases change a copy of it.
const basePlayer = (order) => ({
  gameOrder: order === "cw" ? ["connections", "wordle"] : ["wordle", "connections"],
  wordle: { solves: 212, averageGuesses: 3.9, bestGuesses: 2, bestGuessesCount: 14,
            topStartingWords: ["ADIEU", "BREAD", "MOUSE"], hardestWordResult: "missed" },
  connections: { solves: 140, solvingOrder: ["yellow", "green", "blue", "purple"], purpleFirstCount: 3,
                 solveRate: 86, averageMistakes: 1.4, perfectPuzzles: 2 },
});

// Load the page with this player (null: the page's own EXAMPLE_PLAYER), and wait until Rive has loaded and bound
// its view model, plus the settle time the old harness gave a fresh run.
let injected = null;
async function load(testPlayer) {
  if (injected) await send("Page.removeScriptToEvaluateOnNewDocument", { identifier: injected });
  injected = null;
  if (testPlayer) {
    const r = await send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__yigTestPlayer = ${JSON.stringify(testPlayer)};` });
    injected = r.result.identifier;
  }
  await send("Page.navigate", { url: BASE });
  for (let i = 0; i < 150; i++) {
    await sleep(100);
    if (await ev("!!window.yigExample?.yig?.viewModelInstance")) break;
  }
  await sleep(2200);
}
const cardsPerGame = async () => ev("window.yigExample.cards.reduce((n, c) => (n[c.game] = (n[c.game] || 0) + 1, n), {})");
const VM = "window.yigExample.yig.viewModelInstance";
// What engineering would do to add a card for a game that isn't built yet: a strands card at the end of the list
// and its hidden copy block, then start() again with the new list (start() copies the list it's given).
const ADD_STRANDS = `(() => { const cards = window.yigExample.cards;
  if (cards[cards.length - 1].game === 'chapter3') { cards.pop(); document.querySelector('[data-copy-frame="' + cards.length + '"]')?.remove(); }
  cards.push({ game: "strands", card: "test" });
  document.getElementById('overlay').insertAdjacentHTML('beforeend', '<div class="yig-text blk blk-stat" data-copy-frame="' + (cards.length - 1) +
    '" data-copy-game="strands" data-copy-card="1" hidden><span class="yig-mask"><span class="yig-line t-serif">Strands test card</span></span></div>');
  window.yigExample.start(cards); })()`;
const shownCopy = () => ev(`[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.dataset.copyGame + '#' + (e.dataset.copyCard || '-')).join(',')`);

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
      card: card ? card.dataset.copyGame + '#' + (card.dataset.copyCard || '-') : null,
      cardRising: moving(card, '.yig-line, .yig-text > .yig-pop'),
      cardOut: !!card && card.classList.contains('yig-out'),
      icon: icon ? icon.dataset.iconGame : null,
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
// The first tap: from the empty Chapter 1 room into the opener, waiting out its intro. Not marked in the log.
const openerStep = async () => { await ev("document.getElementById('tap-next').click()"); await sleep((INTRO + 0.6) * 1000); };
const fmt = (v) => (v === undefined || v === null ? "never" : v.toFixed(2) + " s");

for (const order of ["wc", "cw"]) {
  const games = order === "wc" ? ["wordle", "connections"] : ["connections", "wordle"];
  for (const T of TIMES) {
    await load(basePlayer(order));
    const cardsIn = await cardsPerGame();
    await ev(INSTALL);
    const tap = () => ev("window.__mark('tap'); document.getElementById('tap-next').click()");
    const wait = (s) => sleep(s * 1000);
    const at = (s) => ev("window.__t0 + " + s * 1000).then(() => s);
    const first = games[0], second = games[1];

    // the opener first; then tap 1 starts the first game and tap 2 (same game, next card) lands T s into its intro
    await openerStep();
    await ev("window.__log.length = 0");
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
//   G  Back on the first card (the empty Chapter 1 room) does nothing: the scene stays from-chapter-1 and no copy shows.
//   G2 Back from the opener returns to it: scene from-chapter-1, no copy, and Next brings the opener (already built) back.
const PAN = 1.65;
for (const order of ["wc", "cw"]) {
  const games = order === "wc" ? ["wordle", "connections"] : ["connections", "wordle"];
  const [first, second] = games;
  await load(basePlayer(order));
  const cardsIn = await cardsPerGame();
  await ev(INSTALL);
  const press = (id) => ev(`window.__mark('${id}'); document.getElementById('tap-${id}').click()`);
  const wait = (s) => sleep(s * 1000);
  const after = (log, label) => log.filter((e) => e.label === label).map((e) => e.at);

  // G: Back on the first card, the empty Chapter 1 room
  await press("back");
  await wait(0.6);
  const vmScene = await ev(`${VM}.enum('scene').value`);
  const noCopy = (await shownCopy()) === "";
  check(vmScene === "from-chapter-1" && noCopy, `G  ${first} first: Back on the empty Chapter 1 room does nothing (scene ${vmScene}, copy shown ${noCopy ? "none" : "some"})`);

  // M: the first tap, empty Chapter 1 room to the opener: its copy rises 3.2 s later (the intro), like a game's first card
  await ev("window.__log.length = 0");
  await press("next");
  await wait(INTRO + 0.8);
  let logM = await ev("window.__log");
  const tm = after(logM, "next")[0];
  const riseM = logM.find((e) => e.card === "opener#-" && e.cardRising);
  const sceneM = await ev(`${VM}.enum('scene').value`);
  check(sceneM === "intro" && !!riseM && Math.abs(riseM.at - tm - INTRO) <= TOL, `M  ${first} first: the first tap pans to the opener (scene ${sceneM}); its copy rises ${fmt(riseM ? riseM.at - tm : null)} after the tap (want ${INTRO} s, the intro)`);

  // G2: Back from the opener to the empty room, and Next again (no second intro: the copy comes back as the pan ends)
  await press("back"); await wait(PAN + 0.4);
  const sceneG2 = await ev(`${VM}.enum('scene').value`);
  const copyG2 = await shownCopy();
  await ev("window.__log.length = 0");
  await press("next"); await wait(PAN + 0.8);
  const logG2 = await ev("window.__log");
  const tg = after(logG2, "next")[0];
  const riseG2 = logG2.find((e) => e.card === "opener#-" && e.cardRising);
  check(sceneG2 === "from-chapter-1" && copyG2 === "", `G2 ${first} first: Back from the opener returns to the empty Chapter 1 room (scene ${sceneG2}, copy ${copyG2 || "none"})`);
  check(!!riseG2 && Math.abs(riseG2.at - tg - PAN) <= TOL, `G2 ${first} first: Next again brings the opener back, its copy rising ${fmt(riseG2 ? riseG2.at - tg : null)} after the tap (want ${PAN} s, the end of the pan)`);

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
  const order1 = await ev(`(() => { const el = document.querySelector('[data-copy-game="${first}"][data-copy-card="1"]');
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
  const vmF = await ev(`${VM}.enum('scene').value`);
  const cardF = log.find((e) => e.card === first + "#" + cardsIn[first] && e.cardRising);
  const wantF = (PAN - 0.5) + PAN + STEP;
  const lF = `Back 0.5 s into the Next pan to ${second}`;
  check(vmF === first, `F  ${lF}: ends on ${first} (scene ${vmF})`);
  check(!!cardF && Math.abs(cardF.at - tf - wantF) <= TOL + 0.05, `F  ${lF}: waits for the pan, then ${first}'s last card arrives ${fmt(cardF ? cardF.at - tf : null)} after the tap (want ${wantF.toFixed(2)} s)`);
}

// Community cards and the starting-words list:
//   H  a community card for the first game: the frame list has one card for it, community is set in the file,
//      the icon pops 3.2 s after the tap and the card's lines follow one step later, as on a game's first card.
//   I  the starting-words card: one line per word, singular label for one word, and left out when none repeated.
for (const order of ["wc", "cw"]) {
  const [first, second] = order === "wc" ? ["wordle", "connections"] : ["connections", "wordle"];
  const p = basePlayer(order);
  p[first].solves = 7; // fewer than 10: the first game gets its community card
  await load(p);
  await ev(INSTALL);
  await openerStep();
  await ev("window.__log.length = 0");
  const frames = await ev("window.yigExample.cards.map((f) => f.game + (f.community ? '*' : ''))");
  const ownSecond = frames.filter((f) => f === second).length;
  check(frames[0] === "chapter1" && frames[frames.length - 1] === "chapter3" && frames.filter((f) => f.startsWith(first)).length === 1 && frames[2] === first + "*" && ownSecond > 1,
        `H  ${first} community, ${second} own: the frames are ${frames.join(", ")}`);
  await ev("window.__mark('tap'); document.getElementById('tap-next').click()");
  await sleep(300);
  const flag = await ev(`${VM}.boolean('lockup').value`);
  await sleep((INTRO + 1.2) * 1000);
  const log = await ev("window.__log");
  const t0 = log.find((e) => e.label === "tap").at;
  const pop = log.find((e) => e.icon === first && e.iconPopping);
  const rise = log.find((e) => e.card === first + "#-" && e.cardRising);
  check(flag === false, `H  ${first} community card: the file's lockup is ${flag} after the tap (want false: a community card hides the lockup)`);
  check(!!pop && Math.abs(pop.at - t0 - INTRO) <= TOL, `H  ${first} community card: the icon pops ${fmt(pop ? pop.at - t0 : null)} after the tap (want ${INTRO} s)`);
  check(!!rise && Math.abs(rise.at - t0 - INTRO - STEP) <= TOL, `H  ${first} community card: its lines rise ${fmt(rise ? rise.at - t0 : null)} after the tap (want ${(INTRO + STEP).toFixed(2)} s)`);
  await ev("document.getElementById('tap-next').click()");
  await sleep(400);
  const flag2 = await ev(`${VM}.boolean('lockup').value`);
  check(flag2 === true, `H  then ${second}'s own cards: lockup is ${flag2} (want true)`);
}
const WORDS = ["ADIEU", "BREAD", "MOUSE"];
for (const n of [3, 2, 1, 0]) {
  const p = basePlayer("wc");
  p.wordle.topStartingWords = WORDS.slice(0, n);
  await load(p);
  const r = await ev(`(() => { const i = window.yigExample.cards.findIndex((f) => f.game === 'wordle' && f.card === 'starting-words');
    const c = i < 0 ? null : document.querySelector('[data-copy-frame="' + i + '"]');
    return { inFrames: i >= 0,
             words: c ? c.querySelectorAll(':scope > .yig-word').length : 0,
             text: c ? [...c.querySelectorAll(':scope > .yig-word')].map((w) => w.textContent).join(',') : '',
             label: c ? c.children[1].textContent : null,
             order: c ? [...c.children].map((e) => getComputedStyle(e).getPropertyValue('--yig-n').trim()).join(',') : '' }; })()`);
  if (n === 0) check(!r.inFrames, `I  no word repeated: the starting-words card is left out of the cards (in cards: ${r.inFrames})`);
  else check(r.inFrames && r.words === n && r.text === WORDS.slice(0, n).join(",") && r.label === (n === 1 ? "starting word was" : "starting words were") && r.order === [...Array(n + 3).keys()].join(","),
             `I  ${n} starting word(s): ${r.words} word lines (${r.text}), label "${r.label}", stagger ${r.order}`);
}

// A game that isn't built in the .riv yet:
//   J  a card for it (strands, after the last Connections card): Rive stays on the room on screen (scene unchanged),
//      the integration warns once, the old card and icon leave at once and the new copy arrives once the old has
//      cleared (0.34 s). Back from it: the previous card and its icon come back the same way, and the scene still
//      hasn't changed.
{
  unbuilt = true;
  await load(basePlayer("wc"));
  const cardsIn = await cardsPerGame();
  await ev(ADD_STRANDS);
  await ev(INSTALL);
  const press = (id) => ev(`window.__mark('${id}'); document.getElementById('tap-${id}').click()`);
  const wait = (s) => sleep(s * 1000);
  await openerStep();
  await press("next"); await wait(INTRO + 0.6);
  for (let i = 2; i <= cardsIn.wordle; i++) { await press("next"); await wait(0.4); }
  await press("next"); await wait(INTRO + 0.6);
  for (let i = 2; i <= cardsIn.connections; i++) { await press("next"); await wait(0.4); }
  await wait(0.6);
  const sceneBefore = await ev(`${VM}.enum('scene').value`);
  const lastCard = "connections#" + cardsIn.connections;
  warnings.length = 0;
  await ev("window.__log.length = 0");
  await press("next");
  // straight after the tap: is everything that was on screen gone or leaving (yig-out)?
  const leavingJ = await ev(`[...document.querySelectorAll('.yig-text, .yig-icon')].filter((e) => !e.hidden && e.dataset.copyGame !== 'strands')
    .every((e) => e.classList.contains('yig-out'))`);
  await wait(1.4);
  let log = await ev("window.__log");
  const tj = log.find((e) => e.label === "next").at;
  const sceneJ = await ev(`${VM}.enum('scene').value`);
  const warned = warnings.filter((w) => w.includes("strands"));
  const goneJ = log.find((e) => !e.label && e.at >= tj && e.icon !== "connections" && e.card !== lastCard); // fully hidden
  const riseJ = log.find((e) => e.card === "strands#1" && e.cardRising);
  const shownJ = await ev(`[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.dataset.copyGame + '#' + (e.dataset.copyCard || '-')).join(',')`);
  const lJ = "strands card (not built) after Connections";
  check(sceneBefore === "connections" && sceneJ === "connections", `J  ${lJ}: Rive's scene stays on connections (${sceneBefore} before, ${sceneJ} after)`);
  check(warned.length === 1, `J  ${lJ}: one warning names strands (${warned.length}: ${warned[0] ?? "none"})`);
  check(leavingJ, `J  ${lJ}: the old card and icon are leaving at once (${leavingJ})`);
  check(!!goneJ && goneJ.at - tj <= QUICK + TOL, `J  ${lJ}: ...and gone ${fmt(goneJ ? goneJ.at - tj : null)} after the tap (want by ${QUICK} s)`);
  check(!!riseJ && Math.abs(riseJ.at - tj - QUICK) <= TOL, `J  ${lJ}: the strands copy rises ${fmt(riseJ ? riseJ.at - tj : null)} after the tap (want ${QUICK} s)`);
  check(shownJ === "strands#1", `J  ${lJ}: the copy on screen is ${shownJ || "none"} (want strands#1)`);

  await ev("window.__log.length = 0");
  await press("back"); await wait(1.4);
  log = await ev("window.__log");
  const tk = log.find((e) => e.label === "back").at;
  const sceneK = await ev(`${VM}.enum('scene').value`);
  const iconK = log.find((e) => e.icon === "connections" && e.iconPopping);
  const cardK = log.find((e) => e.card === lastCard && e.cardRising);
  const shownK = await ev(`[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.dataset.copyGame + '#' + (e.dataset.copyCard || '-')).join(',')`);
  const lK = "Back from the strands card";
  check(sceneK === "connections", `J  ${lK}: the scene is still connections (${sceneK})`);
  check(!!iconK && Math.abs(iconK.at - tk - QUICK) <= TOL, `J  ${lK}: the Connections icon comes back ${fmt(iconK ? iconK.at - tk : null)} after the tap (want ${QUICK} s)`);
  check(!!cardK && Math.abs(cardK.at - tk - QUICK - STEP) <= TOL, `J  ${lK}: ${lastCard} comes back ${fmt(cardK ? cardK.at - tk : null)} after the tap (want ${(QUICK + STEP).toFixed(2)} s)`);
  check(shownK === lastCard, `J  ${lK}: the copy on screen is ${shownK || "none"} (want ${lastCard})`);
}

//   L  a card for a game that isn't built yet, tapped T s into the room's first-visit intro (cards: opener, Wordle
//      community, strands). Rive stays on Wordle with community still on, the integration warns once, the Wordle
//      card and icon leave at once, and the strands copy waits for the intro: it starts rising no earlier than 3.2 s
//      after the first tap and no later than max(3.2, T + 0.34) s. Back: the Wordle card returns, scene still 1.
for (const T of [0.5, 1.5, 2.5]) {
  const p = basePlayer("wc");
  p.gameOrder = ["wordle"];
  p.wordle.solves = 7;
  unbuilt = true;
  await load(p);
  await ev(ADD_STRANDS);
  const games = await ev("window.yigExample.cards.map((c) => c.game + (c.community ? '*' : '')).join(',')");
  await ev(INSTALL);
  const press = (id) => ev(`window.__mark('${id}'); document.getElementById('tap-${id}').click()`);
  const wait = (s) => sleep(s * 1000);
  await openerStep();
  await ev("window.__log.length = 0");
  warnings.length = 0;
  await press("next"); await wait(T);
  await press("next");
  const iconLeaving = await ev(`(() => { const i = document.querySelector('[data-icon-game="wordle"]'); return i.hidden || i.classList.contains('yig-out'); })()`);
  await wait(Math.max(INTRO - T, QUICK) + 1.2);
  const log = await ev("window.__log");
  const [t1, t2] = log.filter((e) => e.label === "next").map((e) => e.at);
  const sceneL = await ev(`${VM}.enum('scene').value`);
  const lockupL = await ev(`${VM}.boolean('lockup').value`);
  const warned = warnings.filter((w) => w.includes("strands"));
  const goneL = log.find((e) => !e.label && e.at >= t2 && e.card !== "wordle#-");
  const riseL = log.find((e) => e.card === "strands#1" && e.cardRising);
  const startedAt = riseL ? riseL.at - t1 : null;
  const latest = Math.max(INTRO, T + QUICK);
  const lL = `strands card (not built) ${T.toFixed(1)} s into Wordle's intro (${games})`;
  check(sceneL === "wordle" && lockupL === false, `L  ${lL}: Rive stays on wordle with its lockup off (scene ${sceneL}, lockup ${lockupL})`);
  check(warned.length === 1, `L  ${lL}: one warning names strands (${warned.length}: ${warned[0] ?? "none"})`);
  check(!!goneL && goneL.at - t2 <= 0.15, `L  ${lL}: the Wordle card is gone within ${fmt(goneL ? goneL.at - t2 : null)} of the tap`);
  check(iconLeaving, `L  ${lL}: the Wordle icon leaves at once (${iconLeaving})`);
  check(startedAt !== null && startedAt >= INTRO - TOL, `L  ${lL}: the strands copy starts rising ${fmt(startedAt)} after the first tap (not before ${INTRO} s)`);
  check(startedAt !== null && startedAt <= latest + TOL, `L  ${lL}: ...and no later than ${latest.toFixed(2)} s (it was ${fmt(startedAt)})`);

  await ev("window.__log.length = 0");
  await press("back"); await wait(1.4);
  const sceneB = await ev(`${VM}.enum('scene').value`);
  const shownB = await shownCopy();
  check(sceneB === "wordle" && shownB === "wordle#-", `L  Back from it: the Wordle community card is back (${shownB || "none"}) and the scene is still 1 (${sceneB})`);
}

unbuilt = false;

//   N  the ending: the tap after the last game's last card pans to the empty Chapter 3 backdrop (scene to-chapter-3). The game's
//      card and icon leave at once; the ending's own copy (placeholder here) arrives 3.2 s later like a first visit.
//      Back returns to the last game's last card: its icon and card arrive when the pan ends (1.65 s).
{
  await load(basePlayer("wc"));
  const cardsIn = await cardsPerGame();
  await ev(INSTALL);
  const press = (id) => ev(`window.__mark('${id}'); document.getElementById('tap-${id}').click()`);
  const wait = (s) => sleep(s * 1000);
  await openerStep();
  await press("next"); await wait(INTRO + 0.6);
  for (let i = 2; i <= cardsIn.wordle; i++) { await press("next"); await wait(0.4); }
  await press("next"); await wait(INTRO + 0.6);
  for (let i = 2; i <= cardsIn.connections; i++) { await press("next"); await wait(0.4); }
  await wait(0.6);
  const last = "connections#" + cardsIn.connections;
  await ev("window.__log.length = 0");
  await press("next");
  await wait(INTRO + 0.8);
  let logN = await ev("window.__log");
  const tn = logN.find((e) => e.label === "next").at;
  const sceneN = await ev(`${VM}.enum('scene').value`);
  const goneN = logN.find((e) => !e.label && e.at >= tn && e.icon !== "connections" && e.card !== last);
  const riseN = logN.find((e) => e.card === "chapter3#1" && e.cardRising);
  check(sceneN === "to-chapter-3", `N  last game to the ending: Rive is on to-chapter-3, the empty Chapter 3 backdrop (scene ${sceneN})`);
  check(!!goneN && goneN.at - tn <= QUICK + TOL, `N  last game to the ending: the old card and icon are gone ${fmt(goneN ? goneN.at - tn : null)} after the tap`);
  check(!!riseN && Math.abs(riseN.at - tn - INTRO) <= TOL, `N  last game to the ending: the ending's copy rises ${fmt(riseN ? riseN.at - tn : null)} after the tap (want ${INTRO} s)`);
  await ev("window.__log.length = 0");
  await press("back");
  await wait(PAN + 1.0);
  logN = await ev("window.__log");
  const tb = logN.find((e) => e.label === "back").at;
  const iconB = logN.find((e) => e.icon === "connections" && e.iconPopping);
  const cardB = logN.find((e) => e.card === last && e.cardRising);
  const sceneB = await ev(`${VM}.enum('scene').value`);
  check(sceneB === "connections" && !!iconB && Math.abs(iconB.at - tb - PAN) <= TOL && !!cardB && Math.abs(cardB.at - tb - PAN - STEP) <= TOL,
        `N  Back from the ending: scene ${sceneB} (want connections); Connections' icon arrives ${fmt(iconB ? iconB.at - tb : null)} and its last card ${fmt(cardB ? cardB.at - tb : null)} after the tap (want ${PAN} s and ${(PAN + STEP).toFixed(2)} s)`);
}

//   K  the page's own example player, no injection: Next to the last card, then Back to the opener, waiting for
//      each arrival. After every tap the copy on screen is that card's, and the run ends on from-chapter-1.
{
  await load(null);
  const cards = await ev("window.yigExample.cards.map((c) => c.game)");
  const shown = () => ev(`[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.dataset.copyFrame).join(',')`);
  const want = (i) => (cards[i] === "chapter1" ? "" : String(i));    // the empty Chapter 1 room has no copy
  const bad = [];
  for (let i = 1; i < cards.length; i++) {
    await ev("document.getElementById('tap-next').click()");
    await sleep(cards[i] !== cards[i - 1] ? (INTRO + 0.6) * 1000 : 1000);
    const v = await shown(); if (v !== want(i)) bad.push(`Next to ${i}: ${v || "none"}`);
  }
  for (let i = cards.length - 2; i >= 0; i--) {
    await ev("document.getElementById('tap-back').click()");
    await sleep(cards[i] !== cards[i + 1] ? (PAN + 0.6) * 1000 : 1000);
    const v = await shown(); if (v !== want(i)) bad.push(`Back to ${i}: ${v || "none"}`);
  }
  const sceneEnd = await ev(`${VM}.enum('scene').value`);
  check(!bad.length, `K  example player (${cards.join(", ")}): the right copy after every tap, Next to the end and Back (${bad.join("; ") || "all " + (2 * cards.length - 2) + " taps"})`);
  check(sceneEnd === "from-chapter-1", `K  example player: ends on the empty Chapter 1 room (scene ${sceneEnd})`);
  check(cards[0] === "chapter1" && cards[cards.length - 1] === "chapter3", `K  example player: the cards start with chapter1 and end with chapter3 (${cards[0]} ... ${cards[cards.length - 1]})`);
}

proc.kill(); ws.close();
let failed = 0;
for (const r of results) { if (!r.ok) failed++; console.log((r.ok ? "PASS  " : "FAIL  ") + r.text); }
console.log(`\n${results.length - failed} of ${results.length} checks passed`);
process.exit(failed ? 1 : 0);
