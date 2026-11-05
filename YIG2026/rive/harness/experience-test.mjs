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
import path from "node:path";
import { chromeProfile } from "./scratch.mjs";   // Chrome's profile goes in .cache/scratch.nosync/, never /tmp

const args = process.argv.slice(2);
const flag = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const BASE = flag("--url", "http://127.0.0.1:8765");
const TRACE = args.includes("--trace");
const rangeOf = (n) => (args.includes(n) ? args[args.indexOf(n) + 1].split("-").map(Number) : null);
const NEXT_RANGE = rangeOf("--next-range"), BACK_RANGE = rangeOf("--back-range");   // A-B: start at card A (?jump=A) and walk Next up to B, or Back down to B
const PATH = flag("--path", "/experience-stage");                                    // /reference/example/ for the unzipped package
const FLOWS = flag("--flows", "sub,anon").split(",");
const SIZES = flag("--sizes", "phone,desktop").split(",");
const PLAYERS = flag("--players", "wordle-only").split(",");                         // subscriber players to walk
const INTRO = 3.2, PAN = 1.65;
// When a card's copy arrives after a room change (the guide, section 6): a first visit FIRST, or LOCKUP on a Chapter 2
// game's first card with its lockup; a picture or a room coming back PAN; a two-move crossing adds a PAN.
const FIRST = 2.0, LOCKUP = 3.2;
const NO_INTRO = { 1: ["loading", "ad"], 2: ["from-chapter-1", "to-chapter-3"], 3: ["ad"] };
// Scenes that share a room (written out from the guide's Scenes table, not read from the integration): a move between two of them
// is not a room change, and its copy swaps after the usual 0.34 s, except a move that changes Chapter 4's `reveal`
// (chapter-4 to chapter-4-top-game, and Back): its copy waits REVEAL s for the wall's fade.
const REVEAL = 1.45;
const SHARED_ROOMS = [["ad", "chapter-3-personal-badges", "chapter-3-event-badges"], ["chapter-3", "chapter-3-2"], ["chapter-4", "chapter-4-top-game", "chapter-4-editor-video"], ["end", "share"]];
const roomOf = (file, scene) => (file === 3 ? SHARED_ROOMS.find((l) => l.includes(scene))?.[0] : null) ?? scene;
const sameRoom = (a, b) => a.file === b.file && roomOf(a.file, a.scene) === roomOf(b.file, b.scene);
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
const check = (ok, text) => { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${text}`); };

async function browser(width, height) {
  const port = 9650 + Math.floor(Math.random() * 140);
  const proc = spawn(chrome, ["--headless=new", `--remote-debugging-port=${port}`, `--window-size=${width},${height}`, "--hide-scrollbars",
    `--user-data-dir=${chromeProfile("yig-exp-")}`, "about:blank"], { stdio: "ignore" });
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
  // a lost browser connection or a call that takes over 60 s fails the run with a message, instead of hanging it
  const dead = (why) => { console.log(`FAIL  browser: ${why}`); process.exit(2); };
  ws.onclose = () => dead("the connection to Chrome closed");
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); const t = setTimeout(() => dead(`no answer to ${method} within 60 s`), 60000); pending.set(i, (d) => { clearTimeout(t); r(d); }); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
  await send("Runtime.enable"); await send("Network.enable"); await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  return { ev, errors, rivs, close: () => { ws.onclose = null; ws.close(); proc.kill(); }, nav: (url) => send("Page.navigate", { url }) };
}

const shownCopy = "[...document.querySelectorAll('.yig-text')].filter((e) => !e.hidden).map((e) => e.dataset.copyFrame).join(',')";

// What each flow's card list must be, written out from the rules in the engineering guide (not read from the page)
const ORDER = ["wordle", "connections", "spelling-bee", "mini", "midi", "crossword", "strands"];
const PER_GAME = { wordle: 4, connections: 5, "spelling-bee": 2, mini: 1, midi: 1, crossword: 1, strands: 1 };
const COMMUNITY = ["wordle", "connections", "spelling-bee", "mini", "strands"];
const COMPLETED = {
  "wordle-only": { wordle: 212, connections: 7, mini: 3 }, "midi-only": { midi: 40, crossword: 4 }, "connections-only": { wordle: 4, connections: 120, strands: 2 },
  "all-seven": Object.fromEntries(ORDER.map((g) => [g, 50])), "several-games": { wordle: 212, connections: 7, strands: 30, "spelling-bee": 64, mini: 50, midi: 40, crossword: 90 }, none: { wordle: 3, connections: 2 },
};
const BADGES = { "wordle-only": [5, 9], "midi-only": [3, 0], "connections-only": [0, 3], "all-seven": [0, 0], "several-games": [0, 14], none: [0, 0] };
function expectedCards(flow, player) {
  const own = ORDER.filter((g) => (COMPLETED[player][g] ?? 0) >= 10);
  const anon = flow === "anon" || own.length === 0;
  const out = ["1:loading", "1:start", "1:ad", "1:chapter-1", "1:chapter-1-2", "1:chapter-1-3", "1:chapter-1-4", "1:chapter-1-5", "1:ad", "2:chapter-2"];
  if (anon) {
    out.push(...COMMUNITY.filter((g) => g !== "wordle").map((g) => `2:${g}`), "2:to-chapter-3", "3:chapter-3", "3:chapter-3-2", "3:chapter-3-event-badges", "3:chapter-3-event-badges");
  } else {
    for (const g of own) for (let i = 0; i < PER_GAME[g]; i++) out.push(`2:${g}`);
    if (own.length === 1) out.push("2:chapter-2-community-intro", ...COMMUNITY.filter((g) => g !== own[0]).map((g) => `2:${g}`));
    out.push("3:chapter-3", "3:chapter-3-2");
    if (BADGES[player][1] > 0) out.push("3:chapter-3-personal-badges");   // personal badges first, then event badges
    if (BADGES[player][0] > 0) out.push("3:chapter-3-event-badges");
  }
  out.push("3:chapter-4", "3:chapter-4-top-game", "3:chapter-4-editor-video", "3:end");
  if (!anon) out.push("3:share");
  return out;
}

const runs = [];
for (const flow of FLOWS) for (const player of flow === "sub" ? PLAYERS : ["wordle-only"]) for (const size of SIZES) runs.push([flow, player, size]);
for (const [flow, player, size] of runs) {
  for (const [w, h, label] of [size === "phone" ? [430, 932, "phone"] : [1440, 900, "desktop"]]) {
    const b = await browser(w, h);
    const RANGE = NEXT_RANGE || BACK_RANGE;
    await b.nav(`${BASE}${PATH}?flow=${flow}&player=${player}${RANGE ? `&jump=${RANGE[0]}` : ""}`);
    for (let i = 0; i < 150 && !(await b.ev("!!window.yigExperience")); i++) await sleep(100);
    const cards = await b.ev("window.yigExperience.cards.map((c) => ({ file: c.file, scene: c.scene, reveal: c.reveal, icon: c.icon, ad: !!c.ad, community: !!c.community }))");
    const st = () => b.ev("window.yigExperience.state()");
    const tag = `${flow}${flow === "sub" ? " " + player : ""} · ${label} ${w}x${h}`;
    const want = expectedCards(flow, player);
    const got = cards.map((c) => `${c.file}:${c.scene}`);
    check(JSON.stringify(got) === JSON.stringify(want), `${tag}: the card list is the guide's (${got.length} cards)` + (JSON.stringify(got) === JSON.stringify(want) ? "" : `; got ${got.join(" ")} / want ${want.join(" ")}`));
    // the ad cards are Ad 1 (the first File 1 `ad`), Ad 2 (the one after chapter-1-5) and, for anonymous players, Ad 3
    // (File 2's `to-chapter-3`); the badge cards (File 3's chapter-3-*-badges scenes) are not ads
    const adsWant = [2, want.indexOf("2:chapter-2") - 1, ...(flow === "anon" || want.includes("2:to-chapter-3") ? [want.indexOf("2:to-chapter-3")] : [])];
    const adsGot = cards.map((c, i) => (c.ad ? i : -1)).filter((i) => i >= 0);
    check(JSON.stringify(adsGot) === JSON.stringify(adsWant), `${tag}: the ad cards are tagged ad (cards ${adsGot.join(", ")}; want ${adsWant.join(", ")})`);
    if (RANGE) {
      // a short stretch only: jump to card A behind the curtain, let it settle, then walk Next up to B (or Back down to B)
      const [from, to] = RANGE, fwd = !!NEXT_RANGE;
      for (let i = 0; i < 300 && (await st()).frame !== from; i++) await sleep(100);
      await sleep((INTRO + PAN + 1.5) * 1000);
      const next = label === "desktop" ? "arrow-next" : "tap-next", back = label === "desktop" ? "arrow-back" : "tap-back";
      const bad = [];
      for (let i = fwd ? from + 1 : from - 1; fwd ? i <= to : i >= to; i += fwd ? 1 : -1) {
        const prev = fwd ? i - 1 : i + 1;
        await b.ev(`document.getElementById('${fwd ? next : back}').click()`);
        const moved = !sameRoom(cards[i], cards[prev]);      // a change inside one room is a quick copy swap, not a pan
        const edge = fwd ? cards[prev] : cards[i];
        const extra = cards[i].file !== cards[prev].file && edge.scene !== { 1: "ad", 2: "to-chapter-3" }[edge.file] ? PAN : 0;
        await sleep(!moved ? 900 : fwd ? (INTRO + extra + 0.6) * 1000 : (PAN + extra + 0.7) * 1000);
        const x = await st(), copy = await b.ev(shownCopy);
        if (TRACE) console.log(`TRACE ${fwd ? "Next" : "Back"} to card ${i}: file ${x.shown}, scene ${x.scenes[x.shown - 1]}, copy ${copy || "none"}`);
        if (x.frame !== i || x.shown !== cards[i].file || x.scenes[cards[i].file - 1] !== cards[i].scene || copy !== String(i)) bad.push(`to ${i} (${cards[i].file}:${cards[i].scene}): card ${x.frame}, file ${x.shown}, scene ${x.scenes[x.shown - 1]}, copy ${copy || "none"}`);
      }
      check(!bad.length, `${tag}: ${fwd ? "Next" : "Back"} from card ${from} to ${to}: the right file, scene and copy each time${bad.length ? ": " + bad.slice(0, 3).join(" / ") : ""}`);
      check(b.errors.length === 0, `${tag}: no console errors${b.errors.length ? ": " + b.errors.slice(0, 2).join(" / ") : ""}`);
      b.close();
      continue;
    }
    // Loading hands over to Start by itself once File 1 is in
    for (let i = 0; i < 80 && (await st()).frame === 0; i++) await sleep(100);
    await sleep(INTRO * 1000 + 500);
    let s = await st();
    check(s.frame === 1 && s.scenes[0] === "start", `${tag}: Loading hands over to Start (card ${s.frame}, scene ${s.scenes[0]})`);
    const startDelay = await b.ev(`document.querySelector('[data-copy-frame="1"]')?.style.getPropertyValue('--yig-delay') ?? null`);
    check(Math.abs(parseFloat(startDelay) - FIRST * 1000) <= 1, `${tag}: Start's copy waits ${startDelay} after the scene is set (want ${FIRST * 1000}ms, a first visit)`);

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
      const moved = !sameRoom(cards[i], cards[from]);      // a change inside one room is a quick copy swap, not a pan
      const edge = forward ? cards[from] : cards[i];
      const extra = cards[i].file !== cards[from].file && edge.scene !== ENDS[edge.file] ? PAN : 0;
      return !moved ? 900 : forward ? (INTRO + extra + 0.6) * 1000 : (PAN + extra + 0.7) * 1000;
    };
    const verify = async (i, how) => {
      const x = await st();
      const copy = await b.ev(shownCopy);
      if (TRACE) console.log(`TRACE ${how} to card ${i}: file ${x.shown}, scene ${x.scenes[x.shown - 1]}, copy ${copy || "none"}`);
      if (x.frame !== i || x.shown !== cards[i].file || x.scenes[cards[i].file - 1] !== cards[i].scene || copy !== String(i)) {
        bad.push(`${how} to ${i} (${cards[i].file}:${cards[i].scene}): card ${x.frame}, file ${x.shown}, scene ${x.scenes[x.shown - 1]}, copy ${copy || "none"}`);
      }
    };
    const delayOf = (i) => b.ev(`(() => { const e = document.querySelector('[data-copy-frame="${i}"]'); return e ? { delay: e.style.getPropertyValue('--yig-delay'), quick: e.classList.contains('yig-quick') } : null; })()`);
    const revealBad = [];
    // the copy delay a Next sets on a room change, on this walk where every room is new (the guide, section 6)
    const legsNext = (from, to) => (cards[to].file !== cards[from].file && cards[from].scene !== ENDS[cards[from].file] ? 2 : 1);
    const wantNextMs = (i) => {
      const legs = legsNext(i - 1, i), c = cards[i];
      if (NO_INTRO[c.file].includes(roomOf(c.file, c.scene))) return PAN * legs * 1000;
      const lockup = c.file === 2 && ORDER.includes(c.scene) && !c.community;
      return ((legs - 1) * PAN + (lockup ? LOCKUP : FIRST)) * 1000;
    };
    const timingBad = [];
    // no fade: the copy swaps quickly, or, when the game icon changes, waits the 340 ms the old icon takes to lift (never the 1.45 s)
    const okNoFade = (d, iconChanges) => !!d && (d.quick || (iconChanges && d.delay === "340ms"));
    // a move inside the room that changes reveal waits for the wall's fade (this walk never taps before a room's copy is due,
    // so the wait is exactly the fade)
    const revealChanges = (a, b) => a.reveal !== undefined && b.reveal !== undefined && a.reveal !== b.reveal;
    const okSameRoom = (d, to, from) => (revealChanges(to, from)
      ? !!d && !d.quick && Math.abs(parseFloat(d.delay) - REVEAL * 1000) <= 1
      : okNoFade(d, to.icon !== from.icon));
    const sameRoomWant = (to, from) => (revealChanges(to, from) ? `wants ${REVEAL * 1000}ms, the wall's fade` : "wants the quick swap, or 340ms when the icon changes");
    for (let i = 2; i < cards.length; i++) {
      await b.ev(`document.getElementById('${next}').click()`);
      if (!sameRoom(cards[i], cards[i - 1])) {
        await sleep(60);
        const d = await delayOf(i);
        if (!d || Math.abs(parseFloat(d.delay) - wantNextMs(i)) > 1) timingBad.push(`Next to ${i} (${cards[i].file}:${cards[i].scene}${cards[i].community ? ", community" : ""}): ${d?.delay || "none"}, want ${wantNextMs(i)}ms`);
      }
      if (sameRoom(cards[i], cards[i - 1])) {
        await sleep(60);
        const d = await delayOf(i);
        if (!okSameRoom(d, cards[i], cards[i - 1])) revealBad.push(`Next to ${i} (${cards[i].scene}): ${JSON.stringify(d)} (${sameRoomWant(cards[i], cards[i - 1])})`);
      }
      await sleep(settle(i, i - 1, true));
      await verify(i, "Next");
    }
    check(!bad.length, `${tag}: Next through all ${cards.length} cards: the right file, scene and copy each time${bad.length ? ": " + bad.slice(0, 3).join(" / ") : ""}`);
    check(!timingBad.length, `${tag}: every room change on the way waits the guide's time: ${FIRST} s on a first visit, ${LOCKUP} s with a lockup, ${PAN} s for a picture, plus ${PAN} s for a second move${timingBad.length ? ": " + timingBad.slice(0, 4).join(" / ") : ""}`);
    check(!revealBad.length, `${tag}: a change between scenes that share a room (or a repeat of one) swaps the copy after 0.34 s, or waits ${REVEAL} s when Chapter 4's reveal changes, forward and back${revealBad.length ? ": " + revealBad.join(" / ") : ""}`);
    check(JSON.stringify([...b.rivs].sort()) === JSON.stringify(["chapter-2.riv", "chapters-3-4-end.riv", "start-chapter-1.riv"]),
      `${tag}: each .riv was fetched once, the next ones ahead of time (${b.rivs.join(", ")})`);
    bad.length = 0;
    // every ad has been seen on the way here, so Back skips them all: it lands on the card on the ad's other side
    for (let from = cards.length - 1; from > 1;) {
      let i = from - 1;
      while (i > 1 && cards[i].ad) i--;
      await b.ev(`document.getElementById('${back}').click()`);
      if (sameRoom(cards[i], cards[from])) {
        await sleep(60);
        const d = await delayOf(i);
        if (!okSameRoom(d, cards[i], cards[from])) revealBad.push(`Back to ${i} (${cards[i].scene}): ${JSON.stringify(d)} (${sameRoomWant(cards[i], cards[from])})`);
      }
      await sleep(settle(i, from, false));
      await verify(i, "Back");
      from = i;
    }
    check(!bad.length, `${tag}: Back all the way to Start, across both file boundaries and skipping every ad: the right file, scene and copy each time${bad.length ? ": " + bad.slice(0, 3).join(" / ") : ""}`);
    check(b.rivs.length === 3, `${tag}: Back across files reloaded nothing (${b.rivs.length} .riv requests)`);
    await b.ev(`document.getElementById('${back}').click()`);
    await sleep(600);
    s = await st();
    check(s.frame === 1, `${tag}: Back on Start does nothing; Loading never comes back (card ${s.frame})`);

    // a Back during the Next pan into File 2 waits for the pan, then lands back in File 1. Ad 2 has been seen, so Next from
    // chapter-1-5 skips it and plays the two-move crossing (File 1 out to the empty room, File 2 takes over and pans in),
    // and the Back after it skips Ad 2 too: File 2 pans back to the empty room, then File 1 pans back into card 5
    const firstOf2 = cards.findIndex((c) => c.file === 2);
    const card5 = firstOf2 - 2;
    while ((await st()).frame < card5) { await b.ev(`document.getElementById('${next}').click()`); await sleep(120); }
    await sleep((INTRO + 0.6) * 1000);
    await b.ev(`document.getElementById('${next}').click()`);
    await sleep(500);
    await b.ev(`document.getElementById('${back}').click()`);
    await sleep(200);
    const mid = await st();
    await sleep((PAN * 3 + 0.8) * 1000);
    const end = await st();
    check(mid.frame === firstOf2 && end.frame === card5 && end.shown === 1,
      `${tag}: a Back 0.5 s into the two-move Next into File 2 waits (card ${mid.frame}), then skips Ad 2 and lands on chapter-1-5 (card ${end.frame}, file ${end.shown})`);
    check(b.errors.length === 0, `${tag}: no console errors${b.errors.length ? ": " + b.errors.slice(0, 2).join(" / ") : ""}`);
    b.close();

    // each ad, on its own: with the ad seen, Back skips it and lands on the card before it; Next skips it again and lands on
    // the card after it. The copy waits the room's pan (1.65 s) or, for a crossing from a card that isn't on the empty room,
    // both moves (3.3 s); neither card is a first visit (the jump walked through them), so neither waits for an intro.
    for (const ad of adsGot) {
      const before = ad - 1, after = ad + 1;
      const c2 = await browser(w, h);
      await c2.nav(`${BASE}${PATH}?flow=${flow}&player=${player}&jump=${after}`);
      for (let i = 0; i < 150 && !(await c2.ev("!!window.yigExperience")); i++) await sleep(100);
      const st2 = () => c2.ev("window.yigExperience.state()");
      for (let i = 0; i < 400 && (await st2()).frame !== after; i++) await sleep(100);
      await sleep((INTRO + PAN + 1.5) * 1000);
      const legsOf = (from, to, forward) => (cards[to].file !== cards[from].file && (forward ? cards[from].scene !== ENDS[cards[from].file] : cards[to].scene !== ENDS[cards[to].file]) ? 2 : 1);
      const problems = [];
      for (const [to, from, forward] of [[before, after, false], [after, before, true]]) {
        await c2.ev(`document.getElementById('${forward ? next : back}').click()`);
        await sleep(60);
        const d = await c2.ev(`(() => { const e = document.querySelector('[data-copy-frame="${to}"]'); return e ? e.style.getPropertyValue('--yig-delay') : null; })()`);
        const wantMs = `${Math.round(PAN * legsOf(from, to, forward) * 1000)}ms`;
        if (d !== wantMs) problems.push(`${forward ? "Next" : "Back"} to ${to}: the copy waits ${d}, not ${wantMs}`);
        await sleep(settle(to, from, forward));
        const x = await st2(), copy = await c2.ev(shownCopy);
        if (x.frame !== to || x.shown !== cards[to].file || x.scenes[cards[to].file - 1] !== cards[to].scene || copy !== String(to)) {
          problems.push(`${forward ? "Next" : "Back"} to ${to} (${cards[to].file}:${cards[to].scene}): card ${x.frame}, file ${x.shown}, scene ${x.scenes[x.shown - 1]}, copy ${copy || "none"}`);
        }
      }
      if (c2.errors.length) problems.push(`console errors: ${c2.errors.slice(0, 2).join(" / ")}`);
      check(!problems.length, `${tag}: ad card ${ad} (${cards[ad].file}:${cards[ad].scene}): Back skips it to card ${before}, Next skips it to card ${after}, right file, scene, copy and copy timing${problems.length ? ": " + problems.join(" / ") : ""}`);
      c2.close();
    }
  }
}
console.log(`\n${results.filter(Boolean).length} of ${results.length} checks passed`);
process.exit(results.every(Boolean) ? 0 : 1);
