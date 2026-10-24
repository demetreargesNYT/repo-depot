// Scene numbers agreed with design. 0 is the chapter's opening frame.
const SCENE = { opener: 0, wordle: 1, connections: 2, strands: 3, spellingBee: 4, mini: 5, midi: 6, crossword: 7 };

// The chapter's frames in order, built from the player's stats: the opener, then each game's cards in the
// player's order. Each frame names the scene it shows; a game with several cards has several frames in a row.
// Example: [{ scene: "opener" }, { scene: "wordle" }, { scene: "wordle" }, { scene: "connections" }]
const frames = player.chapterFrames;

import { Rive } from "@rive-app/canvas"; // pin the version you ship

const yig = new Rive({
  src: "/yig/chapter-2.riv",
  canvas: document.getElementById("yig-stage"),
  stateMachine: "Chapter 2",
  autoplay: true,
  autoBind: true, // binds the "Chapter 2" view model that drives the state machine
  onLoad: () => {
    yig.resizeDrawingSurfaceToCanvas();
    setScene(SCENE.opener);
  },
});

function setScene(n) {
  yig.viewModelInstance.number("scene").value = n;
}

// Call from the tap handler that already advances the stats
let frame = 0;
let introEndsAt = 0; // when the game's 3.2 s intro finishes, in performance.now() time
const INTRO_MS = 3200; // every intro is exactly this long
function onTap() {
  if (frame >= frames.length - 1) return;
  const sameScene = frames[frame + 1].scene === frames[frame].scene;
  frame += 1;
  if (!sameScene) introEndsAt = performance.now() + INTRO_MS;
  setScene(SCENE[frames[frame].scene]); // the same scene again does nothing, so Rive keeps looping
  showCopy(frame, sameScene);
}

// What changes on a tap:
//  - the scene changes (a new game): the old game's icon and text leave, the new game's icon pops and its first
//    card rises 3.2 s later, when the Rive intro (and its lockup) is over.
//  - the scene stays (the game's next card): only the text changes. The icon stays put. The new card rises right
//    after the old one leaves (yig-quick), or, if the game's intro is still running, when the intro ends, so it
//    never overlaps the lockup.
function showCopy(n, sameScene) {
  const scene = frames[n].scene;
  const visible = [...document.querySelectorAll(".yig-text:not([hidden]), .yig-icon:not([hidden])")];
  visible.filter((el) => !(sameScene && el.classList.contains("yig-icon"))).forEach(leave);

  const next = document.querySelector(`[data-copy-frame="${n}"]`);
  const icon = document.querySelector(`[data-icon-scene="${scene}"]`);
  if (icon && !sameScene) enter(icon, { delay: null });
  if (next) {
    const waitForIntro = Math.max(0, introEndsAt - performance.now());
    if (sameScene) enter(next, waitForIntro > 0 ? { delay: waitForIntro } : { quick: true });
    else enter(next, { delay: null, afterIcon: !!icon });
  }
}

// Copy that has finished rising lifts out; copy that is still rising, or still waiting to rise, just goes.
// Switching it to yig-out would flash it visible for a moment before it lifted.
function leave(el) {
  const settled = el.getAnimations({ subtree: true }).every((a) => a.playState === "finished");
  if (settled) {
    el.classList.add("yig-out");
    setTimeout(() => { el.hidden = true; }, 300);
  } else {
    el.hidden = true;
  }
}

// Take yig-in and yig-out off, force a reflow, then add yig-in, so the CSS animation restarts every time this
// copy shows. Without the reflow the browser sees yig-in already there and plays nothing.
function enter(el, { quick = false, delay = null, afterIcon = false } = {}) {
  el.classList.remove("yig-in", "yig-out");
  el.classList.toggle("yig-quick", quick);
  el.classList.toggle("yig-after-icon", afterIcon); // first card of a game: its lines start one step after the icon
  if (delay === null) el.style.removeProperty("--yig-delay");
  else el.style.setProperty("--yig-delay", `${delay}ms`);
  el.hidden = false;
  void el.offsetWidth;
  el.classList.add("yig-in");
}

// Exports let the review harness drive this file as-is. A page that inlines the code can drop this line.
export { onTap, setScene, yig };
