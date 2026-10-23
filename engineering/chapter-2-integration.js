// Game numbers agreed with design
const GAME = { wordle: 1, connections: 2, strands: 3, spellingBee: 4, mini: 5, midi: 6, crossword: 7 };

import { Rive } from "@rive-app/canvas"; // pin the version you ship

const yig = new Rive({
  src: "/yig/chapter-2.riv",
  canvas: document.getElementById("yig-stage"),
  stateMachines: "Chapter 2",
  autoplay: true,
  autoBind: true, // binds the "Chapter 2" view model that drives the state machine
  onLoad: () => {
    yig.resizeDrawingSurfaceToCanvas();
    setProp("game", GAME[player.topGame]); // once, from the player's stats
    setProp("frame", 1);
  },
});

function setProp(name, value) {
  yig.viewModelInstance.number(name).value = value;
}

// Call from the tap handler that already advances the stats
let frame = 1;
function onTap() {
  frame += 1;
  setProp("frame", frame);
  showCopy(frame);
}

// Copy for the new frame rises in on its own after the CSS delay
function showCopy(n) {
  const current = document.querySelector(".yig-text:not([hidden])");
  const next = document.querySelector(`[data-copy-frame="${n}"]`);
  if (current) {
    current.classList.add("yig-out");
    setTimeout(() => { current.hidden = true; }, 300);
  }
  if (next) {
    next.hidden = false;
    next.classList.add("yig-in");
  }
}
