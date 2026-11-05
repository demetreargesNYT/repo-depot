# Handoff: shared-files session (2026-11-05), for the engineering-handoff chat

**Rooms owned:** none. This session owns the harness, `CLAUDE.md`, `docs/`, the shared tools, `engineering/` and the package script.

**The last delivered package**
- `deliver/yig-engineering-package.zip` (320,856 bytes), the only zip there, built **2026-11-03 13:43** by `python3 tools/package_engineering.py`. Nothing has been built since (none on 11-04 or 11-05). The unzipped copy from that build is `.cache/scratch.nosync/shared/yig-engineering-package/` (same time).
- Built from `824e869` plus the guide and CSS wording edits committed the same minute as `2ac7464` (13:43). Its `.riv` files match the Rive revisions of that delivery: File 1 49418454, File 2 49418480, File 3 49418501, tags `rive/chN-chapter-1-polish-startscene`. It still uses the **old scene names**.
- Rive has moved on since: the latest tags are `rive/ch1-chapter-1-update` (`e841a91`), `rive/ch2-chapter-2-update` (`d980828`) and `rive/ch3-chapter-3-update` (`d734fb1`), all 2026-11-05. The next package must be rebuilt from the current `main`.

**The guide (`docs/engineering-guide.md`), committed in `49ee665`**
- Section 3 has the new **Scenes** table (every scene in flow order, with its file, the Regi/Sub and Anon cards that use it, and Demetre's notes) and the **Renamed scenes** table (old to new, for engineers who have the 11-03 package).
- Also updated: "What's new" (neutral names, scenes that share a room, Chapter 4's three scenes), rule 6, rule 11 (three waits, no 1.45 s reveal wait), the properties table, section 5's card lists and examples, section 6's wait table, section 8 and the checklist.
- **Stale now, fix first:** the Chapter 3 session renamed File 3's `topGame` value `daily` to `crossword` in `a5fd7f6` (after my commit). These all still say or send `daily` for The Crossword's `topGame` and need changing to `crossword`:
  - the guide's properties table and the line above the Renamed table ("`topGame` still calls The Crossword `daily`"); add `topGame` `daily` to `crossword` to the Renamed table;
  - `harness/experience-stage.html` (`TOPGAME_VALUE`, which maps crossword to daily);
  - `engineering/react/src/cards.ts` (the `top === 'crossword' ? 'daily'` mapping) and the `topGame?: string` comment in `types.ts`.
  Until then a Crossword top game gets no fireworks or colour in the harness and the React example.

**Half-done**
- `docs/rive-plan.md` "Changes since the last delivery" has no entry yet for the rename, the new per-card scenes, same-room scene changes (0.34 s, no pan) or the removed 1.45 s reveal wait. The next note to engineering is made from that list.
- The package hasn't been rebuilt, and smoke and the suite haven't run against the new names. Checks run so far: `npm run check` for all three chapters (pass), `npm run finesse` once per chapter (pass), and a one-off walk of File 3's cards for subscriber and anon (every scene and wait right; `.cache/scratch.nosync/shared/pw/scenes-check.mjs`). `npm run experience` and `npm run text` were updated but not run.

**Open items for Demetre** (from the last report)
1. `topGame`'s Crossword value: resolved by the Chapter 3 session (`crossword`); only the follow-up above remains.
2. Chapter 4's wall fade: the old 1.45 s copy wait on `reveal` is removed, so the `chapter-4-top-game` copy arrives 0.34 s after the tap while the wall is still fading. Restore it?
3. Ad 3 is still File 2's `to-chapter-3` card (the same picture as File 3's `ad`); his list put it on File 3's `ad`. Which?
4. Badge card order: the cards run event badges, then achievement (personal) badges; the File 3 manifest lists `chapter-3-personal-badges` first. Swap?
5. The "Chapter 4" ball check reports 0 contacts (Chapter 3 session's to look at).

**Decisions not yet in CLAUDE.md**
- Demetre may approve a review-server restart (done 11-03 14:55 and 11-04 07:35).

**Uncommitted shared files:** none from this session. The chapter sessions keep adding to `docs/rooms*.md` and `tools/ball_speed_accepted.json`; commit them by path at the wrap-up.

**Rive:** this session pushed nothing; no `.cache/rive-push.lock` left. Chapter sessions now push on their own ("Pushing on your own" in CLAUDE.md).

**Next step:** fix the stale `topGame` `daily` references above, add the rename entries to "Changes since the last delivery", get Demetre's answers to items 2 to 4, then rebuild the package and run smoke (ask him first about the suite).

**Tools for checks:** Playwright (`playwright-core`) is in `.cache/scratch.nosync/shared/pw/`; the one-off checks there drive the system Chrome. For a check that needs new `serve.mjs` code, run a second server on 8766 (`PORT=8766 node serve.mjs`) and stop only that one.
