# Setting up one home for the Rive work

## The recommendation

Do all the Rive work in **Claude Code in VS Code, in one git repo, `yig-rive`**. Keep `CLAUDE.md` at its root so every session starts with every decision already loaded.

- **Rive CLI as the main tool.** The file is text, so changes are reviewable and diffable, and every push lands in the Team folder file as a named revision.
- **Rive MCP as the second tool.** Connect it for the times the Editor is open and you want Claude Code to work on the live file.
- **A local harness page instead of the GSAP prototype.** It plays the real `.riv` with Rive's web runtime and the real text CSS, with a button per scene. That way you're tuning the actual file engineering will ship, and the same page is what you show them.
- **Git, alongside Rive's own revision history.** Rive keeps revisions per file. Git keeps the RML diffs, the specs and the engineering files together, and lets you tag what you handed off.
- **Your engineering repo (repo-depot) only gets finished files.** At each milestone, copy the `.riv` and the `engineering/` files over in their own commit or PR.

Use this chat and the Claude project only for thinking, writing and reviews, if you want them at all. Nothing that has to stay current should live here.

## Steps

1. **Create the repo.** Unzip `yig-rive.zip` to `~/Desktop/rive-tests/yig-rive/`, open that folder in VS Code, and start Claude Code there.
2. **Paste this into Claude Code to move everything in:**

```
Read CLAUDE.md and SETUP.md. Then set this repo up:
1. git init, with a .gitignore that ignores build/ folders and .DS_Store.
2. Move the Chapter 2 Rive project from ~/Desktop/rive-tests/yig-ch2 into chapters/ch2, keeping its
   rive.yaml link to "YIG Chapter 2" (file 2677803). Run rive pull chapters/ch2 to confirm the link
   still works and the project matches revision 48903415.
3. Copy ~/Desktop/rive-tests/yig-test/engineering/chapter-2-integration.js into engineering/. It has
   the view model changes you made. The art and spec are already in this repo.
4. If there's a Chapter 1 Rive project, link it as chapters/ch1 the same way. Don't change it.
5. Commit: "Bring Chapter 1 and 2 Rive work into one repo".
Tell me what you moved and anything that didn't match.
```

3. **Connect the Rive MCP**, once. In a terminal: `claude mcp add --transport http rive http://127.0.0.1:9791/mcp`. It only works while the Rive desktop Editor is open.
4. **Build the harness:**

```
Build harness/index.html: a local page that loads chapters/chN/build/*.riv with the Rive web runtime,
on a canvas shaped like the 1495 × 1067 artboard with a phone-crop toggle. Give it a button per scene
value and a frames list that sets scene the way engineering will, using engineering/chapter-2-integration.js
as-is, plus the HTML text layer with engineering/yig-text-motion.css. Serve it with a simple local
server. It has to show the real file, with no stand-ins.
```

5. **Restructure Chapter 2 for multiple games** by following `docs/scene-restructure.md`:

```
Do docs/scene-restructure.md on chapters/ch2, in stages: backdrops and wall lag wrappers, then intros
and outros, then the state machine. Verify, screenshot and push at each stage, and compare against
reference/chapter-2-prototype.html. Then update engineering/chapter-2-integration.js and check it
in the harness.
```

## Day to day

- **Adjusting motion:** ask Claude Code for the change ("make the pan 1.3 s and keep the intro at 3.2 s"), then look at it in the harness. Or tweak it by hand in the Editor, then ask Claude Code to `rive pull` and commit.
- **A new game or chapter:** import its art in the Editor, pull, write its section of the spec, then build in stages.
- **Handing off:** push a named revision, tag it in git, then copy the `.riv` and `engineering/` files into repo-depot.
