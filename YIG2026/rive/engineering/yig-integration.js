// The whole experience on one stage: the three Rive files, Loading through End, switched on the empty rooms they share.
// A working reference for driving the files (you write your own code; engineering-guide.md says the same in words,
// and react/ is the same rules as a React hook). The rules, applied to every file:
//   - Every card names its file and the scene it shows. Setting a scene sets direction (and, in File 2, lockup) first.
//   - Every file starts and ends on an empty room, and neighbouring files share that picture: File 1's last ("ad", the
//     empty Chapter 1 room) is File 2's first ("from-chapter-1"); File 2's last ("to-chapter-3") is File 3's first ("ad").
//     So Next across files shows the next file, already sitting on that picture, and sets its scene on the same frame;
//     Back across files pans back inside the later file to that picture, then shows the earlier file, still on it.
//   - A card needn't sit on the empty room to cross: a Next from File 2's last game card plays two moves by itself (the
//     room pans out to the empty Chapter 3 room, File 3 takes over, and Chapter 3's room arrives right after), and Back
//     from Chapter 3 plays them in reverse to that game card. Anons keep Ad 3 as a card on the empty room.
//   - Files load ahead: File 1 at once, then each next file as soon as the one before it is ready. Every file stays
//     loaded, so Back across files never reloads; a file that isn't on screen is paused.
//   - An ad (a card tagged `ad: true`: Ad 1, Ad 2 and the anonymous Ad 3) shows only the first time the player reaches it with Next.
//     After that Back and Next skip it and land on the card on its other side; the move is worked out from the card landed on,
//     so it can be one move in a file, or the two-move crossing (Ad 2 sits between Chapter 1 card 5 and the Chapter 2 opener).
//   - A Back during a pan, or a Next during a Back pan, waits for the pan to end (the file can't turn a room around part-way).
//   - Copy arrives at fixed times: on a room's first visit 2.0 s after the scene is set (--yig-first-visit), or 3.2 s
//     (--yig-lockup, the whole intro) on a Chapter 2 game's first card with its lockup, so the copy never
//     overlaps the lockup; at the end of the pan (1.65 s) when the room comes back already built or is an empty room;
//     0.34 s within a room; 1.45 s when Chapter 4's `reveal` changes (the wall fades first). A two-move crossing adds
//     the first move's 1.65 s. The intros themselves stay 3.2 s: the copy arrives while a room is still finishing.

import { Rive } from "@rive-app/canvas"; // pin the version you ship; 2.27.3 and later work, with `stateMachines` (plural)

// The three files, in order, with the empty room each opens on and ends on, and the scenes with no intro of their own.
const FILES = [
  { src: "start-chapter-1.riv", opens: "loading", ends: "ad", noIntro: ["loading", "ad"] },
  { src: "chapter-2.riv", opens: "from-chapter-1", ends: "to-chapter-3", noIntro: ["from-chapter-1", "to-chapter-3", "bridge"], lockup: true },
  { src: "chapters-3-4-end.riv", opens: "ad", ends: "end", noIntro: ["ad"] },
];
// The order of the games in Chapter 2, and of Chapter 2.5's community cards, is ours by default and yours to change: the
// page that builds the card list reads these two constants. Rive plays any order, because each move just sets the next
// scene. COMMUNITY_GAMES are the games that have community cards (The Midi and The Crossword have none).
const GAME_ORDER = ["wordle", "connections", "spelling-bee", "mini", "midi", "daily", "strands"];
const COMMUNITY_GAMES = ["wordle", "connections", "spelling-bee", "mini", "strands"];
// The two first-visit copy times live in yig-text-motion.css, as --yig-first-visit (2s) and --yig-lockup (3.2s), and are
// read from there (cssMs) so the page and the CSS can't drift apart; change them there.
const REVEAL_FADE_MS = 1450; // Chapter 4: the wall fades to the top game's colour (or back to the lighter blue) this long after `reveal` changes
const PAN_MS = 1650;   // a room change: the moves run 1.6 s (the pan itself 0.05 to 1.55 s), plus a few frames

let stage = null;   // the element the canvases go in (engineering's full-bleed artboard box)
let files = [];     // per file: { rive, canvas, ready (a promise), loaded }
let cards = [];
let frame = 0;
let shown = 0;      // the file on screen
let visited = new Set();   // "file:scene" rooms whose intro has played (or that have none)
let copyFrom = {};         // "file:scene": when a first visit's copy may arrive, in performance.now() time
let pan = { dir: 0, endsAt: 0 };
let heldTimer = 0;
let holdToken = 0;  // a tap waiting for a file to load; only the last one counts
let swapTimer = 0;
let hopTimer = 0;   // a two-move Next: its second move (the next file taking over), still to come
let hopRun = null;
let seenAds = new Set();   // indexes of the ad cards the player has reached; a seen ad is skipped both ways

// Call once, before any tap, with the element to draw in and every card in order. A card is
//   { file: 1 | 2 | 3, scene: "<a scene of that file>", ad?: true, community?: true, icon?: "<game>", topGame?: "<game>" }
// file and scene drive Rive; ad marks Ad 1, Ad 2 and the anonymous Ad 3 (shown once, then skipped); community (File 2 only) leaves the game's lockup out, so its copy uses the first-visit time, not the lockup's;
// icon names the small HTML icon the card's copy shows with (data-icon-game), kept while the next cards share it;
// the first card with a topGame sets File 3's top game; reveal (File 3, Chapter 4) is false on the first Chapter 4 card
// (the stack and the ball on the lighter wall) and true from the top-game card on (the wall fades to that game's colour
// and its fireworks start), and is set on every move to a card that names it. Card i's copy is the element with data-copy-frame="i".
// The first card is Loading (file 1, scene "loading"); Back never returns to it. A card may leave a file from any
// scene; when it isn't on the file's last picture (File 1 "ad", File 2 "to-chapter-3") the move first plays out to it,
// so the next file can take over invisibly.
function start(el, list) {
  stage = el;
  cards = list.map((c) => ({ ...c }));
  cards.forEach((c, i) => {
    const next = cards[i + 1];
    if (next && next.file !== c.file && next.file !== c.file + 1) {
      throw new Error(`card ${i}: file ${c.file} is followed by file ${next.file}; files go in order`);
    }
  });
  frame = 0;
  shown = 0;
  visited = new Set(FILES.map((f, i) => `${i + 1}:${f.opens}`));
  seenAds = new Set();
  copyFrom = {};
  pan = { dir: 0, endsAt: 0 };
  files = FILES.map(() => null);
  load(0);
  showCopy(0, { changed: true, delay: 0 });
}

// Load a file on its opening picture, paused until it is needed; when it is ready, start loading the next one.
function load(i) {
  const canvas = document.createElement("canvas");
  canvas.className = "yig-file";
  canvas.style.visibility = i === shown ? "visible" : "hidden";
  stage.append(canvas);
  const f = { canvas, rive: null, loaded: false };
  f.ready = new Promise((resolve) => {
    f.rive = new Rive({
      src: FILES[i].src,
      canvas,
      stateMachines: "Backdrop", // plural: runtime 2.27.3 ignores the singular `stateMachine`
      autoplay: true,
      autoBind: true,
      onLoad: () => {
        f.rive.resizeDrawingSurfaceToCanvas();
        const top = cards.find((c) => c.topGame)?.topGame;
        if (top && f.rive.viewModelInstance.enum("topGame")) f.rive.viewModelInstance.enum("topGame").value = top;
        f.loaded = true;
        // let it draw its opening picture once, then rest until it is shown
        requestAnimationFrame(() => requestAnimationFrame(() => { if (i !== shown) f.rive.pause(); }));
        if (i + 1 < FILES.length && !files[i + 1]) load(i + 1);
        resolve();
      },
    });
  });
  files[i] = f;
}

// File 3's `reveal` for a card in the same room (Chapter 4's cards): the wall fades as the player taps. A move that changes
// room sets `reveal` inside setScene instead, in the guide's order.
function applyReveal(card) {
  if (card.reveal === undefined) return false;
  const f = files[card.file - 1];
  const prop = f?.loaded && f.rive.viewModelInstance.boolean("reveal");
  if (!prop) return false;
  const changed = prop.value !== !!card.reveal;
  prop.value = !!card.reveal;
  return changed; // the wall is about to fade (1.45 s), forward or back
}

// A room change sets direction, lockup, reveal, then scene (the guide's order); `reveal` is passed only for a card that names it (File 3).
function setScene(i, scene, step, community, reveal) {
  const vm = files[i].rive.viewModelInstance;
  vm.enum("direction").value = step < 0 ? "back" : "forward";
  if (FILES[i].lockup) vm.boolean("lockup").value = !community;
  if (reveal !== undefined && vm.boolean("reveal")) vm.boolean("reveal").value = !!reveal;
  vm.enum("scene").value = scene;
}

// Show file i: on top of the one on screen, playing, then the old one hides and rests once the new one has drawn.
function show(i) {
  if (i === shown) return;
  const old = files[shown];
  const f = files[i];
  f.canvas.style.visibility = "visible";
  f.canvas.style.zIndex = "1";
  f.rive.play();
  requestAnimationFrame(() => requestAnimationFrame(() => {
    old.canvas.style.visibility = "hidden";
    old.canvas.style.zIndex = "";
    old.rive.pause();
    f.canvas.style.zIndex = "";
  }));
  shown = i;
}

function onTap() {
  move(+1);
}

function onBack() {
  move(-1);
}

// The card a tap lands on: the next one in that direction, leaving out any ad the player has already seen.
function landing(step) {
  let target = frame + step;
  while (cards[target]?.ad && seenAds.has(target)) target += step;
  return target;
}

function move(step) {
  clearTimeout(heldTimer);
  const token = ++holdToken;
  const target = landing(step);
  if (target < 1 && step < 0) return; // Back never returns to Loading
  if (target < 0 || target > cards.length - 1) return;
  const from = cards[frame];
  const to = cards[target];
  const roomChange = to.file !== from.file || to.scene !== from.scene;
  const now = performance.now();
  // crossing files from a card that isn't on the empty room: the first move goes to that room, the second starts after it
  const legs = to.file !== from.file && (step > 0 ? from.scene !== FILES[from.file - 1].ends : to.scene !== FILES[to.file - 1].ends) ? 2 : 1;
  if (roomChange && pan.endsAt > now && (step < 0 || pan.dir < 0)) {
    heldTimer = setTimeout(() => move(step), pan.endsAt - now);
    return;
  }
  const fi = to.file - 1;
  if (step > 0 && !files[fi]?.loaded) {
    // the next file hasn't loaded yet: hold the tap on the empty room until it has
    if (!files[fi]) load(fi);
    files[fi].ready.then(() => { if (token === holdToken) move(step); });
    return;
  }
  if (roomChange) clearTimeout(swapTimer); // a new room change takes over from a Back's hand-back still to come
  if (roomChange && hopRun) { clearTimeout(hopTimer); hopRun(); } // and cuts a Next's two moves short: the next file takes over now
  frame = target;
  if (to.ad) seenAds.add(target);
  const fading = !roomChange && applyReveal(to);
  const key = `${to.file}:${to.scene}`;
  const firstVisit = roomChange && step > 0 && !visited.has(key) && !FILES[fi].noIntro.includes(to.scene);
  if (roomChange) {
    pan = { dir: step, endsAt: now + PAN_MS * legs };
    if (to.file === from.file) {
      setScene(fi, to.scene, step, !!to.community, to.reveal);
    } else if (step > 0) {
      // Next into another file: it is already on the shared picture, so show it and set its scene on the same frame
      const takeOver = () => { hopRun = null; show(fi); setScene(fi, to.scene, step, !!to.community, to.reveal); };
      if (legs === 1) {
        takeOver();
      } else {
        // first the room pans out to the empty room, then the next file takes over
        setScene(from.file - 1, FILES[from.file - 1].ends, step, false);
        hopRun = takeOver;
        hopTimer = setTimeout(takeOver, PAN_MS);
      }
    } else {
      // Back into the earlier file: pan back inside this file to the shared picture, then hand the stage back (and, if
      // the card isn't on that picture, pan back into its room)
      setScene(from.file - 1, FILES[from.file - 1].opens, step, false);
      swapTimer = setTimeout(() => { show(fi); if (legs === 2) setScene(fi, to.scene, step, !!to.community, to.reveal); }, PAN_MS);
    }
  }
  if (firstVisit) {
    visited.add(key);
    copyFrom[key] = now + (legs - 1) * PAN_MS + firstVisitCopyMs(to);
  }
  const iconChange = to.icon !== from.icon;
  const settleLeft = Math.max(0, (copyFrom[key] ?? 0) - now); // an interrupted first visit still waits for its room
  let delay;
  if (!roomChange) delay = fading ? Math.max(settleLeft, REVEAL_FADE_MS) : settleLeft > 0 ? settleLeft : null; // null: the quick swap after the old copy clears; a reveal waits for the wall's fade
  else if (firstVisit) delay = copyFrom[key] - now;
  else delay = Math.max(PAN_MS * legs, settleLeft);
  showCopy(frame, { changed: roomChange || iconChange, delay, back: step < 0 });
}

// How long a first visit's copy waits after its scene is set: the whole intro when a Chapter 2 game's lockup shows (a
// game's card that isn't a community card), the first-visit constant everywhere else.
function firstVisitCopyMs(card) {
  return card.file === 2 && GAME_ORDER.includes(card.scene) && !card.community ? cssMs("--yig-lockup", 3200) : cssMs("--yig-first-visit", 2000);
}

// The old copy (and its icon, when the icon changes) leaves at once; the new copy arrives after `delay` ms, or with
// yig-quick (once the old copy has cleared) when delay is null.
function showCopy(n, { changed, delay, back = false }) {
  const visible = [...document.querySelectorAll(".yig-text:not([hidden]), .yig-icon:not([hidden])")];
  visible.filter((el) => changed || !el.classList.contains("yig-icon")).forEach((el) => leave(el, back));
  const next = document.querySelector(`[data-copy-frame="${n}"]`);
  const icon = cards[n].icon && document.querySelector(`[data-icon-game="${cards[n].icon}"]`);
  const iconStays = !changed && icon && !icon.hidden;
  if (delay === null && changed) delay = clearMs();
  if (icon && !iconStays) enter(icon, { delay, back });
  if (next) enter(next, delay === null ? { quick: true, back } : { delay, afterIcon: !!icon && !iconStays, back });
}

function leave(el, back = false) {
  const settled = el.getAnimations({ subtree: true }).every((a) => a.playState === "finished");
  if (settled) {
    el.classList.toggle("yig-back", back);
    el.classList.add("yig-out");
    setTimeout(() => { el.hidden = true; }, clearMs());
  } else {
    el.hidden = true;
  }
}

function clearMs() {
  return cssMs("--yig-clear", 340);
}

// A time from yig-text-motion.css, in ms; the fallback (the stylesheet's own value) if it hasn't loaded.
function cssMs(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const ms = v.endsWith("ms") ? parseFloat(v) : parseFloat(v) * 1000;
  return Number.isFinite(ms) ? ms : fallback;
}

function enter(el, { quick = false, delay = null, afterIcon = false, back = false } = {}) {
  el.classList.remove("yig-in", "yig-out");
  el.classList.toggle("yig-quick", quick);
  el.classList.toggle("yig-after-icon", afterIcon);
  el.classList.toggle("yig-back", back);
  if (delay === null) el.style.removeProperty("--yig-delay");
  else el.style.setProperty("--yig-delay", `${delay}ms`);
  el.hidden = false;
  void el.offsetWidth;
  el.classList.add("yig-in");
}

// Resolves when a file (1, 2 or 3) has loaded; Loading's own wait for the stats can run alongside File 1's.
function ready(file) {
  return files[file - 1]?.ready ?? Promise.resolve();
}

// Resize every file's drawing surface to its canvas (call on window resize).
function resize() {
  files.forEach((f) => f?.loaded && f.rive.resizeDrawingSurfaceToCanvas());
}

// for debugging and the review page
const state = () => ({ frame, shown: shown + 1, card: cards[frame], scenes: files.map((f) => f?.loaded ? f.rive.viewModelInstance.enum("scene").value : null) });

export { start, onTap, onBack, ready, resize, state, FILES, GAME_ORDER, COMMUNITY_GAMES };
