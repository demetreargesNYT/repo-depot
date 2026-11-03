// Scratch output for the browser tests goes in .cache/scratch.nosync/ (git-ignored), never /tmp (tools/scratch.py is the same rule for
// the Python tools). Sessions run in parallel, so each has its own subfolder, <ch1|ch2|ch3|shared>/, and SCRATCH is the caller's:
// YIG_SESSION if set to one of those, else the chapter the script was run on (its first ch1, ch2 or ch3 argument), else shared.
// chromeProfile() gives a test its own empty Chrome profile folder there, clears the ones an earlier run of the same test left
// behind, and removes its own when the test exits. It creates and deletes only inside the caller's subfolder.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", ".cache", "scratch.nosync");
const SESSIONS = ["ch1", "ch2", "ch3", "shared"];
export const SESSION = SESSIONS.includes(process.env.YIG_SESSION) ? process.env.YIG_SESSION
  : process.argv.slice(2).map((a) => a.match(/^(?:.*\/)?(ch[123])\/?$/)?.[1]).find(Boolean) ?? "shared";
export const SCRATCH = path.join(ROOT, SESSION);

const cleared = new Set();   // prefixes whose leftovers this process has already cleared
const HOUR = 3600 * 1000;

// The profiles go in <subfolder>/chrome/, or in YIG_CHROME_ROOT when the test runner sets it (a folder of its own run, inside the
// subfolder, so it can tell the Chrome windows it started from everyone else's). Only leftovers older than an hour are cleared:
// another run of the same test (another session, or the runner) may be using a newer one. Clearing is best effort: a folder
// Chrome still holds is left for next time.
export function chromeProfile(prefix) {
  const asked = process.env.YIG_CHROME_ROOT && path.resolve(process.env.YIG_CHROME_ROOT);
  const root = asked && asked.startsWith(SCRATCH + path.sep) ? asked : path.join(SCRATCH, "chrome");
  fs.mkdirSync(root, { recursive: true });
  if (!cleared.has(prefix)) {
    cleared.add(prefix);
    for (const name of fs.readdirSync(root)) {
      const old = path.join(root, name);
      try {
        if (name.startsWith(prefix) && Date.now() - fs.statSync(old).mtimeMs > HOUR) fs.rmSync(old, { recursive: true, force: true });
      } catch { /* still in use */ }
    }
  }
  const dir = fs.mkdtempSync(path.join(root, prefix));
  process.on("exit", () => { try { fs.rmSync(dir, { recursive: true, force: true }); } catch { /* Chrome may still hold a file: the next run clears it */ } });
  return dir;
}
