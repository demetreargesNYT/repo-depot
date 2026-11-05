// Reads docs/card-flow.md (the card-flow spec that ships as core/card-flow.md) and works out, for one player, the cards the
// document says they get: file, scene, settings and the copy wait of each. harness/card-flow-test.mjs compares that with
// engineering/react/src/cards.ts, and experience-test.mjs compares it with the card list the harness page builds, so the
// document and the code can't drift apart without a test failing.
//
// The "Skip when" column is a fixed set of sentences; a sentence this file doesn't know stops the test, so a new rule in the
// document has to be taught here too.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const DOC_PATH = path.join(HERE, "..", "docs", "card-flow.md");

export const NAMES = { Wordle: "wordle", Connections: "connections", "Spelling Bee": "spelling-bee", "The Mini": "mini", "The Midi": "midi", "The Crossword": "crossword", Strands: "strands" };
export const GAME_ORDER = Object.values(NAMES);

const strip = (s) => s.replace(/`/g, "").trim();

// {regi: rows, anon: rows}; each row {frame, file, scene, settings, wait, skip, slot}
export function parseDoc(text = fs.readFileSync(DOC_PATH, "utf8")) {
  const tables = {};
  const lines = text.split("\n");
  for (const [key, heading] of [["regi", "## Registered and subscribers"], ["anon", "## Anonymous"]]) {
    const at = lines.findIndex((l) => l.trim() === heading);
    if (at < 0) throw new Error(`card-flow.md has no "${heading}" section`);
    const rows = [];
    let i = at + 1;
    while (i < lines.length && !lines[i].startsWith("|")) i++;
    const header = lines[i].split("|").slice(1, -1).map((c) => c.trim());
    const want = ["Frame", "File", "Scene", "Settings", "Copy wait", "Skip when"];
    if (JSON.stringify(header) !== JSON.stringify(want)) throw new Error(`${heading}: the columns are ${header.join(" | ")}; want ${want.join(" | ")}`);
    for (i += 2; i < lines.length && lines[i].startsWith("|"); i++) {
      const cells = lines[i].split("|").slice(1, -1).map((c) => c.trim());
      if (cells.length !== 6) throw new Error(`${heading}: a row with ${cells.length} cells: ${lines[i]}`);
      const [frame, file, scene, settings, wait, skip] = cells;
      const slot = Number(strip(frame).match(/^[a-z-]+--(\d\d)/)?.[1] ?? 0);
      rows.push({
        frame: strip(frame), file: Number(file), scene: strip(scene), wait, skip, slot,
        settings: settings === "—" ? {} : Object.fromEntries(strip(settings).split(",").map((s) => s.trim().split("="))),
      });
    }
    tables[key] = rows;
  }
  return tables;
}

// ctx: { own: [qualifying games], cardsPerGame: {game: n}, personal: n, events: n, top: game }
function included(row, ctx) {
  const s = row.skip;
  if (s === "Never." || s === "Ad: after the first time it is shown.") return true;
  let m;
  if ((m = s.match(/^Fewer than 10 completed puzzles in (.+?)(, or the stats requirements leave this card out)?\.$/))) {
    const game = NAMES[m[1]];
    if (!game) throw new Error(`${row.frame}: unknown game "${m[1]}"`);
    if (game !== row.scene) throw new Error(`${row.frame}: its skip sentence names ${m[1]}, its scene is ${row.scene}`);
    return ctx.own.includes(game) && (!m[2] || row.slot <= (ctx.cardsPerGame[game] ?? 0));
  }
  if (s === "The player has no personal badges.") return ctx.personal > 0;
  if (s === "The player has no event badges.") return ctx.events > 0;
  if (s === "The player doesn't have exactly one qualifying game.") return ctx.own.length === 1;
  if ((m = s.match(/^The player doesn't have exactly one qualifying game, or that game is (.+)\.$/))) {
    const game = NAMES[m[1]];
    if (!game || game !== row.scene) throw new Error(`${row.frame}: skip sentence "${s}" doesn't match its scene ${row.scene}`);
    return ctx.own.length === 1 && ctx.own[0] !== game;
  }
  throw new Error(`${row.frame}: a "Skip when" sentence the tests don't know: "${s}"`);
}

// The cards the document gives this player: the Anonymous table for Anonymous players and for Regi/Sub players with no
// qualifying game, else the Registered and subscribers table.
export function docCards(doc, flow, ctx) {
  const anon = flow === "anon" || ctx.own.length === 0;
  const top = anon ? "wordle" : ctx.top;
  return doc[anon ? "anon" : "regi"].filter((row) => included(row, ctx)).map((row) => ({
    frame: row.frame, file: row.file, scene: row.scene, wait: row.wait,
    ad: row.skip.startsWith("Ad:"),
    settings: Object.fromEntries(Object.entries(row.settings).map(([k, v]) => [k, v === "<top game>" ? top : v])),
  }));
}

// ---- the copy wait of a card, from the cards before it (the guide's Copy timing table, written out) ---------------------

const PAN = 1.65, FIRST = 2.0, LOCKUP = 3.2, QUICK = 0.34, REVEAL = 1.45;
const NO_INTRO = { 1: ["loading", "ad"], 2: ["from-chapter-1", "to-chapter-3"], 3: ["ad"] };
const ENDS = { 1: "ad", 2: "to-chapter-3" };
const SHARED_ROOMS = [["ad", "chapter-3-personal-badges", "chapter-3-event-badges"], ["chapter-3", "chapter-3-2"], ["chapter-4", "chapter-4-top-game", "chapter-4-editor-video"], ["end", "share"]];
const roomOf = (file, scene) => (file === 3 ? SHARED_ROOMS.find((l) => l.includes(scene))?.[0] : null) ?? scene;

// the wait, in seconds, for a Next that reaches cards[i] for the first time
export function waitFor(cards, i) {
  const c = cards[i], p = cards[i - 1];
  if (c.file === p.file && roomOf(c.file, c.scene) === roomOf(p.file, p.scene)) {
    const revealChanges = c.settings.reveal !== undefined && p.settings.reveal !== undefined && c.settings.reveal !== p.settings.reveal;
    return revealChanges ? REVEAL : QUICK;
  }
  const legs = c.file !== p.file && p.scene !== ENDS[p.file] ? 2 : 1;
  const first = NO_INTRO[c.file].includes(roomOf(c.file, c.scene)) ? PAN : c.file === 2 && GAME_ORDER.includes(c.scene) && c.settings.lockup === "true" ? LOCKUP : FIRST;
  return (legs - 1) * PAN + first;
}

// the numbers (seconds) a "Copy wait" cell offers
export const waitsIn = (cell) => [...cell.matchAll(/(\d+(?:\.\d+)?) s\b/g)].map((m) => Number(m[1]));
