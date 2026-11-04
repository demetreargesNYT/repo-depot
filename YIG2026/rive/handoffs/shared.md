# Handoff: shared-files session (2026-11-04)

**Rooms owned:** none. This session owns the harness, `CLAUDE.md`, `docs/`, the shared tools, `engineering/` and the package script.

**Open notes:** none of mine. Chapter 2's file (`finesse-notes/ch2.md`) has 1 note still `Status: open`, for the Chapter 2 session. Chapter 1's 12 are all done.

**Done this session** (all committed; GitHub has everything up to `9871650`; 11 newer commits are local only):
- Finesse panel: pin comments (C key; the pieces under a pin worked out from the build; Send to Claude writes `finesse-notes/ch<N>.md` and stills), pins only in Comment mode, the timecode as the room's own intro or loop frame (return visits too).
- CLAUDE.md: parallel-session rules, the push lock, hidden loop resets, the several-rooms pattern, illustrator imports.
- Scratch subfolders per session; the suite kills only what it started; `npm run open-package`.
- Ad cards have no copy (no flash when leaving an ad); Wordle Bot's position in the guide.

**Decisions not yet in CLAUDE.md**
- A send covering two chapters keeps the panel's numbers in each file (the second file's section doesn't restart at 1).
- When a chapter session edits a harness file, the shared session commits it, only when Demetre says.
- Demetre may approve a review-server restart; done twice this session (14:55 on 11-03, 07:35 on 11-04).

**Open questions for Demetre**
- The guide's Wordle Bot head (x 868.4, y 533.4) is stale: card 5 round 3 places the bubble from x 755.7, y 376.5. Update the guide when card 5 settles?
- Ad cards keep an empty copy element, because `experience-test.mjs` expects one per card. Drop it and change the test?
- The package hasn't been rebuilt since the ad fix, so its example still has the ad copy until the next build.
- The panel's return-visit loop frame wasn't tested on its own (only first visits and a pin).

**Uncommitted shared files** (changed by the chapter sessions, not by me; commit by path when Demetre says):
- `harness/experience-stage.html`: Chapter 1's card 5 round 3 bubble placement.
- `tools/ball_speed_accepted.json`: "as drawn" entries from the chapter sessions.
- `docs/rooms.md`, `docs/rooms-ch1.md`, `docs/rooms-ch3.md`: the chapters' rooms sheets.

**Rive:** nothing pushed by this session, nothing waiting for approval, and no `.cache/rive-push.lock` left.

**Next step:** wait for Demetre's word to commit the five chapter-session files above, then wrap-up: push `main` to GitHub, rebuild the package (`python3 tools/package_engineering.py`) and update `docs/rive-plan.md`.

**Tools for checks:** Playwright (`playwright-core`) is in `.cache/scratch.nosync/shared/pw/`; the one-off checks there drive the system Chrome. For a check that needs new `serve.mjs` code, run a second server on 8766 (`PORT=8766 node serve.mjs`) and stop only that one.
