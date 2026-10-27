// Frames name their game; this table turns the name into the Rive file's scene number. 0 is the chapter's opening frame.
const SCENE = { opener: 0, wordle: 1, connections: 2, strands: 3, "spelling-bee": 4, mini: 5, midi: 6, daily: 7 };

// The rooms chapter-2.riv has so far. Add a game here when its room ships in the .riv. A card for a game that isn't
// built yet still shows its copy, but Rive stays on the room already on screen, so the page never pans to nothing.
const BUILT = new Set(["opener", "wordle", "connections"]);

// The chapter's frames in order, built from the player's stats: the opener, then each game's cards in the
// player's order. Each frame names the scene it shows; a game with several cards has several frames in a row.
// A player who solved fewer than 10 of a game's puzzles gets one community card for that game instead of their own
// cards: mark that frame community: true (the game's Rive lockup is then left out; everything else is the same).
// Names: "opener", "wordle", "connections", "strands", "spelling-bee", "mini", "midi", "daily".
// Example: [{ scene: "opener" }, { scene: "wordle", community: true }, { scene: "connections" }, { scene: "connections" }]
const frames = player.chapterFrames;

import { Rive } from "@rive-app/canvas"; // pin the version you ship

const yig = new Rive({
  src: "chapter-2.riv", // relative to the page; point it at wherever you host the file
  canvas: document.getElementById("yig-stage"),
  stateMachine: "Chapter 2",
  autoplay: true,
  autoBind: true, // binds the "Chapter 2" view model that drives the state machine
  onLoad: () => {
    yig.resizeDrawingSurfaceToCanvas();
    setScene(SCENE.opener);
  },
});

// The file reads scene, direction (1 forward, -1 back) so a room knows which way to leave, and community, which
// leaves out the lockup of the game being entered. Both are set before scene, so the file sees them on the same frame.
function setScene(n, direction = 1, community = false) {
  yig.viewModelInstance.number("direction").value = direction;
  yig.viewModelInstance.boolean("community").value = community;
  yig.viewModelInstance.number("scene").value = n;
}

const INTRO_MS = 3200; // every intro is exactly this long
const PAN_MS = 1650;   // a room change: the rooms' moves run 1.6 s (the pan itself is 0.05 to 1.55 s), plus a few frames
                       // so a held tap never lands on the frame a move hands over to its resting pose
let frame = 0;
let room = "opener";   // the room Rive is showing; a card for a game that isn't built yet leaves it where it is
let introEndsAt = {};  // per game: when its first-visit intro (and its lockup) finishes, in performance.now() time
let pan = { dir: 0, endsAt: 0 }; // the room change on screen: which way the camera is moving, and when it stops
let heldTimer = 0;     // a tap waiting for a pan to end

// Next: call from the tap handler that already advances the stats.
function onTap() {
  move(+1);
}

// Back: call from the back control. On the opener it does nothing.
function onBack() {
  move(-1);
}

// The file can't turn a room around part-way through a move without a snap, so a tap that changes the room
// while a pan is running waits for the pan to end if it is a Back, or a Next that would reverse a Back. A Next
// during a Next pan goes at once, as it always has. Only the last tap of a wait counts.
function move(step) {
  clearTimeout(heldTimer);
  const target = frame + step;
  if (target < 0 || target > frames.length - 1) return;
  const scene = frames[target].scene;
  if (!(scene in SCENE)) throw new Error(`Unknown game "${scene}" in chapterFrames`);
  const built = BUILT.has(scene);
  // Only a built game in a different room moves Rive. The text can change game without the room changing, when
  // the card is for a game that isn't built yet, or comes back from one to the room still on screen.
  const roomChange = built && scene !== room;
  const gameChange = scene !== frames[frame].scene;
  const now = performance.now();
  if (roomChange && pan.endsAt > now && (step < 0 || pan.dir < 0)) {
    heldTimer = setTimeout(() => move(step), pan.endsAt - now);
    return;
  }
  frame = target;
  const firstVisit = roomChange && step > 0 && !(scene in introEndsAt) && scene !== "opener";
  if (roomChange) pan = { dir: step, endsAt: now + PAN_MS };
  if (firstVisit) introEndsAt[scene] = now + INTRO_MS; // a first visit plays the game's intro
  if (built) {
    setScene(SCENE[scene], step, !!frames[frame].community); // the same scene again does nothing, so Rive keeps looping
    room = scene;
  } else {
    console.warn(`chapter-2: "${scene}" isn't built in chapter-2.riv yet; staying on the ${room} room and changing only the copy`);
  }
  showCopy(frame, gameChange, roomChange, firstVisit, step);
}

// What changes on a tap:
//  - the room changes: the old game's icon and text leave at once, and the new game's text and icon arrive when
//    the room has settled: 3.2 s after the tap on a game's first visit (the intro and its lockup), at the end of
//    the move (1.65 s) when the game comes back already built, or when that game's interrupted intro ends, if later.
//  - the game changes but the room doesn't (a game that isn't built yet, or back from one): the old icon and text
//    leave at once as above, and the new ones arrive once the old text has cleared, or when the room's intro ends,
//    if later. The delay is explicit because yig-quick only applies to the text, not the icon.
//  - the room stays (the game's next or previous card): only the text changes, and the icon stays put. The new
//    card arrives right after the old one leaves (yig-quick), or, if the game's intro is still running, when the
//    intro ends, so it never overlaps the lockup. Back moves the text down instead of up (yig-back).
function showCopy(n, gameChange, roomChange, firstVisit, step) {
  const scene = frames[n].scene;
  const back = step < 0;
  const visible = [...document.querySelectorAll(".yig-text:not([hidden]), .yig-icon:not([hidden])")];
  visible.filter((el) => gameChange || !el.classList.contains("yig-icon")).forEach((el) => leave(el, back));

  const next = document.querySelector(`[data-copy-frame="${n}"]`);
  const icon = document.querySelector(`[data-icon-scene="${scene}"]`);
  const now = performance.now();
  const introLeft = Math.max(0, (introEndsAt[room] ?? 0) - now); // the intro of the room on screen, not the card's game
  if (gameChange) {
    let wait = Math.max(clearMs(), introLeft);
    if (roomChange) wait = firstVisit ? null : Math.max(PAN_MS, introLeft); // null: the CSS default, the 3.2 s intro
    if (icon) enter(icon, { delay: wait, back });
    if (next) enter(next, { delay: wait, afterIcon: !!icon, back });
  } else if (next) {
    enter(next, introLeft > 0 ? { delay: introLeft, back } : { quick: true, back });
  }
}

// Copy that has finished arriving leaves (up on Next, down on Back); copy that is still arriving, or still
// waiting to, just goes. Switching it to yig-out would flash it visible for a moment before it left.
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

// How long old copy takes to dissolve, read from the CSS's --yig-clear so the two can't drift apart.
function clearMs() {
  const v = getComputedStyle(document.documentElement).getPropertyValue("--yig-clear").trim();
  const ms = v.endsWith("ms") ? parseFloat(v) : parseFloat(v) * 1000;
  return Number.isFinite(ms) ? ms : 340;   // 340 ms, the v3 value, if the stylesheet hasn't loaded
}

// Take yig-in and yig-out off, force a reflow, then add yig-in, so the CSS animation restarts every time this
// copy shows. Without the reflow the browser sees yig-in already there and plays nothing.
function enter(el, { quick = false, delay = null, afterIcon = false, back = false } = {}) {
  el.classList.remove("yig-in", "yig-out");
  el.classList.toggle("yig-quick", quick);
  el.classList.toggle("yig-after-icon", afterIcon); // first card of a game: its lines start one step after the icon
  el.classList.toggle("yig-back", back);
  if (delay === null) el.style.removeProperty("--yig-delay");
  else el.style.setProperty("--yig-delay", `${delay}ms`);
  el.hidden = false;
  void el.offsetWidth;
  el.classList.add("yig-in");
}

// Exports let the review harness drive this file as-is. A page that inlines the code can drop this line.
export { onTap, onBack, setScene, yig };
