# Harness

A local page that plays a chapter's real built `.riv` with Rive's web runtime (pinned to 2.45.0, served from `node_modules`), driven by `engineering/chapter-2-integration.js` and `engineering/yig-text-motion.css` exactly as engineering will use them. The copy is placeholder text from the prototype.

```bash
cd harness
npm install        # once
npm start          # http://127.0.0.1:8765/
CHAPTER=ch1 PORT=9000 npm start   # another chapter or port
```

- The server rebuilds the `.riv` with `rive --once` whenever `scene.rml` is newer than the build, so reload the page after an edit.
- **Tap** runs engineering's `onTap()`. **Restart** reloads the file and the integration code. The scene buttons set the file's number directly, as a shortcut.
- The page reads the integration file's source: with `chapterFrames` it uses the scene style (frame list, one `scene` value); without it, the game + frame style.
- The only addition to the integration source is one appended `export { onTap, yig }` line, so the page can call `onTap`.
