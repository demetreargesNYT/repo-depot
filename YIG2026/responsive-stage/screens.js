"use strict";

// Subscriber / Registered click-through for Year in Games 2026.
//
// Screen order matches the Figma "YIG - Prototype" link order (file SPgdDz5gM1VQIg2Z6gLqZf).
// Only screens with a `lines` array are rendered; the rest are listed in PENDING_FIGMA_NODES
// until a Figma token can supply copy and layout from those frames.
//
// Line objects use the same { style: value } shape as YIG2026/renderer.js so a real Games API
// payload can fill {placeholders} later. Copy and stats here are the Chapter 1 values already
// matched to Figma in this folder — not sample-data.js.

const FIGMA_FILE_KEY = "SPgdDz5gM1VQIg2Z6gLqZf";

// Full Subscriber/Registered link order (45 frames). Hyphen form is for Figma URLs; colon for the API.
const FLOW_NODE_IDS = [
  "103:52456", "103:52488", "103:52362", "103:52339", "103:52385",
  "103:52396", "103:52436", "103:52439", "103:52445", "103:52470",
  "103:52478", "103:52418", "103:52502", "103:52974", "103:52521",
  "103:52548", "103:52997", "103:53051", "103:52565", "103:52602",
  "103:52620", "103:52634", "103:52584", "103:52700", "103:52685",
  "103:52650", "103:52908", "103:52670", "103:52737", "103:52950",
  "103:52713", "103:52928", "103:52762", "103:52833", "103:52874",
  "103:52857", "103:52891", "103:52279", "103:52305", "103:53029",
  "103:52328", "103:52283", "103:52293", "103:53013", "103:53019",
];

// Prototype payload for the screens we can ship without inventing copy. Paths match the
// placeholders in SCREENS[].lines. Replace with a real Games API payload later.
const PROTOTYPE_PAYLOAD = {
  first_puzzle: {
    game: "wordle",
    at: "Jan 3, 2026 7:35AM",
  },
  streak: {
    game: "connections",
    days: 74,
    range: "Jan 3 - mar 28, 2026",
  },
  total_puzzles: 152,
  community_quote:
    "If you lined up all the Wordle tiles guessed in 2026, they would reach the moon faster than you can say PSHAW.",
};

// Implemented screens only. First five FLOW_NODE_IDS are Chapter 1 (existing HTML already matched Figma).
// lockup.top / height match the prior hardcoded layout. Preserve the Figma typo "You first puzzle".
const SCREENS = [
  {
    id: "ch1-time",
    figmaNodeId: "103:52456",
    chapter: 1,
    label: "This year, you gave the puzzles your time",
    lockup: { top: 176, height: 149, justifyContent: "center" },
    lines: [
      { headline: "This year, you gave the puzzles your time." },
    ],
  },
  {
    id: "ch1-first-puzzle",
    figmaNodeId: "103:52488",
    chapter: 1,
    label: "Your first puzzle of the year",
    lockup: { top: 207 },
    lines: [
      { headline: "You first puzzle of\nthe year was" },
      { "game-icon": "{first_puzzle.game}" },
      { display: "{first_puzzle.game}" },
      { label: "{first_puzzle.at}" },
    ],
  },
  {
    id: "ch1-streak",
    figmaNodeId: "103:52362",
    chapter: 1,
    label: "Your longest streak",
    lockup: { top: 210 },
    lines: [
      { headline: "Your longest streak was" },
      { "game-icon-stack": "{streak.game}" },
      { display: "{streak.days} days" },
      { label: "{streak.range}" },
    ],
  },
  {
    id: "ch1-total",
    figmaNodeId: "103:52339",
    chapter: 1,
    label: "Total puzzles played",
    lockup: { top: 207 },
    lines: [
      { headline: "You played a total of" },
      { display: "{total_puzzles} puzzles" },
      { label: "Across all games" },
    ],
  },
  {
    id: "ch1-moon-quote",
    figmaNodeId: "103:52385",
    chapter: 1,
    label: "Wordle tiles to the moon",
    lockup: { top: 225 },
    lines: [
      { quote: "\u201c{community_quote}\u201d" },
    ],
  },
];

// Remaining frames in click-through order — need Figma node text/layout before they can be screens.
const PENDING_FIGMA_NODES = FLOW_NODE_IDS.slice(SCREENS.length);

function figmaUrl(nodeId) {
  const hyphen = String(nodeId).replace(":", "-");
  return `https://www.figma.com/design/${FIGMA_FILE_KEY}/YIG---Prototype?node-id=${hyphen}&m=dev`;
}
