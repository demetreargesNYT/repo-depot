"use strict";

// Subscriber / Registered click-through for Year in Games 2026.
// Revised Chapter 1, the Chapter 2 game cards, and the five community fallbacks come from
// Figma file 9kgGqMlvJXa4jUolapkp89. Older frames (Chapter 2 intro, ads, Start, badges,
// later chapters, editor, end card) stay on SPgdDz5gM1VQIg2Z6gLqZf.
// Copy and X-placeholders match Figma; not sample-data.js.
//
// The review click-through shows every card and variant. `rule` notes (and card-rules.csv) record when a
// card is skipped or swapped for an alternate; they are not applied here.

const FIGMA_FILE_KEY = "SPgdDz5gM1VQIg2Z6gLqZf";
const FIGMA_FILE_KEY_2026 = "9kgGqMlvJXa4jUolapkp89";

// Scope passed to stage-render. Screen copy keeps exact Figma placeholders inline
// ("X guesses", "X%", "TKTKTKTKTK", "Month XX", "XXX players", etc.).
//
// Do NOT treat this object as a Games API response of precomputed stats. When the
// API lands it will supply raw play data; a front-end stats calculation layer will
// derive display strings and chart rows — schema unknown, so no calculations here.
// The chart / end-tile entries below are Figma-authored samples for the prototype only.
const PROTOTYPE_PAYLOAD = {
  // Figma chart on Ch2 Daily 01 (node 10522:107947) — labels and values as drawn.
  weekday_solves: [
    { day: "MONDAY", value: 24, bar: 110 },
    { day: "TUESDAY", value: 18, bar: 63 },
    { day: "WEDNESDAY", value: 16, bar: 44 },
    { day: "THURSDAY", value: 12, bar: 29 },
    { day: "FRIDAY", value: 11, bar: 29 },
    { day: "SATURDAY", value: 5, bar: 29 },
    { day: "SUNDAY", value: 2, bar: 29 },
  ],
  // Figma charts on Ch2 Daily 02/03 — values are placeholders; bars vary by weekday as drawn.
  weekday_times: [
    { day: "MONDAY", value: 12, bar: 20 },
    { day: "TUESDAY", value: 12, bar: 29 },
    { day: "WEDNESDAY", value: 12, bar: 38 },
    { day: "THURSDAY", value: 12, bar: 45 },
    { day: "FRIDAY", value: 12, bar: 56 },
    { day: "SATURDAY", value: 12, bar: 97 },
    { day: "SUNDAY", value: 12, bar: 110 },
  ],
  // Figma End Card tiles spelling 2026 (node 103:53019).
  end_tiles: [
    { letter: "2", state: "absent" },
    { letter: "0", state: "present" },
    { letter: "2", state: "correct" },
    { letter: "6", state: "absent" },
  ],
};

const BG = {
  ch1: "#f1ecc0",
  wordle: "#c3e2c0",
  connections: "#e1dbf5",
  spelling_bee: "#fffdef",
  crossword: "#c0d8f8",
  midi: "#9ebff5",
  daily: "#84a9eb",
  strands: "#dff3f0",
  badges: "#f3eec2",
  default: "#e7f1e1",
};

// Revised frames place content 32px below the 134px Global Nav.
const CONTENT_TOP = 166;
// 24px between a game icon and the copy under it (lockup gap 16 + 8).
const AFTER_ICON = 8;

const WORDLE_HARDEST_HEADLINE = { headline: "The hardest word\nof the year was" };
const WORDLE_HARDEST_TILES = { "wordle-row": "PSHAW", state: "correct" };

const SCREENS = [
  // Chapter 1
  {
    id: "ch1-01-intro",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79012",
    label: "Downtime into playtime",
    chapterBg: BG.ch1,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "This year, you turned\ndowntime into playtime." },
    ],
  },
  {
    id: "ch1-02-total",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:78734",
    label: "You played a total of",
    chapterBg: BG.ch1,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "You played a total of" },
      { "headline-strong": "X puzzles" },
    ],
  },
  {
    id: "ch1-03-first",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:84497",
    label: "Your first puzzle was",
    chapterBg: BG.ch1,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "Your first puzzle was" },
      { image: "assets/first-puzzle-strands.svg", alt: "Strands", width: 175, height: 127.703 },
      { body: "January 4, 1:23 p.m." },
    ],
  },
  {
    id: "ch1-04-streak",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:78883",
    label: "Longest streak",
    chapterBg: BG.ch1,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "And your longest streak was\nin **Connections** at" },
      { "game-icon": "connections", size: 75 },
      { "headline-strong": "X days", marginTop: -4 },
      { body: "Keep the wins coming." },
    ],
  },
  {
    id: "ch1-05-bot",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10702:73032",
    label: "Bot fact",
    chapterBg: BG.ch1,
    kind: "bot",
    bot: {
      image: "assets/bot-illustration.png",
      lead: "Did you know: ",
      text: "Over XXX players achieved 100-day Wordle streaks this year. That’s a lot, even for this clever bot!",
    },
  },

  // Chapter 2
  {
    id: "ch2-01-intro",
    figmaNodeId: "103:52439",
    label: "Puzzle powers",
    chapterBg: BG.wordle,
    lockup: { top: 331, height: 149, justifyContent: "center" },
    lines: [
      { headline: "Let’s take a closer look\nat your puzzle powers." },
    ],
  },

  // Chapter 2: Wordle
  {
    id: "ch2-wordle-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79035",
    label: "Average Wordle guesses",
    rule: "Personalized Wordle cards need at least 10 Wordle solves; otherwise show ch2-wordle-fallback. Show the community-average lines only when the player’s average is lower than the community’s.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "wordle" },
      { headline: "On average, you solved\nWordle puzzles in", marginTop: AFTER_ICON },
      { "headline-strong": "X guesses" },
      { body: "The average across all solvers was\nX guesses. Well played!" },
    ],
  },
  {
    id: "ch2-wordle-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:106554",
    label: "Your best solves",
    rule: "Personalized Wordle cards need at least 10 Wordle solves; otherwise show ch2-wordle-fallback.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "wordle" },
      { headline: "Your best solves took", marginTop: AFTER_ICON },
      { "headline-strong": "X guesses" },
      { headline: "which you did" },
      { "headline-strong": "X times" },
      { body: "Luck. Skill. What a thrill." },
    ],
  },
  {
    id: "ch2-wordle-03a",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:106753",
    label: "Hardest Wordle: missed",
    rule: "Hardest-word slot, one of 03a/03b/03c. Show 03a when the player played PSHAW and missed it.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "wordle" },
      { ...WORDLE_HARDEST_HEADLINE, marginTop: AFTER_ICON },
      WORDLE_HARDEST_TILES,
      { body: "Over X% of players were stumped on\nJuly 15, including you!" },
    ],
  },
  {
    id: "ch2-wordle-03b",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:106945",
    label: "Hardest Wordle: solved",
    rule: "Hardest-word slot, one of 03a/03b/03c. Show 03b when the player played PSHAW and solved it.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "wordle" },
      { ...WORDLE_HARDEST_HEADLINE, marginTop: AFTER_ICON },
      WORDLE_HARDEST_TILES,
      { body: "But you guessed it! Over X% of\nplayers weren’t as lucky on July 15." },
    ],
  },
  {
    id: "ch2-wordle-03c",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10927:178917",
    label: "Hardest Wordle: not played",
    rule: "Hardest-word slot, one of 03a/03b/03c. Show 03c when the player did not play PSHAW.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "wordle" },
      { ...WORDLE_HARDEST_HEADLINE, marginTop: AFTER_ICON },
      WORDLE_HARDEST_TILES,
      { body: "It stumped over X%\nof players on July 15." },
    ],
  },
  {
    id: "ch2-wordle-04",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:106848",
    label: "Top starting words",
    rule: "Personalized Wordle cards need at least 10 Wordle solves; otherwise show ch2-wordle-fallback.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "wordle" },
      { headline: "And your top\nstarting words were", marginTop: AFTER_ICON },
      { "wordle-row": ["ADIEU", "BREAD", "MOUSE"], state: "empty" },
      { body: "Way to make the first move." },
    ],
  },
  {
    id: "ch2-wordle-fallback",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10987:61831",
    label: "Wordle community fallback",
    rule: "Community fallback for Wordle. Shown instead of the personalized Wordle cards when the player has fewer than 10 Wordle solves.",
    chapterBg: BG.wordle,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "In Wordle, the most popular\nstarting word was" },
      { "wordle-row": "ADIEU", state: "correct" },
      { body: "Oh là là!" },
    ],
  },

  // Chapter 2: Connections
  {
    id: "ch2-connections-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107062",
    label: "Solve order",
    rule: "Personalized Connections cards need at least 10 Connections solves; otherwise show ch2-connections-fallback.",
    chapterBg: BG.connections,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "connections" },
      { headline: "In Connections, your most\ncommon solving order was", marginTop: AFTER_ICON },
      { "connections-color": ["blue", "green", "yellow", "purple"] },
    ],
  },
  {
    id: "ch2-connections-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79048",
    label: "Purple first",
    rule: "Skip when the player never got the purple category first. No alternate.",
    chapterBg: BG.connections,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "connections" },
      { headline: "You got the purple category first", marginTop: AFTER_ICON, nowrap: true },
      { "headline-strong": "X times" },
      { body: "We see you, overachiever." },
    ],
  },
  {
    id: "ch2-connections-03",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107138",
    label: "Connections solve rate",
    rule: "Personalized Connections cards need at least 10 Connections solves; otherwise show ch2-connections-fallback.",
    chapterBg: BG.connections,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "connections" },
      { headline: "And of puzzles you\nattempted, you had a", marginTop: AFTER_ICON },
      { "headline-strong": "X% solve rate" },
    ],
  },
  {
    id: "ch2-connections-04",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107222",
    label: "Average mistakes",
    rule: "Personalized Connections cards need at least 10 Connections solves; otherwise show ch2-connections-fallback.",
    chapterBg: BG.connections,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "connections" },
      { headline: "On average, you solved\npuzzles while making", marginTop: AFTER_ICON },
      { "headline-strong": "X mistakes" },
      { body: "Blame it on the red herrings." },
    ],
  },
  {
    id: "ch2-connections-05",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107296",
    label: "Perfect Connections",
    rule: "Skip when the player had no mistake-free solves. No alternate.",
    chapterBg: BG.connections,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "connections" },
      { headline: "You also solved\nwithout any mistakes", marginTop: AFTER_ICON },
      { "headline-strong": "X times" },
      { body: "And they say perfection doesn’t exist." },
    ],
  },
  {
    id: "ch2-connections-fallback",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10957:179144",
    label: "Connections community fallback",
    rule: "Community fallback for Connections. Shown instead of the personalized Connections cards when the player has fewer than 10 Connections solves.",
    chapterBg: BG.connections,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "In Connections, a picture-only\npuzzle stumped" },
      { "headline-strong": "X% of players", nowrap: true },
      { body: "February 7. What a day." },
    ],
  },

  // Chapter 2: Spelling Bee
  {
    id: "ch2-spelling-bee-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79058",
    label: "Spelling Bee words",
    rule: "Personalized Spelling Bee cards need at least 10 Spelling Bee solves; otherwise show ch2-spelling-bee-fallback.",
    chapterBg: BG.spelling_bee,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "spelling_bee" },
      { headline: "In Spelling Bee, you found a\ntotal of", marginTop: AFTER_ICON },
      { "headline-strong": "X words" },
      { body: "Honey, what an accomplishment." },
    ],
  },
  {
    id: "ch2-spelling-bee-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107386",
    label: "Longest word",
    rule: "Personalized Spelling Bee cards need at least 10 Spelling Bee solves; otherwise show ch2-spelling-bee-fallback.",
    chapterBg: BG.spelling_bee,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "spelling_bee" },
      { headline: "Your longest word was", marginTop: AFTER_ICON },
      { honeycomb: "TKTKTKTKTK" },
    ],
  },
  {
    id: "ch2-spelling-bee-03",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107453",
    label: "Pangrams",
    rule: "Skip when the player found no pangrams.",
    chapterBg: BG.spelling_bee,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "spelling_bee" },
      { headline: "You also found", marginTop: AFTER_ICON },
      { "headline-strong": "X pangrams" },
      { body: "Hive fives, all around." },
    ],
  },
  {
    id: "ch2-spelling-bee-04a",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10515:107520",
    label: "Genius and Queen Bee",
    rule: "Top-rank slot, one of 04a/04b. Show 04a when Genius or Queen Bee was reached at least once. Skip the slot when the top rank is below Solid.",
    chapterBg: BG.spelling_bee,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "spelling_bee" },
      { headline: "And you reached Genius", marginTop: AFTER_ICON },
      { "headline-strong": "X times" },
      { headline: "and Queen Bee" },
      { "headline-strong": "X times" },
      { body: "Sweet, sweet victory." },
    ],
  },
  {
    id: "ch2-spelling-bee-04b",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10844:160970",
    label: "Top rank",
    rule: "Top-rank slot, one of 04a/04b. Show 04b when the top rank is Solid or higher but neither Genius nor Queen Bee was reached. Skip the slot when the top rank is below Solid.",
    chapterBg: BG.spelling_bee,
    lockup: { top: 150 },
    lines: [
      { "game-icon": "spelling_bee", size: 75 },
      { headline: "And you reached [Rank]" },
      { "headline-strong": "X times" },
      { body: "Sweet!" },
    ],
  },
  {
    id: "ch2-spelling-bee-fallback",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10957:179155",
    label: "Spelling Bee community fallback",
    rule: "Community fallback for Spelling Bee. Shown instead of the personalized Spelling Bee cards when the player has fewer than 10 Spelling Bee solves.",
    chapterBg: BG.spelling_bee,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "The Month XX\nSpelling Bee puzzle gave us" },
      { "headline-strong": "XX Queen Bees", nowrap: true },
      { body: "They’ve got the last word. Literally." },
    ],
  },

  // Older screens, in their previous relative order.
  {
    id: "ad-2",
    figmaNodeId: "103:52362",
    label: "Ad 2 – Countdown",
    chapterBg: BG.default,
    hideNav: true,
    kind: "ad",
    ad: { creative: "assets/ad-creative.png", skipLabel: "Continue in", skipCount: "5" },
  },
  {
    id: "ad-1",
    figmaNodeId: "103:52339",
    label: "Ad 1 – Countdown",
    chapterBg: BG.default,
    hideNav: true,
    kind: "ad",
    ad: { creative: "assets/ad-creative.png", skipLabel: "Continue in", skipCount: "5" },
  },
  {
    id: "ad-2-b",
    figmaNodeId: "103:52974",
    label: "Ad 2 – Countdown (repeat)",
    chapterBg: BG.default,
    hideNav: true,
    kind: "ad",
    ad: { creative: "assets/ad-creative.png", skipLabel: "Continue in", skipCount: "5" },
  },
  {
    id: "start",
    figmaNodeId: "103:52997",
    label: "Start",
    chapterBg: BG.default,
    hideNav: true,
    kind: "start",
  },
  // Chapter 2: Mini
  {
    id: "ch2-mini-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10519:107602",
    label: "Mini total",
    rule: "Personalized Mini cards need at least 10 Mini solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.crossword,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "mini" },
      { headline: "For the Mini,\nyou solved a total of", marginTop: AFTER_ICON },
      { "headline-strong": "X puzzles" },
      { body: "Small grid, big win." },
    ],
  },
  {
    id: "ch2-mini-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79068",
    label: "Fastest Mini",
    rule: "Personalized Mini cards need at least 10 Mini solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.crossword,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "mini" },
      { headline: "Your fastest time was", marginTop: AFTER_ICON },
      { "headline-strong": "XX:XX" },
      { body: "That’s some speedy typing." },
    ],
  },
  {
    id: "ch2-mini-03",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10844:161050",
    label: "Average Mini time",
    rule: "Personalized Mini cards need at least 10 Mini solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.crossword,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "mini" },
      { headline: "Your average time was", marginTop: AFTER_ICON },
      { "headline-strong": "XX:XX" },
    ],
  },
  {
    id: "ch2-mini-04",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10519:107672",
    label: "Mini streak",
    rule: "Skip when the player’s longest Mini streak is below the configured threshold; threshold value TBD.",
    chapterBg: BG.crossword,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "mini" },
      { headline: "And your longest streak was", marginTop: AFTER_ICON },
      { "headline-strong": "X puzzles" },
      { body: "A not-so-Mini milestone." },
    ],
  },

  // Chapter 2: Midi
  {
    id: "ch2-midi-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79247",
    label: "Midi total",
    rule: "Personalized Midi cards need at least 10 Midi solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.midi,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "midi" },
      { headline: "When it came to the Midi,\nyou solved a total of", marginTop: AFTER_ICON },
      { "headline-strong": "X puzzles" },
    ],
  },
  {
    id: "ch2-midi-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:107763",
    label: "Midi streak",
    rule: "Skip when the player’s longest Midi streak is below the configured threshold; threshold value TBD.",
    chapterBg: BG.midi,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "midi" },
      { headline: "Your longest streak was", marginTop: AFTER_ICON },
      { "headline-strong": "X days" },
      { body: "Gold stars look good on you." },
    ],
  },
  {
    id: "ch2-midi-03",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:107848",
    label: "Midi times",
    rule: "Personalized Midi cards need at least 10 Midi solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.midi,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "midi" },
      { headline: "Your fastest time was", marginTop: AFTER_ICON },
      { "headline-strong": "X:XX" },
      { headline: "and your average time was" },
      { "headline-strong": "X:XX" },
    ],
  },

  // Chapter 2: Daily Crossword
  {
    id: "ch2-daily-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:107947",
    label: "Most often Mondays",
    rule: "Personalized Daily Crossword cards need at least 10 Daily Crossword solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.daily,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "crossword" },
      { headline: "For the Crossword,\nyou solved most often on", marginTop: AFTER_ICON },
      { "headline-strong": "Mondays", marginTop: -8 },
      { body: "Starting the week with win.", marginTop: -8 },
      { "weekday-chart": "weekday_solves" },
    ],
  },
  {
    id: "ch2-daily-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:108030",
    label: "Average Crossword time",
    rule: "Personalized Daily Crossword cards need at least 10 Daily Crossword solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.daily,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "crossword" },
      { headline: "Your average time was", marginTop: AFTER_ICON },
      { "headline-strong": "X:XX" },
      { "weekday-chart": "weekday_times", marginTop: -8 },
    ],
  },
  {
    id: "ch2-daily-03",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:108113",
    label: "Fastest Crossword",
    rule: "Personalized Daily Crossword cards need at least 10 Daily Crossword solves; otherwise show ch2-crosswords-fallback.",
    chapterBg: BG.daily,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "crossword" },
      { headline: "Your fastest time was", marginTop: AFTER_ICON },
      { "headline-strong": "X:XX" },
      { body: "A puzzle boss. Down and across." },
      { "weekday-chart": "weekday_times", marginTop: -8 },
    ],
  },
  {
    id: "ch2-daily-04",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79098",
    label: "Crossword streak",
    rule: "Skip when the player’s longest Daily Crossword streak is below the configured threshold; threshold value TBD.",
    chapterBg: BG.daily,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "crossword" },
      { headline: "And your longest streak was", marginTop: AFTER_ICON },
      { "headline-strong": "X days" },
      { body: "Who’s off the grid? Not you!" },
    ],
  },
  {
    id: "ch2-crosswords-fallback",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10957:179166",
    label: "Crosswords community fallback",
    rule: "Shared community fallback for Mini, Midi, and the Daily Crossword. Shown instead of that game’s personalized cards when the player has fewer than 10 solves of that game. The review flow shows it once.",
    chapterBg: BG.crossword,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "One speedster solved the\nMini crossword in just" },
      { "headline-strong": "X seconds", nowrap: true },
      { body: "We can’t believe it either." },
    ],
  },

  // Chapter 2: Strands
  {
    id: "ch2-strands-01",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:108211",
    label: "Strands total",
    rule: "Personalized Strands cards need at least 10 Strands solves; otherwise show ch2-strands-fallback.",
    chapterBg: BG.strands,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "strands" },
      { headline: "In Strands,\nyou solved a total of", marginTop: AFTER_ICON },
      { "headline-strong": "X puzzles" },
    ],
  },
  {
    id: "ch2-strands-02",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10406:79111",
    label: "Spangram first",
    rule: "Skip when the player never found the spangram first.",
    chapterBg: BG.strands,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "strands" },
      { headline: "You found the spangram first", marginTop: AFTER_ICON, nowrap: true },
      { "headline-strong": "X times" },
      { body: "Way to see all sides of the story." },
    ],
  },
  {
    id: "ch2-strands-03",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10522:108302",
    label: "Strands without hints",
    rule: "Skip when the player had no solves without hints.",
    chapterBg: BG.strands,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "strands" },
      { headline: "And solved without hints", marginTop: AFTER_ICON },
      { "headline-strong": "X times" },
      { body: "A-maze-ing." },
    ],
  },
  {
    id: "ch2-strands-04",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10844:161117",
    label: "Strands hints",
    rule: "Skip when the player did not use any hints.",
    chapterBg: BG.strands,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "strands" },
      { headline: "And used a total of", marginTop: AFTER_ICON },
      { "headline-strong": "X hints" },
      { body: "Teamwork makes the theme work.\nOn average, players used\nXXX hints this year." },
    ],
  },
  {
    id: "ch2-strands-05",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10844:161181",
    label: "Strands non-theme words",
    rule: "Skip when the player never found a non-theme word.",
    chapterBg: BG.strands,
    lockup: { top: CONTENT_TOP },
    lines: [
      { "game-icon": "strands" },
      { headline: "And found a total of", marginTop: AFTER_ICON },
      { "headline-strong": "X non-theme words" },
      { body: "Here for every twist and turn." },
    ],
  },
  {
    id: "ch2-strands-fallback",
    figmaFileKey: FIGMA_FILE_KEY_2026,
    figmaNodeId: "10957:179177",
    label: "Strands community fallback",
    rule: "Community fallback for Strands. Shown instead of the personalized Strands cards when the player has fewer than 10 Strands solves.",
    chapterBg: BG.strands,
    lockup: { top: CONTENT_TOP },
    lines: [
      { headline: "In Strands," },
      { "headline-strong": "X million players", nowrap: true },
      { headline: "solved a puzzle with 0 hints." },
      { body: "A-maze-ing." },
    ],
  },
  {
    id: "badges-new",
    figmaNodeId: "103:52305",
    label: "New badges",
    chapterBg: BG.badges,
    kind: "badges-new",
  },
  {
    id: "ch3-02",
    figmaNodeId: "103:53029",
    label: "Midi, Crossplay, Bonus",
    chapterBg: BG.crossword,
    kind: "ch3-icons",
  },
  {
    id: "chapter-7",
    figmaNodeId: "103:52279",
    label: "Plenty more to celebrate",
    chapterBg: BG.crossword,
    lockup: { top: 331, height: 149, justifyContent: "center" },
    lines: [
      { headline: "There’s plenty more to\ncelebrate, too." },
    ],
  },
  {
    id: "badges-earned",
    figmaNodeId: "103:52328",
    label: "Bragging rights",
    chapterBg: BG.badges,
    kind: "badges-earned",
  },
  {
    id: "chapter-13",
    figmaNodeId: "103:52283",
    label: "You play favorites",
    chapterBg: BG.default,
    lockup: { top: 280, justifyContent: "center" },
    lines: [
      { headline: "But through it all, it's clear" },
      { headline: "you play favorites." },
      { headline: "In 2026, your top game was..." },
    ],
  },
  {
    id: "chapter-16",
    figmaNodeId: "103:52293",
    label: "Top game Wordle",
    chapterBg: BG.wordle,
    lockup: { top: 280, justifyContent: "center" },
    lines: [
      { "game-icon": "wordle", size: 75 },
      { "headline-strong": "Wordle" },
    ],
  },
  {
    id: "ch4-editor-video",
    figmaNodeId: "103:53013",
    label: "Editor video",
    chapterBg: BG.wordle,
    kind: "editor-video",
  },
  {
    id: "end-card",
    figmaNodeId: "103:53019",
    label: "End card",
    chapterBg: BG.default,
    kind: "end-card",
  },
];

const FLOW_NODE_IDS = SCREENS.map((screen) => screen.figmaNodeId);

function figmaUrl(screenOrNodeId) {
  const screen = typeof screenOrNodeId === "object" ? screenOrNodeId : { figmaNodeId: screenOrNodeId };
  const fileKey = screen.figmaFileKey || FIGMA_FILE_KEY;
  const hyphen = String(screen.figmaNodeId).replace(":", "-");
  return `https://www.figma.com/design/${fileKey}/?node-id=${hyphen}&m=dev`;
}
