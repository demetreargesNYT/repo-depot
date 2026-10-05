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
document.querySelector(".stage").addEventListener("click", (e) => {
  if (!e.target.closest("button")) showStep(step() + 1);
});
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "ArrowRight") showStep(step() + 1);
  else if (e.key === "ArrowLeft") showStep(step() - 1);
  else if (e.key.toLowerCase() === "m") layoutToggle.click();
  else if (e.key.toLowerCase() === "o") toggleOverlay();
});

// ?layout=large&step=3 sets both, for repeatable screenshots.
const params = new URLSearchParams(location.search);
setLayout(params.get("layout") === "large" ? "large" : "card");
showStep(parseInt(params.get("step"), 10) || 1);
if (params.get("overlay") === "1") toggleOverlay();
