// Review controls for our own harness only. serve.mjs adds this file to the page it serves; index.html does not load
// it, so the engineering example and the handoff never see it.
//
//   http://127.0.0.1:8765/#mini   starts on the card before The Mini, so one tap plays The Mini's intro
//   Replay                        replays the current room's intro (reloads to the card before it, then taps Next)
//
// Names: chapter1 (the empty start room), opener, wordle, connections, strands, spelling-bee, mini, midi, daily (daily is The Crossword), chapter3
// (the Chapter 2 ending: no intro of its own, so #chapter3 is for viewing the backdrop crossfade, not a replay).
const SCENE = { opener: 0, wordle: 1, connections: 2, strands: 3, "spelling-bee": 4, mini: 5, midi: 6, daily: 7, chapter3: 8, chapter1: 9 };
const ALIAS = { crossword: "daily", "the-mini": "mini", "the-midi": "midi", "the-crossword": "daily", spellingbee: "spelling-bee", bee: "spelling-bee", "chapter-3": "chapter3", ending: "chapter3", start: "chapter1", "chapter-1": "chapter1" };
const gameOfScene = (n) => Object.keys(SCENE).find((g) => SCENE[g] === n);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const ex = () => window.yigExample;
const ready = async () => {
  for (let i = 0; i < 300 && !ex()?.yig?.viewModelInstance; i++) await sleep(50);
  return !!ex()?.yig?.viewModelInstance;
};

function hashGame() {
  const name = decodeURIComponent(location.hash.slice(1)).toLowerCase();
  const game = ALIAS[name] ?? name;
  return game in SCENE ? game : null;
}

// Fast-forward to the card before the room, hidden behind a curtain so the skipped rooms are not watched.
async function jumpTo(game, thenPlay) {
  const stage = document.getElementById("stage");
  stage.style.transition = "none";
  stage.style.opacity = "0";
  if (!(await ready())) { stage.style.opacity = ""; return; }
  const first = ex().cards.findIndex((c) => c.game === game);
  if (first > 1) {
    for (let i = 0; i < first - 1; i++) { ex().onTap(); await sleep(60); }
    await sleep(3700); // the last pan (1.65 s) and the intro of the room before (3.2 s) overlap; this clears both
  } else {
    await sleep(600);
  }
  stage.style.transition = "opacity .25s";
  stage.style.opacity = "";
  if (thenPlay && first > 0) ex().onTap();
}

const replay = document.createElement("button");
replay.textContent = "Replay";
replay.title = "Play the current room's intro again";
replay.addEventListener("click", () => {
  const scene = ex()?.yig?.viewModelInstance?.number("scene")?.value ?? 0;
  const game = gameOfScene(scene) ?? "opener";
  sessionStorage.setItem("yigReplay", "1");
  if (location.hash === `#${game}`) location.reload();
  else { location.hash = game; location.reload(); }
});
document.getElementById("restart")?.insertAdjacentElement("afterend", replay);

window.addEventListener("hashchange", () => location.reload());

const game = hashGame();
const play = sessionStorage.getItem("yigReplay") === "1";
sessionStorage.removeItem("yigReplay");
if (game && game !== "chapter1") jumpTo(game, play);
