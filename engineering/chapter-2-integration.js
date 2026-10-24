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

// The old copy goes at once. The new copy rises on its own: 3.2 s after a tap that changes the scene. A tap
// that only moves to the game's next card waits just 300 ms (yig-quick), unless the game's intro is still
// running: then the copy waits until the intro ends, so it never overlaps the lockup.
function showCopy(n, sameScene) {
  const current = document.querySelector(".yig-text:not([hidden])");
  const next = document.querySelector(`[data-copy-frame="${n}"]`);
  if (current) {
    // Copy that is still rising, or still waiting to rise, just goes. Switching it to yig-out would flash it
    // visible for a moment before it lifted.
    const settled = current.getAnimations({ subtree: true }).every((a) => a.playState === "finished");
    if (settled) {
      current.classList.add("yig-out");
      setTimeout(() => { current.hidden = true; }, 300);
    } else {
      current.hidden = true;
    }
  }
  if (next) {
    // Take both classes off, force a reflow, then add yig-in, so the CSS animation restarts every time this
    // copy shows. Without the reflow the browser sees yig-in already there and plays nothing.
    next.classList.remove("yig-in", "yig-out");
    const waitForIntro = Math.max(0, introEndsAt - performance.now());
    if (sameScene && waitForIntro > 0) {
      next.style.setProperty("--yig-delay", `${waitForIntro}ms`); // the rest of the intro
      next.classList.remove("yig-quick");
    } else {
      next.style.removeProperty("--yig-delay");
      next.classList.toggle("yig-quick", sameScene);
    }
    next.hidden = false;
    void next.offsetWidth;
    next.classList.add("yig-in");
  }
}

// Exports let the review harness drive this file as-is. A page that inlines the code can drop this line.
export { onTap, setScene, yig };
