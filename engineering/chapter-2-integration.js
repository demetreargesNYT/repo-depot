// Scene numbers agreed with design. 0 is the chapter's opening frame.
const SCENE = { opener: 0, wordle: 1, connections: 2, strands: 3, spellingBee: 4, mini: 5, midi: 6, crossword: 7 };

// The chapter's frames in order, built from the player's stats: the opener, then each game once, in the
// player's order. Each frame names the scene it shows.
// Example: [{ scene: "opener" }, { scene: "wordle" }, { scene: "connections" }]
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
function onTap() {
  if (frame >= frames.length - 1) return;
  frame += 1;
  setScene(SCENE[frames[frame].scene]);
  showCopy(frame);
}

// The old copy goes at once; the new copy rises on its own 3.2 s after the tap (the CSS delay)
function showCopy(n) {
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
    next.hidden = false;
    void next.offsetWidth;
    next.classList.add("yig-in");
  }
}

// Exports let the review harness drive this file as-is. A page that inlines the code can drop this line.
export { onTap, setScene, yig };
