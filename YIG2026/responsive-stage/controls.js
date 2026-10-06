// Steps between the five Chapter 1 screens and toggles the two comparison aids.
const STEPS = 5;
const root = document.documentElement;
const screens = [...document.querySelectorAll(".screen")];
const segments = [...document.querySelectorAll(".seg")];
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const label = document.getElementById("step-label");
const layoutToggle = document.getElementById("layout-toggle");
const overlayToggle = document.getElementById("overlay-toggle");
const scaleToggle = document.getElementById("scale-toggle");

// Fit modes. All of them grow the stage to fit big windows (capped), and leave phones alone.
//   off: never shrink; short windows crop the bottom of the artboard
//   all: shrink the whole stage (text, nav and art) so the artboard is visible down to FIT_HEIGHT
//   art: shrink only the art layer; header and text keep full size, but their position relative to the art shifts
const MAX_SCALE = 1.5;
const FIT_HEIGHT = 812;       // bottom of the Figma phone frame
const MIN_SCALE_ALL = 0.75;   // keeps the 26px headline at about 19px
const MIN_SCALE_ART = 0.4;
const STAGE_SIZE = { card: [1495, 1067], large: [2555, 1440] };
const FIT_MODES = ["all", "art", "off"];
const FIT_LABELS = { all: "All", art: "Art only", off: "Off" };
let fit = "all";

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function updateScale() {
  const [w, h] = STAGE_SIZE[root.dataset.layout];
  const bigFit = Math.min(innerWidth / w, innerHeight / h);
  const isPhone = innerWidth < 600;
  let scale = 1, artScale = 1, artY = 0;
  if (fit !== "off" && !isPhone) {
    if (bigFit >= 1) {
      scale = root.dataset.layout === "card" ? Math.min(MAX_SCALE, bigFit) : 1;
    } else if (fit === "all") {
      scale = clamp(innerHeight / FIT_HEIGHT, MIN_SCALE_ALL, 1);
    } else {
      artScale = clamp(innerHeight / FIT_HEIGHT, MIN_SCALE_ART, 1);
      // Anchor only while shrinking: y = FIT_HEIGHT of the art lands on the window bottom.
      if (artScale < 1) artY = innerHeight - FIT_HEIGHT * artScale;
    }
  }
  root.style.setProperty("--scale", scale.toFixed(4));
  root.style.setProperty("--art-scale", artScale.toFixed(4));
  root.style.setProperty("--art-y", `${artY.toFixed(1)}px`);
}

function setFit(mode) {
  fit = mode;
  scaleToggle.textContent = `Fit: ${FIT_LABELS[mode]} (S)`;
  updateScale();
}

function showStep(n) {
  const step = Math.min(STEPS, Math.max(1, n));
  screens.forEach((s) => { s.hidden = Number(s.dataset.step) !== step; });
  segments.forEach((seg, i) => seg.classList.toggle("is-active", i < step));
  label.textContent = `${step} / ${STEPS}`;
  prev.disabled = step === 1;
  next.disabled = step === STEPS;
  root.dataset.step = step;
}

function setLayout(mode) {
  root.dataset.layout = mode;
  layoutToggle.textContent = `Layout: ${mode === "card" ? "Card" : "Large"} (M)`;
  updateScale();
}

function toggleOverlay() {
  const on = document.body.classList.toggle("show-overlay");
  overlayToggle.setAttribute("aria-pressed", String(on));
}

const step = () => Number(root.dataset.step);
prev.addEventListener("click", () => showStep(step() - 1));
next.addEventListener("click", () => showStep(step() + 1));
layoutToggle.addEventListener("click", () => setLayout(root.dataset.layout === "card" ? "large" : "card"));
overlayToggle.addEventListener("click", toggleOverlay);
scaleToggle.addEventListener("click", () => setFit(FIT_MODES[(FIT_MODES.indexOf(fit) + 1) % FIT_MODES.length]));
addEventListener("resize", updateScale);
document.querySelector(".stage").addEventListener("click", (e) => {
  if (!e.target.closest("button")) showStep(step() + 1);
});
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "ArrowRight") showStep(step() + 1);
  else if (e.key === "ArrowLeft") showStep(step() - 1);
  else if (e.key.toLowerCase() === "m") layoutToggle.click();
  else if (e.key.toLowerCase() === "o") toggleOverlay();
  else if (e.key.toLowerCase() === "s") scaleToggle.click();
});

// ?layout=large&step=3&fit=art sets all three, for repeatable screenshots. ?scale=0 is the old name for fit=off.
const params = new URLSearchParams(location.search);
setLayout(params.get("layout") === "large" ? "large" : "card");
showStep(parseInt(params.get("step"), 10) || 1);
if (params.get("overlay") === "1") toggleOverlay();
const fitParam = params.get("fit") || (params.get("scale") === "0" ? "off" : "all");
setFit(FIT_MODES.includes(fitParam) ? fitParam : "all");
