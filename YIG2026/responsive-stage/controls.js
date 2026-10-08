// Steps between the five Chapter 1 screens and runs the comparison controls.
const STEPS = 5;
const root = document.documentElement;
const screens = [...document.querySelectorAll(".screen")];
const segments = [...document.querySelectorAll(".seg")];
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const label = document.getElementById("step-label");
const overlayToggle = document.getElementById("overlay-toggle");
const deviceSelect = document.getElementById("device-select");
const deviceFrame = document.querySelector(".device-frame");
const deviceLabel = document.querySelector(".device-label");
const minSlider = document.getElementById("min-scale");
const minValue = document.getElementById("min-scale-value");
const minNote = document.getElementById("min-scale-note");

// Fit to window: grow the stage to fit big windows (capped), and on short windows shrink the whole stage
// (text, nav and art together) so the artboard is visible down to FIT_HEIGHT, but never below minScale (the
// slider): below that window height the bottom of the artboard crops instead. Phone-width windows are never scaled.
const MAX_SCALE = 1.5;
const FIT_HEIGHT = 812;       // bottom of the Figma phone frame
const STAGE_W = 1495, STAGE_H = 1067;   // the Rive artboard
let minScale = 0.9;           // slider; at 90% the 26px headline is about 23px and the 12px label 11px

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function updateScale() {
  const bigFit = Math.min(innerWidth / STAGE_W, innerHeight / STAGE_H);
  const isPhone = innerWidth < 600;
  let scale = 1;
  if (!isPhone) {
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

function showStep(n) {
  const step = Math.min(STEPS, Math.max(1, n));
  screens.forEach((s) => { s.hidden = Number(s.dataset.step) !== step; });
  segments.forEach((seg, i) => seg.classList.toggle("is-active", i < step));
  label.textContent = `${step} / ${STEPS}`;
  prev.disabled = step === 1;
  next.disabled = step === STEPS;
  root.dataset.step = step;
}

// Device frames from the Figma overlay sheets (Desktop 60:1756, Tablet 60:1806, Mobile 60:1781): width x height in px.
const DEVICES = [
  { id: "macbook-air-1280", group: "Desktop", name: "MacBook Air 1280px", w: 1280, h: 832 },
  { id: "macbook-pro-14-1512", group: "Desktop", name: 'MacBook Pro 14" 1512px', w: 1512, h: 982 },
  { id: "macbook-pro-16-1728", group: "Desktop", name: 'MacBook Pro 16" 1728px', w: 1728, h: 1117 },
  { id: "ipad-mini-744", group: "Tablet", name: "iPad Mini 744px", w: 744, h: 1133 },
  { id: "ipad-pro-834", group: "Tablet", name: "iPad Pro 834px", w: 834, h: 1194 },
  { id: "ipad-pro-1024", group: "Tablet", name: "iPad Pro 1024px", w: 1024, h: 1366 },
  { id: "iphone-14-375", group: "Mobile", name: "iPhone 14 \u2013 375px", w: 375, h: 812 },
  { id: "iphone-13-14-390", group: "Mobile", name: "iPhone 13 & 14 \u2013 390px", w: 390, h: 844 },
  { id: "iphone-17-402", group: "Mobile", name: "iPhone 17 \u2013 402px", w: 402, h: 874 },
  { id: "iphone-16-plus-430", group: "Mobile", name: "iPhone 16 Plus \u2013 430px", w: 430, h: 932 },
  { id: "iphone-16-17-pro-max-440", group: "Mobile", name: "iPhone 16 & 17 Pro Max \u2013 440px", w: 440, h: 956 },
  { id: "iphone-duo-closed-466", group: "Mobile", name: "iPhone Duo Closed", w: 466, h: 678 },
  { id: "iphone-duo-open-890", group: "Mobile", name: "iPhone Duo Open", w: 890, h: 626 },
];
const DEFAULT_DEVICE = "iphone-14-375";

for (const group of ["Desktop", "Tablet", "Mobile"]) {
  const optgroup = document.createElement("optgroup");
  optgroup.label = group;
  for (const d of DEVICES.filter((x) => x.group === group)) {
    const option = document.createElement("option");
    option.value = d.id;
    option.textContent = `${d.name} (${d.w}\u00d7${d.h})`;
    optgroup.append(option);
  }
  deviceSelect.append(optgroup);
}

function setDevice(id) {
  const d = DEVICES.find((x) => x.id === id) || DEVICES.find((x) => x.id === DEFAULT_DEVICE);
  deviceSelect.value = d.id;
  deviceFrame.style.setProperty("--device-w", `${d.w}px`);
  deviceFrame.style.setProperty("--device-h", `${d.h}px`);
  deviceLabel.textContent = `${d.name} \u00b7 ${d.w}\u00d7${d.h}`;
}

function toggleOverlay() {
  const on = document.body.classList.toggle("show-overlay");
  overlayToggle.setAttribute("aria-pressed", String(on));
  overlayToggle.textContent = `Overlay: ${on ? "On" : "Off"} (O)`;
}

const step = () => Number(root.dataset.step);
prev.addEventListener("click", () => showStep(step() - 1));
next.addEventListener("click", () => showStep(step() + 1));
overlayToggle.addEventListener("click", toggleOverlay);
deviceSelect.addEventListener("change", () => setDevice(deviceSelect.value));
minSlider.addEventListener("input", () => setMinScale(Number(minSlider.value)));
addEventListener("resize", updateScale);
document.querySelector(".stage").addEventListener("click", (e) => {
  if (!e.target.closest("button")) showStep(step() + 1);
});
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "ArrowRight") showStep(step() + 1);
  else if (e.key === "ArrowLeft") showStep(step() - 1);
  else if (e.key.toLowerCase() === "o") toggleOverlay();
});

// ?step=3&overlay=1&device=ipad-pro-1024&min=65 sets the screen, overlay, device and Min scale, for repeatable screenshots.
const params = new URLSearchParams(location.search);
showStep(parseInt(params.get("step"), 10) || 1);
setDevice(params.get("device"));
if (params.get("overlay") === "1") toggleOverlay();
updateScale();
