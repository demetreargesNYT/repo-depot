// Scratch output for the browser tests goes in .cache/scratch/ (git-ignored), never /tmp (tools/scratch.py is the same rule for
// the Python tools). chromeProfile() gives a test its own empty Chrome profile folder there, clears the ones an earlier run of the
// same test left behind, and removes its own when the test exits.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const SCRATCH = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", ".cache", "scratch");

const cleared = new Set();   // prefixes whose leftovers this process has already cleared

// A test may open several browsers one after another; the old profiles are cleared only on the first call, because a browser
// this run just closed can still be writing to its own. Clearing is best effort: a folder Chrome still holds is left for next time.
export function chromeProfile(prefix) {
  const root = path.join(SCRATCH, "chrome");
  fs.mkdirSync(root, { recursive: true });
  if (!cleared.has(prefix)) {
    cleared.add(prefix);
    for (const name of fs.readdirSync(root)) {
      if (name.startsWith(prefix)) { try { fs.rmSync(path.join(root, name), { recursive: true, force: true }); } catch { /* still in use */ } }
    }
  }
  const dir = fs.mkdtempSync(path.join(root, prefix));
  process.on("exit", () => { try { fs.rmSync(dir, { recursive: true, force: true }); } catch { /* Chrome may still hold a file: the next run clears it */ } });
  return dir;
}
