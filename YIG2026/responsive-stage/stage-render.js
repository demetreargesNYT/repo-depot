"use strict";

// Renders SCREENS[].lines into the responsive-stage lockup using the same placeholder / style
// conventions as YIG2026/renderer.js, adapted for stage CSS and local icon assets.

const STAGE_GAMES = {
  wordle: { name: "Wordle", icon: "assets/wordle-icon.svg" },
  connections: {
    name: "Connections",
    icon: "assets/connections-icon.svg",
    glyph: "assets/connections-glyph.svg",
  },
  spelling_bee: { name: "Spelling Bee", icon: "../icons/spelling_bee.svg" },
  midi: { name: "The Midi", icon: "../icons/midi.svg" },
  mini: { name: "The Mini", icon: "../icons/mini.svg" },
  crossword: { name: "The Crossword", icon: "../icons/crossword.svg" },
  strands: { name: "Strands", icon: "../icons/strands.svg" },
};

const STAGE_TEXT_STYLES = [
  "headline", "headline-strong", "display", "stat", "body", "label", "label-bold", "quote",
];

function stageGet(source, path) {
  return String(path)
    .replace(/\[(\d+)\]/g, ".$1")
    .split(".")
    .filter(Boolean)
    .reduce((value, key) => (value == null ? undefined : value[key]), source);
}

function stageFormat(value) {
  return typeof value === "number"
    ? value.toLocaleString("en-US", { maximumFractionDigits: 1 })
    : String(value);
}

function stageFill(template, scope, raw = false) {
  return String(template ?? "")
    .replace(/\{([^}]+)\}/g, (_, path) => {
      const value = stageGet(scope, path.trim());
      if (value == null) {
        console.warn(`Unresolved placeholder {${path}}`);
        return "";
      }
      if (raw) return String(value);
      if (typeof value === "string" && Object.hasOwn(STAGE_GAMES, value)) {
        return STAGE_GAMES[value].name;
      }
      return stageFormat(value);
    })
    .trim();
}

function stageEl(tag, className, text, children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  if (children) node.append(...children);
  return node;
}

function renderStageText(style, value, scope) {
  const text = stageFill(value, scope);
  // Preserve intentional line breaks from Figma / screen defs (e.g. "You first puzzle of\nthe year was").
  const node = stageEl("p", style);
  const parts = text.split("\n");
  parts.forEach((part, i) => {
    if (i) node.appendChild(document.createElement("br"));
    node.appendChild(document.createTextNode(part));
  });
  return node;
}

function renderStageIcon(value, scope) {
  const id = stageFill(value, scope, true);
  const game = STAGE_GAMES[id];
  if (!game) {
    const missing = stageEl("div", "game-icon game-icon-missing");
    missing.appendChild(stageEl("span", "game-icon-label", id || "no game"));
    return missing;
  }
  const img = stageEl("img", "game-icon");
  img.src = game.icon;
  img.alt = "";
  return img;
}

// Connections (and any future stacked glyph) as authored in Chapter 1 Figma.
function renderStageIconStack(value, scope) {
  const id = stageFill(value, scope, true);
  const game = STAGE_GAMES[id];
  if (!game) return renderStageIcon(value, scope);
  const stack = stageEl("div", "game-icon game-icon-stack");
  const base = stageEl("img");
  base.src = game.icon;
  base.alt = "";
  stack.appendChild(base);
  if (game.glyph) {
    const inset = stageEl("span", "inset");
    inset.style.inset = "0.07%";
    const glyph = stageEl("img");
    glyph.src = game.glyph;
    glyph.alt = "";
    inset.appendChild(glyph);
    stack.appendChild(inset);
  }
  return stack;
}

function renderStageLine(line, scope) {
  const [style, value] = Object.entries(line)[0] || [];
  if (style === undefined) return null;
  if (style === "game-icon") return renderStageIcon(value, scope);
  if (style === "game-icon-stack") return renderStageIconStack(value, scope);
  if (STAGE_TEXT_STYLES.includes(style)) return renderStageText(style, value, scope);
  console.warn(`Unknown stage line style "${style}"`);
  return null;
}

function applyLockup(lockupEl, lockup) {
  lockupEl.style.top = lockup && lockup.top != null ? `${lockup.top}px` : "";
  lockupEl.style.height = lockup && lockup.height != null ? `${lockup.height}px` : "";
  lockupEl.style.justifyContent = (lockup && lockup.justifyContent) || "";
}

// Mount one screen's lines into #screen-root. Shared Rive canvas / nav stay outside.
function renderStageScreen(screen, scope) {
  const root = document.getElementById("screen-root");
  if (!root || !screen) return;
  root.dataset.screenId = screen.id || "";
  root.setAttribute("aria-label", screen.label || "");
  const phone = stageEl("div", "phone");
  const lockup = stageEl("div", "lockup");
  applyLockup(lockup, screen.lockup);
  for (const line of screen.lines || []) {
    const node = renderStageLine(line, scope);
    if (node) lockup.appendChild(node);
  }
  phone.appendChild(lockup);
  root.replaceChildren(phone);
}
