// Checks docs/card-flow.md (core/card-flow.md in the package) against the React example's card builder
// (engineering/react/src/cards.ts): for several players, the scenes, their order, their settings, the ad tags and the
// copy waits the document gives must be the ones the code builds. Fails when either side changes alone.
//
//   npm run cardflow        (no server, no browser; node --experimental-strip-types reads cards.ts)
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseDoc, docCards, waitFor, waitsIn, GAME_ORDER } from "./card-flow.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.join(HERE, "..");
const { buildCards } = await import(path.join(REPO, "engineering", "react", "src", "cards.ts"));
const doc = parseDoc();

const results = [];
const check = (ok, text) => { results.push(ok); console.log(`${ok ? "PASS" : "FAIL"}  ${text}`); };

// ---- the document itself --------------------------------------------------------------------------------------------
for (const [key, rows] of Object.entries(doc)) {
  const dup = rows.map((r) => r.frame).filter((f, i, all) => all.indexOf(f) !== i);
  check(!dup.length, `${key} table: every frame appears once${dup.length ? ": " + dup.join(", ") : ""}`);
  check(rows[0]?.scene === "loading" && rows.at(-1)?.scene === (key === "regi" ? "share" : "end"), `${key} table: runs from loading to ${key === "regi" ? "share" : "end"}`);
}
// every scene named is a value of its file's scene enum
const enums = {};
for (const n of [1, 2, 3]) enums[n] = JSON.parse(fs.readFileSync(path.join(REPO, "chapters", `ch${n}`, "chapter.json"), "utf8")).scenes.map((s) => s.name);
const unknown = Object.values(doc).flat().filter((r) => !enums[r.file].includes(r.scene)).map((r) => `${r.frame} (file ${r.file}: ${r.scene})`);
check(!unknown.length, `every scene in the tables is a scene of its file${unknown.length ? ": " + unknown.join(", ") : ""}`);

// ---- the players ----------------------------------------------------------------------------------------------------
// the most cards each game can have (the frames in the design files); the stats rules decide how many a player gets
const FULL = { wordle: 4, connections: 5, "spelling-bee": 4, mini: 4, midi: 3, crossword: 4, strands: 4 };
const player = (name, flow, games, extra = {}) => ({ name, flow, games, personal: 2, events: 3, top: games[0] ?? "wordle", ...extra });
const PLAYERS = [
  player("Wordle only", "sub", ["wordle"]),
  player("Connections only", "sub", ["connections"]),
  player("Spelling Bee only", "sub", ["spelling-bee"]),
  player("The Mini only", "sub", ["mini"]),
  player("The Midi only", "sub", ["midi"]),
  player("The Crossword only", "sub", ["crossword"]),
  player("Strands only", "sub", ["strands"]),
  player("Wordle and Connections", "sub", ["connections", "wordle"], { top: "connections" }),
  player("The Mini and The Midi", "sub", ["midi", "mini"]),
  player("all seven", "sub", [...GAME_ORDER].reverse(), { top: "strands" }),
  player("Wordle only, no badges", "sub", ["wordle"], { personal: 0, events: 0 }),
  player("Wordle only, event badges only", "sub", ["wordle"], { personal: 0 }),
  player("Wordle only, personal badges only", "sub", ["wordle"], { events: 0 }),
  player("Wordle and Spelling Bee, fewer cards", "sub", ["wordle", "spelling-bee"], { cards: { wordle: 2, "spelling-bee": 1 } }),
  player("Regi/Sub with no qualifying game", "sub", []),
  player("Anonymous", "anon", []),
];

for (const p of PLAYERS) {
  const cardsPerGame = Object.fromEntries(p.games.map((g) => [g, p.cards?.[g] ?? FULL[g]]));
  const code = buildCards({
    flow: p.flow === "anon" ? "anonymous" : "subscriber", games: p.games, cardsPerGame,
    eventBadges: p.events, achievementBadges: p.personal, topGame: p.top,
  });
  const own = GAME_ORDER.filter((g) => p.games.includes(g));
  const want = docCards(doc, p.flow, { own, cardsPerGame, personal: p.personal, events: p.events, top: p.top });

  // what the settings of a code card are, in the document's terms
  const settingsOf = (c) => {
    const s = {};
    if (c.file === 2 && GAME_ORDER.includes(c.scene)) s.lockup = String(!c.community);
    if (c.reveal !== undefined) s.reveal = String(c.reveal);
    if (c.topGame) s.topGame = c.topGame;
    return s;
  };
  const line = (x) => `${x.file}:${x.scene} ${JSON.stringify(x.settings)}${x.ad ? " ad" : ""}`;
  const got = code.map((c) => line({ ...c, settings: settingsOf(c), ad: !!c.ad }));
  const exp = want.map(line);
  const same = JSON.stringify(got) === JSON.stringify(exp);
  let why = "";
  if (!same) {
    const i = [...Array(Math.max(got.length, exp.length)).keys()].find((k) => got[k] !== exp[k]);
    why = `: first difference at card ${i}: code ${got[i] ?? "(none)"}, document ${exp[i] ?? "(none)"}`;
  }
  check(same, `${p.name}: scenes, order, settings and ad tags match the document (${code.length} cards)${why}`);
  if (!same) continue;

  const waitBad = [];
  want.forEach((c, i) => {
    if (i < 2) return;            // loading has no copy; start's copy is a first visit
    const nums = waitsIn(c.wait), w = waitFor(want, i);
    if (!nums.includes(w) || (nums.length === 1 && nums[0] !== w)) waitBad.push(`${c.frame} (card ${i}): the document says "${c.wait}", the guide's timing gives ${w} s`);
  });
  check(!waitBad.length, `${p.name}: every copy wait matches the guide's Copy timing${waitBad.length ? ": " + waitBad.slice(0, 3).join(" / ") : ""}`);
}

console.log(`\n${results.filter(Boolean).length} of ${results.length} checks passed`);
process.exit(results.every(Boolean) ? 0 : 1);
