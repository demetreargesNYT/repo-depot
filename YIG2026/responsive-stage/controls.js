// Steps through the data-driven Subscriber/Registered screens and runs the comparison controls.
const root = document.documentElement;
const screenRoot = document.getElementById("screen-root");
const progressEl = document.querySelector(".progress");
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const label = document.getElementById("step-label");
const overlayToggle = document.getElementById("overlay-toggle");
const deviceSelect = document.getElementById("device-select");
const templateToggle = document.getElementById("template-toggle");
const deviceFrame = document.querySelector(".device-frame");
const deviceLabel = document.querySelector(".device-label");
const minSlider = document.getElementById("min-scale");
const minValue = document.getElementById("min-scale-value");
const minNote = document.getElementById("min-scale-note");

const STEPS = SCREENS.length;
const PROGRESS_SEGMENTS = 26;

// Figma carousel widths (26 segments). Fill proportionally across the whole flow.
const DEFAULT_SEG_WIDTHS = [
  11, 12, 12, 13, 12, 13, 12, 12, 11, 12, 11, 11, 11, 11, 12, 12, 13, 13, 12, 11, 11, 11, 12, 11, 13, 13,
];

function buildProgress() {
  if (!progressEl) return [];
  progressEl.replaceChildren();
  for (const w of DEFAULT_SEG_WIDTHS) {
    const seg = document.createElement("i");
    seg.className = "seg";
    seg.style.setProperty("--w", `${w}px`);
    progressEl.append(seg);
  }
  return [...progressEl.querySelectorAll(".seg")];
}

let segments = buildProgress();

const MAX_SCALE = 1.5;
const FIT_HEIGHT = 812;
const STAGE_W = 1495, STAGE_H = 1067;
let minScale = 0.9;

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function updateScale() {
  const bigFit = Math.min(innerWidth / STAGE_W, innerHeight / STAGE_H);
  const isPhone = innerWidth < 600;
  let scale = 1;
  if (!isPhone) {
    scale = bigFit >= 1 ? Math.min(MAX_SCALE, bigFit) : clamp(innerHeight / FIT_HEIGHT, minScale, 1);
  }
  root.style.setProperty("--scale", scale.toFixed(4));
  resizeRive(scale);
  const crops = minScale >= 1 ? "Never shrinks" : `Crops below ${Math.round(FIT_HEIGHT * minScale)}px tall`;
  const idle = bigFit >= 1 && !isPhone ? " The window is larger than the artboard, so the slider has no effect yet." : "";
  minNote.textContent = `Scale now ${scale.toFixed(2)}x. ${crops}.${idle}`;
}

const riveCanvas = document.getElementById("rive-canvas");
let riveInstance = null;
let lastScale = 1;
function resizeRive(scale = lastScale) {
  lastScale = scale;
  if (riveInstance) riveInstance.resizeDrawingSurfaceToCanvas(Math.min(window.devicePixelRatio || 1, 2) * scale);
}
function startRive() {
  if (!window.rive) { console.warn("Rive runtime failed to load"); return; }
  riveInstance = new rive.Rive({
    src: "assets/2026_yig-test_no-template.riv",
    canvas: riveCanvas,
    artboard: "YIG Test",
    stateMachines: "Scene Loop",
    autoplay: true,
    layout: new rive.Layout({ fit: rive.Fit.Contain, alignment: rive.Alignment.Center }),
    onLoad: () => resizeRive(),
    onLoadError: (e) => console.warn("Rive failed to load the .riv", e),
  });
}

function setMinScale(percent) {
  minScale = clamp(percent, 50, 100) / 100;
  minSlider.value = Math.round(minScale * 100);
  minValue.textContent = `${minSlider.value}%`;
  updateScale();
}

function activeSegmentCount(step) {
  if (!STEPS) return 0;
  return Math.max(1, Math.min(PROGRESS_SEGMENTS, Math.ceil((step / STEPS) * PROGRESS_SEGMENTS)));
}

function showStep(n) {
  if (!STEPS) {
    label.textContent = "0 / 0";
    return;
  }
  const step = Math.min(STEPS, Math.max(1, n));
  const screen = SCREENS[step - 1];
  renderStageScreen(screen, PROTOTYPE_PAYLOAD);
  const lit = activeSegmentCount(step);
  segments.forEach((seg, i) => seg.classList.toggle("is-active", i < lit));
  label.textContent = `${step} / ${STEPS}`;
  prev.disabled = step === 1;
  next.disabled = step === STEPS;
  root.dataset.step = step;
  if (screenRoot) screenRoot.hidden = false;
}

const DEVICES = [
  { id: "macbook-air-1280", group: "Desktop", name: "MacBook Air 1280px", w: 1280, h: 832 },
  { id: "macbook-pro-14-1512", group: "Desktop", name: 'MacBook Pro 14" 1512px', w: 1512, h: 982 },
  { id: "macbook-pro-16-1728", group: "Desktop", name: 'MacBook Pro 16" 1728px', w: 1728, h: 1117 },
  { id: "ipad-mini-744", group: "Tablet", name: "iPad Mini 744px", w: 744, h: 1133 },
  { id: "ipad-pro-834", group: "Tablet", name: "iPad Pro 834px", w: 834, h: 1194 },
  { id: "ipad-pro-1024", group: "Tablet", name: "iPad Pro 1024px", w: 1024, h: 1366 },
  { id: "iphone-se-375", group: "Mobile", name: "iPhone SE \u2013 375px", w: 375, h: 667 },
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

function toggleTemplate(force) {
  const on = document.body.classList.toggle("show-template", force);
  templateToggle.setAttribute("aria-pressed", String(on));
  templateToggle.textContent = `Rive template: ${on ? "On" : "Off"} (T)`;
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
templateToggle.addEventListener("click", () => toggleTemplate());
deviceSelect.addEventListener("change", () => setDevice(deviceSelect.value));
minSlider.addEventListener("input", () => setMinScale(Number(minSlider.value)));
addEventListener("resize", updateScale);

// Stage click advances unless the target is (or is inside) a control that advances / is interactive.
document.querySelector(".stage").addEventListener("click", (e) => {
  if (e.target.closest("button, a, input, select, textarea, [data-advance]")) return;
  showStep(step() + 1);
});

// Primary / skip buttons inside #screen-root advance without the stage handler double-firing.
if (screenRoot) {
  screenRoot.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-advance], .primary-btn, .ad-skip");
    if (!btn) return;
    e.stopPropagation();
    showStep(step() + 1);
  });
}

document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "ArrowRight") showStep(step() + 1);
  else if (e.key === "ArrowLeft") showStep(step() - 1);
  else if (e.key.toLowerCase() === "o") toggleOverlay();
  else if (e.key.toLowerCase() === "t") toggleTemplate();
});

const params = new URLSearchParams(location.search);
showStep(parseInt(params.get("step"), 10) || 1);
setDevice(params.get("device"));
if (params.get("overlay") === "1") toggleOverlay();
if (params.get("template") === "1") toggleTemplate(true);
updateScale();
startRive();
