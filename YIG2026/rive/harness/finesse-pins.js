// The Finesse panel's pin comments, stage side. Review only: the server adds this file to /experience-stage when the address has
// ?finesse=1, right after the Rive runtime and before the integration imports it, so every Rive instance the integration makes is
// recorded here. Without ?finesse=1 it is never loaded. The panel (experience.html) asks it about the frame on screen:
//
//   piecesAt(x, y, tree)  the named pieces under and near an artboard point, on a paused live frame. Each named node of the file
//                         (the tree from tools/room_pieces.py) is hidden in turn (scale 0) for one redraw of the same moment, and
//                         a piece counts where hiding it changes the pixels around the point: tools/safe_area.py's test, in the
//                         browser. Each hide is compared with a redraw that touches the same piece by a hair (scale x 0.999999),
//                         because touching any piece makes Rive update a little more than an untouched redraw does. It descends
//                         into the pieces that change and names the deepest. No time passes in a redraw (the Finesse clock draws
//                         the held frame again), and the last redraw puts the frame back.
//   still(x, y, label)    the frame on screen as a PNG, one pixel per artboard unit, with the pin and the window's crop drawn on it.
//   rect()                where the artboard sits in the stage's window.
(() => {
  if (!window.rive || window.__yigPins) return;
  const AB_W = 1495, AB_H = 1067;
  const UNDER = 3;                  // artboard units: a piece whose pixels change this close to the point is under it
  const NEAR = 40;                  // and one within this distance is near it
  const THRESHOLD = 24;             // per-channel difference that counts as a change (tools/safe_area.py's)
  const WRAPPER = / (Art|Spin|Scale|Gate)$/;   // rig groups: a hit on one is named after the piece around it

  const instances = [];
  const base = window.rive;
  class TrackedRive extends base.Rive {
    constructor(options) { super(options); instances.push(this); }
  }
  window.rive = { ...base, Rive: TrackedRive };   // the stage's import map reads window.rive when the integration first imports it

  // the instance whose canvas is on screen (the last visible one, as the Finesse clock picks it)
  const onScreen = () => instances.filter((r) => r.canvas?.isConnected && r.canvas.style.visibility !== "hidden" && r.artboard).pop() || null;

  // while `touch` is set, the artboard's next draw scales that piece by touch.k (0 hides it), advances by 0 so it shows, draws, and
  // puts it back: after the state machine has applied its keys, so a keyed scale cannot undo it
  let touch = null;
  function hook(r) {
    const ab = r.artboard;
    if (ab.__yigPins) return;
    const draw = ab.draw;
    ab.draw = function (renderer) {
      const t = touch && touch.ab === ab ? touch : null;
      let sx = 1, sy = 1;
      if (t) { sx = t.tc.scaleX; sy = t.tc.scaleY; t.tc.scaleX = sx * t.k; t.tc.scaleY = sy * t.k; ab.advance(0); }
      draw.call(ab, renderer);
      if (t) { t.tc.scaleX = sx; t.tc.scaleY = sy; }
    };
    ab.__yigPins = true;
  }

  // the canvas pixels in a square of NEAR units around the point
  function grab(r, x, y) {
    const c = r.canvas, kx = c.width / AB_W, ky = c.height / AB_H;
    const x0 = Math.max(0, Math.floor((x - NEAR) * kx)), y0 = Math.max(0, Math.floor((y - NEAR) * ky));
    const x1 = Math.min(c.width, Math.ceil((x + NEAR) * kx)), y1 = Math.min(c.height, Math.ceil((y + NEAR) * ky));
    if (x1 <= x0 || y1 <= y0) return null;
    return { x0, y0, w: x1 - x0, h: y1 - y0, kx, ky, data: c.getContext("2d").getImageData(x0, y0, x1 - x0, y1 - y0).data };
  }
  // the distance from the point to the nearest pixel that changed, in artboard units (Infinity: none within NEAR)
  function nearest(a, b, x, y) {
    let best = Infinity;
    for (let j = 0; j < a.h; j++) {
      for (let i = 0; i < a.w; i++) {
        const o = 4 * (j * a.w + i);
        if (Math.abs(a.data[o] - b.data[o]) > THRESHOLD || Math.abs(a.data[o + 1] - b.data[o + 1]) > THRESHOLD
          || Math.abs(a.data[o + 2] - b.data[o + 2]) > THRESHOLD || Math.abs(a.data[o + 3] - b.data[o + 3]) > THRESHOLD) {
          const d = Math.hypot((a.x0 + i + 0.5) / a.kx - x, (a.y0 + j + 0.5) / a.ky - y);
          if (d < best) best = d;
        }
      }
    }
    return best <= NEAR ? best : Infinity;
  }

  function piecesAt(x, y, tree) {
    const clock = window.__yigClock;
    const r = onScreen();
    if (!clock?.redraw || !clock.paused || clock.stepsBehind() > 0 || !r || !tree) return null;
    hook(r);
    const ab = r.artboard;
    const drawn = (tc, k) => { touch = { ab, tc, k }; clock.redraw(); touch = null; return grab(r, x, y); };
    if (!clock.redraw() || !grab(r, x, y)) return null;
    const found = new Map();        // name: { d, path }
    let hits = 0;
    const walk = (nodes, around, path) => {
      for (const node of nodes) {
        const tc = ab.transformComponent(node.n);
        if (!tc) continue;
        const ref = drawn(tc, 0.999999);
        const d = nearest(ref, drawn(tc, 0), x, y);
        if (d === Infinity) continue;
        const name = WRAPPER.test(node.n) && around ? around : node.n;
        const here = WRAPPER.test(node.n) && around ? path : [...path, node.n];
        const had = hits;
        walk(node.c, name, here);
        if (hits === had && !(found.get(name)?.d <= d)) { found.set(name, { d, path: here }); hits++; }
      }
    };
    try { walk(tree, "", []); } finally { touch = null; clock.redraw(); }
    // each piece with the group it sits in (its parent, past the rig groups) and its whole path from the file's top group
    const list = [...found].map(([name, f]) => ({ name, in: f.path.at(-2) ?? null, d: Math.round(f.d), path: f.path.slice(1) })).sort((a, b) => a.d - b.d);
    return { under: list.filter((p) => p.d <= UNDER), near: list.filter((p) => p.d > UNDER) };
  }

  const rect = () => document.getElementById("artboard").getBoundingClientRect();

  // the pin as drawn on the stills and on the stage: a ring around the point (so what is under it still shows) and its number
  function drawPin(g, x, y, label) {
    g.save();
    g.lineWidth = 7; g.strokeStyle = "#FFFFFF";
    g.beginPath(); g.arc(x, y, 26, 0, 2 * Math.PI); g.stroke();
    g.lineWidth = 3.5; g.strokeStyle = "#C2570A";
    g.beginPath(); g.arc(x, y, 26, 0, 2 * Math.PI); g.stroke();
    g.fillStyle = "#C2570A"; g.strokeStyle = "#FFFFFF"; g.lineWidth = 3;
    g.beginPath(); g.arc(x + 34, y - 34, 17, 0, 2 * Math.PI); g.fill(); g.stroke();
    g.fillStyle = "#FFFFFF"; g.font = "700 20px Helvetica, Arial, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText(label, x + 34, y - 33);
    g.restore();
  }

  function still(x, y, label) {
    const src = window.__yigClock?.frameCanvas?.() || onScreen()?.canvas;
    if (!src || !src.width) return null;
    const out = document.createElement("canvas");
    out.width = AB_W; out.height = AB_H;
    const g = out.getContext("2d");
    g.drawImage(src, 0, 0, AB_W, AB_H);
    const a = rect();                                   // the window's crop, in artboard units
    const cx0 = Math.max(0, (-a.left / a.width) * AB_W), cy0 = Math.max(0, (-a.top / a.height) * AB_H);
    const cx1 = Math.min(AB_W, ((innerWidth - a.left) / a.width) * AB_W), cy1 = Math.min(AB_H, ((innerHeight - a.top) / a.height) * AB_H);
    g.save();
    g.setLineDash([14, 9]); g.lineWidth = 3; g.strokeStyle = "rgba(18, 18, 18, .6)";
    g.strokeRect(cx0 + 1.5, cy0 + 1.5, cx1 - cx0 - 3, cy1 - cy0 - 3);
    g.restore();
    drawPin(g, x, y, label);
    return out.toDataURL("image/png");
  }

  window.__yigPins = { piecesAt, still, rect, instances };
})();
