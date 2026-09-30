"use strict";

// Example data for the configurator. A real payload will replace these.
//
// PAYLOADS: one player's data each, in the order the payload dropdown lists them. Every payload's
// streak game is one of its own games, so switching payloads changes the icon and name as well as
// the chart. The "anon" payload has no player data, only community.* fields.
//
// STARTING_CARD: the card JSON the page opens with. One version for players with stats ("personal")
// and one for players without ("anon", which reads community.* instead).

const PAYLOADS = {
  "sub-1-wordle": {
    label: "Sub/Regi · 1 game · Wordle",
    data: {
      streak: { game: "wordle", days: 9 },
      days_all: 150,
      best_wordle_solve: { word: "bongo", date: "Jan 1st, 2026", time: "12:34pm" },
      games: [{ game: "wordle", solved: 142 }],
    },
  },
  "sub-1-connections": {
    label: "Sub/Regi · 1 game · Connections",
    data: {
      streak: { game: "connections", days: 34 },
      days_all: 120,
      top_connections_color: "yellow",
      games: [{ game: "connections", solved: 110 }],
    },
  },
  "sub-4-wordle": {
    label: "Sub/Regi · 4 games · Wordle-led",
    data: {
      streak: { game: "wordle", days: 41 },
      days_all: 380,
      best_wordle_solve: { word: "quick", date: "Feb 9th, 2026", time: "8:02am" },
      top_connections_color: "blue",
      games: [
        { game: "wordle", solved: 190 },
        { game: "connections", solved: 92 },
        { game: "mini", solved: 48 },
        { game: "strands", solved: 27 },
      ],
    },
  },
  "sub-4-connections": {
    label: "Sub/Regi · 4 games · Connections-led",
    data: {
      streak: { game: "connections", days: 66 },
      days_all: 420,
      best_wordle_solve: { word: "crane", date: "Mar 3rd, 2026", time: "7:15am" },
      top_connections_color: "yellow",
      games: [
        { game: "connections", solved: 205 },
        { game: "spelling_bee", solved: 104 },
        { game: "wordle", solved: 57 },
        { game: "midi", solved: 28 },
      ],
    },
  },
  "sub-7-wordle": {
    label: "Sub/Regi · 7 games · Wordle-led",
    data: {
      streak: { game: "wordle", days: 41 },
      days_all: 605,
      best_wordle_solve: { word: "quick", date: "Feb 9th, 2026", time: "8:02am" },
      top_connections_color: "green",
      games: [
        { game: "wordle", solved: 190 },
        { game: "connections", solved: 92 },
        { game: "spelling_bee", solved: 76 },
        { game: "mini", solved: 48 },
        { game: "midi", solved: 41 },
        { game: "crossword", solved: 66 },
        { game: "strands", solved: 27 },
      ],
    },
  },
  "sub-7-bee": {
    label: "Sub/Regi · 7 games · Spelling Bee-led",
    data: {
      streak: { game: "spelling_bee", days: 88 },
      days_all: 560,
      best_wordle_solve: { word: "slate", date: "Apr 12th, 2026", time: "6:40am" },
      top_connections_color: "purple",
      games: [
        { game: "spelling_bee", solved: 198 },
        { game: "crossword", solved: 112 },
        { game: "wordle", solved: 85 },
        { game: "midi", solved: 55 },
        { game: "mini", solved: 38 },
        { game: "connections", solved: 22 },
        { game: "strands", solved: 14 },
      ],
    },
  },
  anon: {
    label: "Anon",
    data: {
      community: {
        longest_streak: { game: "wordle", days: 365 },
        wordle_most_solved_word: "least",
        top_connections_color: "purple",
        games: [
          { game: "wordle", solved: 480000000 },
          { game: "connections", solved: 310000000 },
          { game: "spelling_bee", solved: 150000000 },
          { game: "mini", solved: 120000000 },
          { game: "midi", solved: 60000000 },
          { game: "crossword", solved: 50000000 },
          { game: "strands", solved: 34583917 },
        ],
      },
    },
  },
};

const STARTING_CARD = {
  personal: {
    lines: [
      { headline: "You played a streak of" },
      { "game-icon": "{streak.game}" },
      { display: "{streak.days} days" },
      { "label-bold": "of {streak.game}" },
    ],
  },
  anon: {
    lines: [
      { headline: "The longest streak was" },
      { "game-icon": "{community.longest_streak.game}" },
      { display: "{community.longest_streak.days} days" },
      { "label-bold": "of {community.longest_streak.game}" },
    ],
  },
};
