// The Finesse panel's clock. Review only: the server adds this file to /experience-stage when the address has ?finesse=1
// (the panel on /experience asks for it), before the Rive runtime loads. With it, the Rive animation runs on a clock the
// panel controls: pause and play, 0.5x speed, one frame at a time forward, and one frame at a time back through the last
// couple of seconds. Without ?finesse=1 this file is never loaded and the stage is exactly the engineering page.
//
// How: the Rive runtime asks the page for each frame with requestAnimationFrame(callback) and advances its animations by
// the difference between the timestamps it is handed. Here those requests are held in a queue and answered with a time we
// choose (a "virtual" time). Pause stops handing out frames, speed scales the step, and a single step hands out exactly
// 1/60 s. The runtime cannot run backwards, so every frame drawn is also copied (reduced in size) into a short buffer of
// the last 2 s; stepping back shows those copies over the live canvas.
//
// Not slowed or paused: the integration's own timers (copy delays, held taps), which keep real time. Taps while paused or
// at 0.5x still set Rive's properties at once; the animation moves on as the clock does.
(() => {
  if (window.__yigClock) return;
  const nativeRaf = window.requestAnimationFrame.bind(window);
  const nativeCancel = window.cancelAnimationFrame.bind(window);
  const FRAME_MS = 1000 / 60;        // the files are authored at 60 fps
  const BUFFER = 120;                // frames kept for stepping back: 2 s
  const CAPTURE_W = 420;             // width of the kept copies (reduced, to keep the buffer small)

  const clock = {
    paused: false,
    speed: 1,
    time: 0,                         // virtual milliseconds since the page started
    view: 0,                         // 0: live; n: showing the copy n frames behind the live frame
    onFrame: null,                   // called after each virtual frame is drawn
  };

  // ---- the frame queue: only the Rive runtime's own scheduler (a bound function) is held; the page's callbacks stay real
  let queue = [];
  let ids = 0;
  const t0 = performance.now();
  window.requestAnimationFrame = (cb) => {
    if (typeof cb !== "function" || !/^bound/.test(cb.name)) return nativeRaf(cb);
    queue.push({ id: ++ids, cb });
    return -ids;
  };
  window.cancelAnimationFrame = (id) => {
    if (id < 0) queue = queue.filter((e) => e.id !== -id);
    else nativeCancel(id);
  };

  // ---- the buffer of recent frames
  const ring = [];                   // { time, canvas }, oldest first
  let spare = [];                    // canvases to reuse
  let ghost = null;                  // the canvas that shows an older frame over the live one
  const liveCanvas = () => [...document.querySelectorAll("canvas.yig-file")].filter((c) => c.style.visibility !== "hidden").pop() || null;

  function capture() {
    const src = liveCanvas();
    if (!src || !src.width) return;
    const w = CAPTURE_W, h = Math.max(1, Math.round((src.height * w) / src.width));
    if (ring.length && (ring[0].canvas.width !== w || ring[0].canvas.height !== h)) { spare = []; ring.length = 0; } // the size changed
    const entry = ring.length >= BUFFER ? ring.shift() : { time: 0, canvas: spare.pop() || document.createElement("canvas") };
    entry.canvas.width = w;
    entry.canvas.height = h;
    entry.canvas.getContext("2d").drawImage(src, 0, 0, w, h);
    entry.time = clock.time;
    ring.push(entry);
  }

  function showHistory() {
    const live = liveCanvas();
    if (!live) return;
    if (clock.view <= 0 || !ring.length) { if (ghost) ghost.style.display = "none"; return; }
    const entry = ring[Math.max(0, ring.length - 1 - clock.view)];
    if (!ghost) {
      ghost = document.createElement("canvas");
      ghost.className = "yig-file";
      ghost.style.pointerEvents = "none";
      ghost.style.zIndex = "5";
    }
    if (ghost.parentNode !== live.parentNode) live.parentNode.append(ghost);
    ghost.width = entry.canvas.width;
    ghost.height = entry.canvas.height;
    ghost.style.display = "block";
    ghost.getContext("2d").drawImage(entry.canvas, 0, 0);
  }

  // ---- one virtual frame
  function runFrame(dt) {
    clock.time += dt;
    const batch = queue;
    queue = [];
    for (const e of batch) {
      try { e.cb(t0 + clock.time); } catch (err) { console.error(err); }
    }
    capture();
    if (clock.onFrame) clock.onFrame(clock);
  }

  // the HTML copy's CSS animations follow the same pause and speed (the integration's timers do not)
  function syncAnimations() {
    const hold = clock.paused || clock.view > 0;
    for (const a of document.getAnimations()) {
      if (a.playbackRate !== clock.speed) a.playbackRate = clock.speed;
      if (hold && a.playState === "running") { a.pause(); a.__held = true; }
      else if (!hold && a.__held) { a.play(); a.__held = false; }
    }
  }

  let last = null;
  let steps = 0;                     // single steps asked for
  function tick(now) {
    nativeRaf(tick);
    const real = last === null ? 0 : Math.min(now - last, 100);
    last = now;
    syncAnimations();
    if (clock.view > 0) {            // showing the past: playing walks forward through it to the live frame
      if (!clock.paused) { clock.view--; showHistory(); }
      return;
    }
    if (steps > 0) { while (steps-- > 0) runFrame(FRAME_MS); steps = 0; return; }
    if (clock.paused) return;
    runFrame(real * clock.speed);
  }
  nativeRaf(tick);

  // ---- what the panel uses
  clock.setPaused = (p) => { clock.paused = !!p; };
  clock.setSpeed = (s) => { clock.speed = s; };
  clock.stepForward = () => {
    if (clock.view > 0) { clock.view--; showHistory(); } else steps++;
  };
  clock.stepBack = () => {
    if (clock.view < ring.length - 1) { clock.view++; showHistory(); }
  };
  clock.stepsBehind = () => clock.view;
  clock.available = () => ring.length - 1 - clock.view;      // frames still to step back through
  clock.shownTime = () => (clock.view > 0 && ring.length ? ring[Math.max(0, ring.length - 1 - clock.view)].time : clock.time);
  window.__yigClock = clock;
})();
