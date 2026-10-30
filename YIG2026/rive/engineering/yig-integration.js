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
//   - A Back during a pan, or a Next during a Back pan, waits for the pan to end (the file can't turn a room around part-way).
//   - Copy arrives when the room has settled: 3.2 s on a room's first visit (its intro), at the end of the pan (1.65 s)
//     when the room comes back already built or is an empty room, 0.34 s within a room, and on a community card as soon
//     as its room's intro settles (no lockup to wait for). A two-move crossing adds the first move's 1.65 s.

import { Rive } from "@rive-app/canvas"; // pin the version you ship; 2.27.3 and later work, with `stateMachines` (plural)

// The three files, in order, with the empty room each opens on and ends on, and the scenes with no intro of their own.
const FILES = [
  { src: "start-chapter-1.riv", opens: "loading", ends: "ad", noIntro: ["loading", "ad"] },
  { src: "chapter-2.riv", opens: "from-chapter-1", ends: "to-chapter-3", noIntro: ["from-chapter-1", "to-chapter-3", "bridge"], lockup: true },
  { src: "chapters-3-4-end.riv", opens: "ad", ends: "end", noIntro: ["ad"] },
];
const INTRO_MS = 3200; // every intro is exactly this long
const PAN_MS = 1650;   // a room change: the moves run 1.6 s (the pan itself 0.05 to 1.55 s), plus a few frames
// File 2's community cards: copy arrives when the room's pieces have landed, without waiting for the ball or the lockup (chapters/ch2/chapter.json,
// communityCopyMs, measured from the file by our checks).
const COMMUNITY_COPY_MS = { wordle: 2334, connections: 2367, strands: 1967, "spelling-bee": 2017, mini: 2084, midi: 1950, daily: 1950 };

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

// Call once, before any tap, with the element to draw in and every card in order. A card is
//   { file: 1 | 2 | 3, scene: "<a scene of that file>", community?: true, icon?: "<game>", topGame?: "<game>" }
// file and scene drive Rive; community (File 2 only) leaves the game's lockup out and times the copy to the room;
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

// File 3's `reveal`: set with the move to a card that names it, so the wall fades as the player taps
function applyReveal(card) {
  if (card.reveal === undefined) return;
  const f = files[card.file - 1];
  const prop = f?.loaded && f.rive.viewModelInstance.boolean("reveal");
  if (prop) prop.value = !!card.reveal;
}

function setScene(i, scene, step, community) {
  const vm = files[i].rive.viewModelInstance;
  vm.enum("direction").value = step < 0 ? "back" : "forward";
  if (FILES[i].lockup) vm.boolean("lockup").value = !community;
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

function move(step) {
  clearTimeout(heldTimer);
  const token = ++holdToken;
  const target = frame + step;
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
  applyReveal(to);
  const key = `${to.file}:${to.scene}`;
  const firstVisit = roomChange && step > 0 && !visited.has(key) && !FILES[fi].noIntro.includes(to.scene);
  if (roomChange) {
    pan = { dir: step, endsAt: now + PAN_MS * legs };
    if (to.file === from.file) {
      setScene(fi, to.scene, step, !!to.community);
    } else if (step > 0) {
      // Next into another file: it is already on the shared picture, so show it and set its scene on the same frame
      const takeOver = () => { hopRun = null; show(fi); setScene(fi, to.scene, step, !!to.community); };
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
      swapTimer = setTimeout(() => { show(fi); if (legs === 2) setScene(fi, to.scene, step, !!to.community); }, PAN_MS);
    }
  }
  if (firstVisit) {
    visited.add(key);
    copyFrom[key] = now + (legs - 1) * PAN_MS + (to.community && to.scene in COMMUNITY_COPY_MS ? COMMUNITY_COPY_MS[to.scene] : INTRO_MS);
  }
  const iconChange = to.icon !== from.icon;
  const settleLeft = Math.max(0, (copyFrom[key] ?? 0) - now); // an interrupted first visit still waits for its room
  let delay;
  if (!roomChange) delay = settleLeft > 0 ? settleLeft : null;        // null: the quick swap after the old copy clears
  else if (firstVisit) delay = copyFrom[key] - now;
  else delay = Math.max(PAN_MS * legs, settleLeft);
  showCopy(frame, { changed: roomChange || iconChange, delay, back: step < 0 });
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
  const v = getComputedStyle(document.documentElement).getPropertyValue("--yig-clear").trim();
  const ms = v.endsWith("ms") ? parseFloat(v) : parseFloat(v) * 1000;
  return Number.isFinite(ms) ? ms : 340;
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

export { start, onTap, onBack, ready, resize, state, FILES };
