// Reference version from the prototype, written with a state machine input named "Scene".
// The live file binds through a view model; the restructure updates this to match.

// Scene numbers agreed with design. 0 is the chapter's opening frame.
const SCENE = { opener: 0, wordle: 1, connections: 2, strands: 3, spellingBee: 4, mini: 5, midi: 6, crossword: 7 };

// The chapter's frames in order, built from the player's stats. Each frame names the scene it shows.
// Example: [{ scene: "opener" }, { scene: "wordle" }, { scene: "wordle" }, { scene: "connections" }]
const frames = player.chapterFrames;

import { Rive } from "@rive-app/canvas"; // pin the version you ship

const yig = new Rive({
  src: "/yig/chapter-2.riv",
  canvas: document.getElementById("yig-stage"),
  stateMachines: "Chapter 2",
  autoplay: true,
  onLoad: () => {
    yig.resizeDrawingSurfaceToCanvas();
    setScene(SCENE.opener);
  },
});

function setScene(n) {
  yig.stateMachineInputs("Chapter 2").find((i) => i.name === "Scene").value = n;
}

// Call from the tap handler that already advances the stats
let frame = 0;
function onTap() {
  if (frame >= frames.length - 1) return;
  const sameScene = frames[frame + 1].scene === frames[frame].scene;
  frame += 1;
  setScene(SCENE[frames[frame].scene]); // no change in Scene means Rive just keeps looping
  showCopy(frame, sameScene);
}

// Copy for the new frame rises in on its own: after the 3.2 s transition, or right away on the same scene
function showCopy(n, sameScene) {
  const current = document.querySelector(".yig-text:not([hidden])");
  const next = document.querySelector(`[data-copy-frame="${n}"]`);
  if (current) {
    current.classList.add("yig-out");
    setTimeout(() => { current.hidden = true; }, 300);
  }
  if (next) {
    next.hidden = false;
    next.classList.toggle("yig-quick", sameScene);
    next.classList.add("yig-in");
  }
}
