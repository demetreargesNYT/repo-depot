// Steps between the five Chapter 1 screens and runs the comparison controls.
const STEPS = 5;
const root = document.documentElement;
const screens = [...document.querySelectorAll(".screen")];
const segments = [...document.querySelectorAll(".seg")];
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const label = document.getElementById("step-label");
const overlayToggle = document.getElementById("overlay-toggle");
const scaleToggle = document.getElementById("scale-toggle");
const minSlider = document.getElementById("min-scale");
const minValue = document.getElementById("min-scale-value");
const minNote = document.getElementById("min-scale-note");

// Fit to window. On: grow the stage to fit big windows (capped), and on short windows shrink the whole stage
// (text, nav and art together) so the artboard is visible down to FIT_HEIGHT, but never below minScale (the
// slider): below that window height the bottom of the artboard crops instead. Off: 1:1, always cropped.
// Phone-width windows are never scaled.
const MAX_SCALE = 1.5;
const FIT_HEIGHT = 812;       // bottom of the Figma phone frame
const STAGE_W = 1495, STAGE_H = 1067;   // the Rive artboard
let fit = true;
let minScale = 0.75;          // slider; at 75% the 26px headline is about 19px and the 12px label 9px

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function updateScale() {
  const bigFit = Math.min(innerWidth / STAGE_W, innerHeight / STAGE_H);
  const isPhone = innerWidth < 600;
  let scale = 1;
  if (fit && !isPhone) {
    scale = bigFit >= 1 ? Math.min(MAX_SCALE, bigFit) : clamp(innerHeight / FIT_HEIGHT, minScale, 1);
  }
  root.style.setProperty("--scale", scale.toFixed(4));
  const crops = minScale >= 1 ? "Never shrinks" : `Crops below ${Math.round(FIT_HEIGHT * minScale)}px tall`;
  const idle = bigFit >= 1 && !isPhone ? " The window is larger than the artboard, so the slider has no effect yet." : "";
  minNote.textContent = `Scale now ${scale.toFixed(2)}x. ${crops}.${idle}`;
}

function setMinScale(percent) {
  minScale = clamp(percent, 50, 100) / 100;
  minSlider.value = Math.round(minScale * 100);
  minValue.textContent = `${minSlider.value}%`;
  updateScale();
}

function setFit(on) {
  fit = on;
  scaleToggle.textContent = `Fit to window: ${on ? "On" : "Off"} (S)`;
  scaleToggle.setAttribute("aria-pressed", String(on));
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

function toggleOverlay() {
  const on = document.body.classList.toggle("show-overlay");
  overlayToggle.setAttribute("aria-pressed", String(on));
}

const step = () => Number(root.dataset.step);
prev.addEventListener("click", () => showStep(step() - 1));
next.addEventListener("click", () => showStep(step() + 1));
overlayToggle.addEventListener("click", toggleOverlay);
minSlider.addEventListener("input", () => setMinScale(Number(minSlider.value)));
scaleToggle.addEventListener("click", () => setFit(!fit));
addEventListener("resize", updateScale);
document.querySelector(".stage").addEventListener("click", (e) => {
  if (!e.target.closest("button")) showStep(step() + 1);
});
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "ArrowRight") showStep(step() + 1);
  else if (e.key === "ArrowLeft") showStep(step() - 1);
  else if (e.key.toLowerCase() === "o") toggleOverlay();
  else if (e.key.toLowerCase() === "s") scaleToggle.click();
});

// ?step=3&fit=off&min=65 sets the screen and the fit settings, for repeatable screenshots.
const params = new URLSearchParams(location.search);
showStep(parseInt(params.get("step"), 10) || 1);
if (params.get("overlay") === "1") toggleOverlay();
setFit(params.get("fit") !== "off");
