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
const minSlider = document.getElementById("min-scale");
const minValue = document.getElementById("min-scale-value");
const minNote = document.getElementById("min-scale-note");

// Fit modes. All of them grow the stage to fit big windows (capped), and leave phones alone.
//   off: never shrink; short windows crop the bottom of the artboard
//   all: shrink the whole stage (text, nav and art) so the artboard is visible down to FIT_HEIGHT
//   art: shrink only the art layer, toward the top; header and text keep full size, so the art can run into the text
// Neither shrinks below minScale (the slider): below that window height the bottom of the artboard crops instead.
const MAX_SCALE = 1.5;
const FIT_HEIGHT = 812;       // bottom of the Figma phone frame
const STAGE_SIZE = { card: [1495, 1067], large: [2555, 1440] };
const FIT_MODES = ["all", "art", "off"];
const FIT_LABELS = { all: "All", art: "Art only", off: "Off" };
let fit = "all";
let minScale = 0.75;          // slider; at 75% the 26px headline is about 19px and the 12px label 9px

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function updateScale() {
  const [w, h] = STAGE_SIZE[root.dataset.layout];
  const bigFit = Math.min(innerWidth / w, innerHeight / h);
  const isPhone = innerWidth < 600;
  let scale = 1, artScale = 1;
  if (fit !== "off" && !isPhone) {
    if (bigFit >= 1) {
      scale = root.dataset.layout === "card" ? Math.min(MAX_SCALE, bigFit) : 1;
    } else if (fit === "all") {
      scale = clamp(innerHeight / FIT_HEIGHT, minScale, 1);
    } else {
      artScale = clamp(innerHeight / FIT_HEIGHT, minScale, 1);
    }
  }
  root.style.setProperty("--scale", scale.toFixed(4));
  root.style.setProperty("--art-scale", artScale.toFixed(4));
}

function setMinScale(percent) {
  minScale = clamp(percent, 50, 100) / 100;
  minSlider.value = Math.round(minScale * 100);
  minValue.textContent = `${minSlider.value}%`;
  minNote.textContent = minScale >= 1 ? "Never shrinks" : `Crops below ${Math.round(FIT_HEIGHT * minScale)}px tall`;
  updateScale();
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
minSlider.addEventListener("input", () => setMinScale(Number(minSlider.value)));
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

// ?layout=large&step=3&fit=art&min=65 sets all four, for repeatable screenshots. ?scale=0 is the old name for fit=off.
const params = new URLSearchParams(location.search);
setLayout(params.get("layout") === "large" ? "large" : "card");
showStep(parseInt(params.get("step"), 10) || 1);
if (params.get("overlay") === "1") toggleOverlay();
const fitParam = params.get("fit") || (params.get("scale") === "0" ? "off" : "all");
setMinScale(parseInt(params.get("min"), 10) || 75);
setFit(FIT_MODES.includes(fitParam) ? fitParam : "all");
