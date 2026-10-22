"use strict";

// Renders SCREENS into the responsive-stage lockup using renderer-style { style: value } lines.

const STAGE_GAMES = {
  wordle: { name: "Wordle", icon: "assets/wordle-icon.svg" },
  connections: {
    name: "Connections",
    icon: "assets/connections-icon.svg",
    glyph: "assets/connections-glyph.svg",
  },
  spelling_bee: {
    name: "Spelling Bee",
    icon: "assets/spelling-bee-icon.svg",
    iconLarge: "../icons/spelling_bee.svg",
  },
  midi: { name: "The Midi", icon: "../icons/midi.svg" },
  mini: { name: "The Mini", icon: "../icons/mini.svg" },
  crossword: { name: "The Crossword", icon: "../icons/crossword.svg" },
  strands: { name: "Strands", icon: "../icons/strands.svg" },
};

const CONNECTIONS_COLORS = ["yellow", "green", "blue", "purple"];

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
  const node = stageEl("p", style);
  const parts = text.split("\n");
  parts.forEach((part, i) => {
    if (i) node.appendChild(document.createElement("br"));
    // **text** marks an inline emphasis run (e.g. the game name in a headline).
    part.split(/\*\*(.+?)\*\*/).forEach((run, j) => {
      if (!run) return;
      node.appendChild(j % 2 ? stageEl("strong", "", run) : document.createTextNode(run));
    });
  });
  return node;
}

function renderStageImage(line, scope) {
  const img = stageEl("img", "stage-image");
  img.src = stageFill(line.image, scope, true);
  img.alt = line.alt || "";
  if (line.width != null) img.style.width = `${line.width}px`;
  if (line.height != null) img.style.height = `${line.height}px`;
  return img;
}

function renderWordleRow(word, state) {
  const row = stageEl("div", "wordle-row");
  for (const letter of String(word)) {
    row.appendChild(stageEl("span", `wordle-row-tile wordle-row-tile-${state}`, letter));
  }
  return row;
}

function renderWordleRows(line, scope) {
  const state = line.state === "correct" ? "correct" : "empty";
  const words = (Array.isArray(line["wordle-row"]) ? line["wordle-row"] : [line["wordle-row"]])
    .map((word) => stageFill(word, scope, true));
  if (words.length === 1) return renderWordleRow(words[0], state);
  const stack = stageEl("div", "wordle-rows");
  for (const word of words) stack.appendChild(renderWordleRow(word, state));
  return stack;
}

function renderHoneycomb(value, scope) {
  const wrap = stageEl("div", "honeycomb");
  const img = stageEl("img", "honeycomb-art");
  img.src = "assets/spelling-bee-honeycomb.svg";
  img.alt = "";
  wrap.append(img, stageEl("span", "honeycomb-word", stageFill(value, scope)));
  return wrap;
}

function renderStageIcon(value, scope, size) {
  const id = stageFill(value, scope, true);
  const game = STAGE_GAMES[id];
  if (!game) {
    const missing = stageEl("div", "game-icon game-icon-missing");
    missing.appendChild(stageEl("span", "game-icon-label", id || "no game"));
    return missing;
  }
  const large = size === 75;
  const img = stageEl("img", large ? "game-icon game-icon-lg" : "game-icon");
  img.src = (large && game.iconLarge) || game.icon;
  img.alt = "";
  return img;
}

function renderStageIconStack(value, scope) {
  const id = stageFill(value, scope, true);
  const game = STAGE_GAMES[id];
  if (!game) return renderStageIcon(value, scope);
  const stack = stageEl("div", "game-icon game-icon-stack game-icon-lg");
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

function renderConnectionsColor(value, scope) {
  if (Array.isArray(value)) {
    const stack = stageEl("div", "connections-colors");
    for (const item of value) stack.appendChild(renderConnectionsColor(item, scope));
    return stack;
  }
  const color = stageFill(value, scope, true).toLowerCase();
  const node = stageEl("div", "connections-color");
  node.dataset.color = CONNECTIONS_COLORS.includes(color) ? color : "unknown";
  node.appendChild(stageEl("span", "connections-label", color.toUpperCase()));
  return node;
}

function renderWeekdayChart(path, scope) {
  const rows = stageGet(scope, path);
  const list = stageEl("ol", "weekday-chart");
  if (!Array.isArray(rows)) return list;
  const maxBar = Math.max(...rows.map((r) => Number(r.bar) || 0), 1);
  const trackW = 137;
  for (const row of rows) {
    const item = stageEl("li", "weekday-chart-row");
    const barW = Math.max(20, Math.round(((Number(row.bar) || trackW) / maxBar) * trackW));
    // Equal-value charts (all 12): force equal bars per design note.
    const equal = rows.every((r) => Number(r.value) === Number(rows[0].value));
    const width = equal ? trackW : barW;
    const track = stageEl("span", "weekday-chart-track");
    const bar = stageEl("span", "weekday-chart-bar");
    bar.style.width = `${width}px`;
    track.appendChild(bar);
    item.append(
      stageEl("span", "weekday-chart-label", String(row.day).toUpperCase()),
      track,
      stageEl("span", "weekday-chart-value", stageFormat(row.value))
    );
    list.appendChild(item);
  }
  return list;
}

function renderPrimaryButton(label) {
  const btn = stageEl("button", "primary-btn");
  btn.type = "button";
  btn.textContent = label;
  btn.dataset.advance = "1";
  return btn;
}

function applyLockup(lockupEl, lockup) {
  lockupEl.style.top = lockup && lockup.top != null ? `${lockup.top}px` : "";
  lockupEl.style.height = lockup && lockup.height != null ? `${lockup.height}px` : "";
  lockupEl.style.justifyContent = (lockup && lockup.justifyContent) || "";
}

// The first key of a line is its style; later keys (size, state, marginTop, nowrap, ...) are options.
function renderStageLineNode(style, value, line, scope) {
  if (style === "game-icon") return renderStageIcon(value, scope, line.size);
  if (style === "game-icon-stack") return renderStageIconStack(value, scope);
  if (style === "connections-color") return renderConnectionsColor(value, scope);
  if (style === "weekday-chart") return renderWeekdayChart(value, scope);
  if (style === "image") return renderStageImage(line, scope);
  if (style === "wordle-row") return renderWordleRows(line, scope);
  if (style === "honeycomb") return renderHoneycomb(value, scope);
  if (STAGE_TEXT_STYLES.includes(style)) return renderStageText(style, value, scope);
  console.warn(`Unknown stage line style "${style}"`);
  return null;
}

function renderStageLine(line, scope) {
  const [style, value] = Object.entries(line)[0] || [];
  if (style === undefined) return null;
  const node = renderStageLineNode(style, value, line, scope);
  if (!node) return null;
  if (line.marginTop != null) node.style.marginTop = `${line.marginTop}px`;
  if (line.nowrap) node.style.whiteSpace = "nowrap";
  return node;
}

function renderLinesLockup(screen, scope) {
  const phone = stageEl("div", "phone");
  const lockup = stageEl("div", "lockup");
  applyLockup(lockup, screen.lockup);
  for (const line of screen.lines || []) {
    const node = renderStageLine(line, scope);
    if (node) lockup.appendChild(node);
  }
  phone.appendChild(lockup);
  return phone;
}

function renderAd(screen) {
  const phone = stageEl("div", "phone phone-ad");
  const wrap = stageEl("div", "ad-screen");
  const slug = stageEl("div", "ad-slug", "ADVERTISEMENT");
  const media = stageEl("div", "ad-media");
  const img = stageEl("img", "ad-creative");
  img.src = screen.ad.creative;
  img.alt = "";
  media.appendChild(img);

  const controls = stageEl("div", "ad-media-controls");
  const pause = stageEl("span", "ad-circle-btn ad-pause", "");
  pause.setAttribute("aria-hidden", "true");
  const mute = stageEl("img", "ad-circle-btn");
  mute.src = "assets/ad-audio-off.svg";
  mute.alt = "";
  const learn = stageEl("span", "ad-learn");
  learn.appendChild(document.createTextNode("Learn more"));
  const arrow = stageEl("img");
  arrow.src = "assets/ad-arrow-right.svg";
  arrow.alt = "";
  learn.appendChild(arrow);
  controls.append(pause, mute, learn);
  media.appendChild(controls);

  const skip = stageEl("button", "ad-skip");
  skip.type = "button";
  skip.dataset.advance = "1";
  skip.setAttribute("aria-label", "Continue");
  const skipText = stageEl("span", "ad-skip-label", screen.ad.skipLabel || "Skip");
  const skipIcon = stageEl("span", "ad-skip-icon");
  const circle = stageEl("img");
  circle.src = "assets/ad-skip-circle.svg";
  circle.alt = "";
  skipIcon.appendChild(circle);
  skipIcon.appendChild(stageEl("span", "ad-skip-count", screen.ad.skipCount || "5"));
  skip.append(skipText, skipIcon);

  wrap.append(slug, media, skip);
  phone.appendChild(wrap);
  return phone;
}

function renderStart() {
  const phone = stageEl("div", "phone phone-start");
  const stack = stageEl("div", "start-stack");
  const logo = stageEl("img", "start-games-logo");
  logo.src = "assets/games-logo-black.svg";
  logo.alt = "The New York Times Games";
  stack.appendChild(logo);
  stack.appendChild(stageEl("p", "headline", "Year in Games 2026"));
  stack.appendChild(renderPrimaryButton("Let’s go"));
  const sponsor = stageEl("div", "start-sponsor");
  sponsor.appendChild(stageEl("p", "start-supported", "Supported by"));
  const tmobile = stageEl("img", "start-tmobile");
  tmobile.src = "assets/tmobile-logo.svg";
  tmobile.alt = "T-Mobile";
  sponsor.appendChild(tmobile);
  phone.append(stack, sponsor);
  return phone;
}

function renderBot(screen) {
  const phone = stageEl("div", "phone");
  const bubble = stageEl("div", "bot-bubble");
  const p = stageEl("p", "bot-copy");
  const lead = stageEl("strong");
  lead.textContent = screen.bot.lead;
  p.append(lead, document.createTextNode(screen.bot.text));
  bubble.appendChild(p);
  const tail = stageEl("img", "bot-tail");
  tail.src = "assets/speech-tail.svg";
  tail.alt = "";
  const bot = stageEl("img", "bot-illustration");
  bot.src = screen.bot.image;
  bot.alt = "";
  phone.append(bubble, tail, bot);
  return phone;
}

function renderBadgesNew() {
  const phone = stageEl("div", "phone");
  const lockup = stageEl("div", "lockup badges-lockup");
  lockup.style.top = "183px";
  lockup.appendChild(stageEl("p", "headline", "You also earned new badges"));
  const grid = stageEl("div", "badge-grid");
  const items = [
    { src: "assets/badge-1000th.png", label: "JAN 4" },
    { src: "assets/badge-waves.png", label: "MAY 24" },
    { src: "assets/badge-5years.png", label: "JUN 6" },
    { src: "assets/badge-cake-layer.svg", label: "AUG 4", className: "badge-img badge-cake" },
    { src: "assets/badge-1st.png", label: "SEP 24" },
  ];
  for (const item of items) {
    const cell = stageEl("div", "badge-cell");
    const img = stageEl("img", item.className || "badge-img");
    img.src = item.src;
    img.alt = "";
    cell.append(img, stageEl("span", "badge-date", item.label));
    grid.appendChild(cell);
  }
  lockup.appendChild(grid);
  phone.appendChild(lockup);
  const footer = stageEl("div", "screen-footer");
  footer.appendChild(renderPrimaryButton("Share"));
  phone.appendChild(footer);
  return phone;
}

function renderBadgesEarned() {
  const phone = stageEl("div", "phone");
  const lockup = stageEl("div", "lockup badges-lockup");
  lockup.style.top = "167px";
  lockup.appendChild(stageEl("p", "headline", "...and bragging rights."));
  const wrap = stageEl("div", "badge-hero");
  const rings = stageEl("img", "badge-hero-rings");
  rings.src = "assets/badge-wordle-in-one-circles.svg";
  rings.alt = "";
  const mark = stageEl("img", "badge-hero-mark");
  mark.src = "assets/badge-wordle-in-one.svg";
  mark.alt = "";
  wrap.append(rings, mark);
  lockup.appendChild(wrap);
  lockup.appendChild(stageEl("p", "badge-date", "WORDLE IN ONE"));
  lockup.appendChild(stageEl("p", "badge-date", "JUNE 6"));
  phone.appendChild(lockup);
  const footer = stageEl("div", "screen-footer");
  footer.appendChild(renderPrimaryButton("Share"));
  phone.appendChild(footer);
  return phone;
}

function renderCh3Icons() {
  const phone = stageEl("div", "phone");
  const lockup = stageEl("div", "lockup");
  lockup.style.top = "191px";
  const row = stageEl("div", "icon-row");
  for (const [src, cls] of [
    ["assets/icon-midi-ch3.svg", "ch3-icon"],
    ["assets/icon-crossplay.svg", "ch3-icon ch3-icon-crossplay"],
    ["assets/icon-bonus.png", "ch3-icon ch3-icon-bonus"],
  ]) {
    const img = stageEl("img", cls);
    img.src = src;
    img.alt = "";
    row.appendChild(img);
  }
  lockup.appendChild(row);
  lockup.appendChild(stageEl("p", "headline", "Crossplay, the Midi and"));
  lockup.appendChild(stageEl("p", "headline", "bonus puzzles gave you"));
  lockup.appendChild(stageEl("p", "headline", "new ways to play."));
  phone.appendChild(lockup);
  return phone;
}

function renderEditorVideo() {
  const phone = stageEl("div", "phone");
  const frame = stageEl("div", "editor-frame");
  const poster = stageEl("img", "editor-poster");
  poster.src = "assets/editor-poster.png";
  poster.alt = "Tracy Bennett";
  frame.appendChild(poster);
  const ctrls = stageEl("div", "editor-controls");
  ctrls.appendChild(stageEl("span", "ad-circle-btn ad-pause", ""));
  const mute = stageEl("img", "ad-circle-btn");
  mute.src = "assets/ad-audio-off.svg";
  mute.alt = "";
  ctrls.appendChild(mute);
  frame.appendChild(ctrls);
  const cap = stageEl("div", "editor-caption");
  cap.appendChild(stageEl("p", "headline-strong", "Tracy Bennett"));
  cap.appendChild(stageEl("p", "headline", "Editor of Wordle"));
  phone.append(frame, cap);
  return phone;
}

function renderEndCard(scope) {
  const phone = stageEl("div", "phone");
  const lockup = stageEl("div", "lockup");
  lockup.style.top = "203px";
  const tiles = stageEl("div", "wordle-tiles");
  const list = scope.end_tiles || [];
  for (const t of list) {
    const tile = stageEl("span", `wordle-tile wordle-tile-${t.state}`, t.letter);
    tiles.appendChild(tile);
  }
  lockup.appendChild(tiles);
  lockup.appendChild(stageEl("p", "headline", "Thanks for playing with us."));
  lockup.appendChild(stageEl("p", "headline", "What wins will next year bring?"));
  phone.appendChild(lockup);
  return phone;
}

function renderStageScreen(screen, scope) {
  const root = document.getElementById("screen-root");
  const nav = document.querySelector(".nav");
  if (!root || !screen) return;
  root.dataset.screenId = screen.id || "";
  root.setAttribute("aria-label", screen.label || "");
  if (nav) nav.hidden = Boolean(screen.hideNav);
  if (screen.chapterBg) {
    document.documentElement.style.setProperty("--chapter-bg", screen.chapterBg);
  }

  let phone;
  switch (screen.kind) {
    case "ad":
      phone = renderAd(screen);
      break;
    case "start":
      phone = renderStart();
      break;
    case "bot":
      phone = renderBot(screen);
      break;
    case "badges-new":
      phone = renderBadgesNew();
      break;
    case "badges-earned":
      phone = renderBadgesEarned();
      break;
    case "ch3-icons":
      phone = renderCh3Icons();
      break;
    case "editor-video":
      phone = renderEditorVideo();
      break;
    case "end-card":
      phone = renderEndCard(scope);
      break;
    default:
      phone = renderLinesLockup(screen, scope);
  }
  root.replaceChildren(phone);
}
