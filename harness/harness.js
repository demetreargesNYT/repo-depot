// Review harness: plays the chapter's real built .riv, driven by engineering's own integration file.
// Nothing here stands in for Rive or for engineering's code: the file is imported untouched and must export
// onTap, setScene and yig.

const $ = (id) => document.getElementById(id);
const rive = window.rive;
// The readout below listens for state changes to show the playing state's name. The runtime flags that as
// deprecated; this page is a review tool, not engineering's code, so it is silenced here only.
rive.Rive.suppressDeprecationWarnings = ["state-change-events"];
rive.RuntimeLoader.setWasmUrl("/vendor/rive/rive.wasm"); // the pinned local runtime, never a CDN

const LABEL = { opener: "Opener", wordle: "Wordle", connections: "Connections" };
const ORDERS = { wc: ["wordle", "connections"], cw: ["connections", "wordle"] };
const SCENE_NUM = { opener: 0, wordle: 1, connections: 2 };

let copyTemplate = "";
let state = { mod: null, frames: [], at: 0, scenePropStyle: null, source: "", timer: null };

async function boot() {
  clearInterval(state.timer);
  $("err").hidden = true;
  state.mod?.yig?.cleanup?.();

  // fresh canvas and fresh copy every run, so nothing carries over from the last one
  const old = $("yig-stage");
  const canvas = old.cloneNode(false);
  old.replaceWith(canvas);
  $("overlay").innerHTML = copyTemplate;

  const info = await (await fetch("/api/riv")).json();
  $("ro-file").textContent = `${info.file} · ${info.bytes.toLocaleString()} bytes`;
  $("filelabel").textContent = info.file.split("/").pop();

  const source = await (await fetch("/engineering/chapter-2-integration.js", { cache: "no-store" })).text();
  state.source = source;
  // The scene-reference style sets a "Scene" value from a frame list; the live style sets game and frame.
  const usesFrameList = /chapterFrames/.test(source);
  state.scenePropStyle = usesFrameList ? "scene" : "game-frame";
  $("ro-int").textContent = usesFrameList ? "chapter-2-integration.js (frame list, scene)" : "chapter-2-integration.js (game + frame)";

  const [first, second] = ORDERS[$("order").value];
  const frames = usesFrameList
    ? [{ scene: "opener" }, { scene: first, step: 1 }, { scene: first, step: 2 }, { scene: second, step: 1 }]
    : [{ scene: "opener" }, { scene: first, step: 1 }];
  state.frames = frames;
  state.at = 0;

  // the integration code reads these globals, the way engineering's page will provide them
  window.player = { topGame: first, chapterFrames: frames };

  // number the copy blocks the way the integration file expects: the live style counts frames from 1
  const base = usesFrameList ? 0 : 1;
  frames.forEach((f, i) => {
    const el = $("overlay").querySelector(`[data-copy-scene="${f.scene}"][data-copy-step="${f.step || 1}"]`);
    if (el) el.dataset.copyFrame = String(i + base);
  });
  $("overlay").querySelectorAll(".yig-text:not([data-copy-frame]):not([data-copy-scene='opener'])").forEach((el) => el.remove());

  const url = URL.createObjectURL(new Blob([source], { type: "text/javascript" })); // the file as engineering wrote it
  try {
    state.mod = await import(url);
  } catch (e) {
    showError("The integration file failed to run:\n" + (e.stack || e));
    return;
  }
  state.mod.yig.on(rive.EventType.StateChange, (e) => { $("ro-state").textContent = [].concat(e.data).join(", ") || "…"; });
  state.mod.yig.on(rive.EventType.LoadError, (e) => showError("Rive could not load the file: " + JSON.stringify(e.data)));

  renderFrames();
  state.timer = setInterval(readVm, 120);
  $("tap").disabled = frames.length < 2;
  window.__harness = { state, tap, boot, readVm };
}

function readVm() {
  const vm = state.mod?.yig?.viewModelInstance;
  if (!vm) { $("ro-vm").textContent = "not bound yet"; return; }
  const parts = ["scene", "game", "frame"].map((n) => [n, vm.number(n)]).filter(([, p]) => p).map(([n, p]) => `${n} ${p.value}`);
  $("ro-vm").textContent = parts.join(" · ") || "no number properties found";
  syncSceneButtons(vm);
}

function tap() {
  if (state.at >= state.frames.length - 1) return;
  state.mod.onTap();
  state.at += 1;
  renderFrames();
  $("tap").disabled = state.at >= state.frames.length - 1;
}

function renderFrames() {
  $("framelist").innerHTML = state.frames
    .map((f, i) => `<li class="${i === state.at ? "now" : ""}"><b>${i + 1}</b>${LABEL[f.scene]}${i > 0 && f.scene === state.frames[i - 1].scene ? " · same scene" : ""}</li>`)
    .join("");
  $("framenote").textContent = state.scenePropStyle === "scene"
    ? "Frames come from the player's data: opener, the first game twice, then the second game."
    : "This integration file handles one jump: opener to the player's top game (game + frame). Longer chains arrive with the scene restructure.";
  $("framenote").className = "note";
}

// A button per scene value. They set the file's number directly, which is a shortcut for poking one value;
// the Tap button is the real path, because it runs engineering's own code.
function buildSceneButtons() {
  $("scenes").innerHTML = Object.entries(SCENE_NUM)
    .map(([k, n]) => `<button data-scene="${n}" title="${LABEL[k]}">${n} ${LABEL[k]}</button>`).join("");
  $("scenes").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b || b.disabled) return;
    const n = Number(b.dataset.scene), vm = state.mod?.yig?.viewModelInstance;
    if (!vm) return;
    if (vm.number("scene")) { vm.number("scene").value = n; return; }
    if (n > 0) { vm.number("game").value = n; vm.number("frame").value = 2; }
  });
}
function syncSceneButtons(vm) {
  const hasScene = !!vm.number("scene");
  $("scenes").querySelectorAll("button").forEach((b) => {
    const n = Number(b.dataset.scene);
    b.disabled = !hasScene && n === 0;
    b.title = hasScene ? `Set scene to ${n}` : n === 0 ? "This file has no scene value yet; use Restart to see the opener" : `Sets game ${n} and frame 2 (this file has game + frame)`;
    b.setAttribute("aria-pressed", String(hasScene && vm.number("scene").value === n));
  });
}

function setView(mode) {
  $("stage").className = "stage " + mode;
  $("v-full").setAttribute("aria-pressed", String(mode === "full"));
  $("v-phone").setAttribute("aria-pressed", String(mode === "phone"));
  // the canvas changes size, so the drawing surface has to follow
  requestAnimationFrame(() => state.mod?.yig?.resizeDrawingSurfaceToCanvas?.());
}

function showError(msg) {
  $("err").textContent = msg; $("err").hidden = false;
}

(async function init() {
  $("rtlabel").textContent = "2.45.0";
  copyTemplate = await (await fetch("/copy.html")).text();
  buildSceneButtons();
  $("tap").addEventListener("click", tap);
  $("restart").addEventListener("click", boot);
  $("order").addEventListener("change", boot);
  $("v-full").addEventListener("click", () => setView("full"));
  $("v-phone").addEventListener("click", () => setView("phone"));
  window.addEventListener("resize", () => state.mod?.yig?.resizeDrawingSurfaceToCanvas?.());
  await boot();
})();
