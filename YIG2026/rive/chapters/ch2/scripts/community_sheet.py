"""A schematic bounce sheet for the Community room, drawn from the build's own numbers (no Rive render: Chapter 2 has no helper that
renders a copy of a project). Run from chapters/ch2/scripts: python3 community_sheet.py <out.png>. Also prints the beat table."""
import sys

from PIL import Image, ImageDraw

import community as c

out = sys.argv[1]
p = c.plan()["loop"]
beats = [("gather", c.LAUNCH - 5), ("launch", c.LAUNCH + 2), ("top", c.LAUNCH + 17), ("mouse out", c.LAUNCH + 11),
         ("mouse darts", c.LAUNCH + 20), ("ball lands", c.LAUNCH + 36), ("bird lands", c.LAUNCH + 44)]
W, H, Z = 150, 190, 2
x0, x1, y0, y1 = 560, 935, 520, 720
sheet = Image.new("RGB", (len(beats) * W, H * Z // 2 + 20), "#E7F1E1")
d = ImageDraw.Draw(sheet)
for i, (name, f) in enumerate(beats):
    ox = i * W
    s = 0.4
    def X(x): return ox + (x - 600) * s
    def Y(y): return (y - y0) * s
    d.rectangle([ox, Y(712), ox + W, H], fill="#FEA0C9")
    d.line([ox, Y(712), ox + W, Y(712)], fill="#1F1F1F", width=1)
    cy = p["cy"][f]
    sy = p["sy"][f]
    r = c.R
    bottom = cy + r
    top = bottom - 2 * r * sy
    d.ellipse([X(c.BALL_X - r / sy), Y(top), X(c.BALL_X + r / sy), Y(bottom)], fill="#FF5959", outline="#1F1F1F")
    by = p["bird_y"][f]
    d.rectangle([X(c.BALL_X + c.BIRD_DX - 28), Y(by - 36), X(c.BALL_X + c.BIRD_DX + 15), Y(by + 5)], outline="#8A9A00")
    if p["feet"][f]:
        d.line([X(c.BALL_X - 2), Y(by + 5), X(c.BALL_X + 2), Y(by + 5)], fill="#1F1F1F")
    mx = p["mouse_x"][f]
    d.rectangle([X(c.HOLE_X - 9), Y(693), X(c.HOLE_X + 9.5), Y(712)], outline="#1F1F1F")
    if mx < c.HOLE_X + 21.8:
        d.ellipse([X(mx - 12), Y(701), X(mx), Y(711)], fill="#DFDBD7", outline="#1F1F1F")
    d.text((ox + 4, H * Z // 2 - 8), f"{name} f{f - c.LAUNCH:+d}", fill="#1F1F1F")
sheet.save(out)
print(out)
t = lambda f: f - c.LAUNCH
vis = [f for f in range(c.L + 1) if p["mouse_x"][f] < c.HOLE_X + 21.8]
print("mouse visible frames", t(vis[0]), "to", t(vis[-1]), "=", len(vis), "frames", len(vis) / 60)
gap = [(f, p["bird_y"][f] - 0) for f in range(c.L + 1)]
print("ball apex rise", c.RISE, "air frames", c.T, "bottom above hole top", c.RISE - 19.5)
print("bird top rise", c.BIRD_TOP, "gap at ball apex", c.bird_h(c.T / 2) - c.top_h(c.T / 2), "gap at ball landing", c.bird_h(c.T) - c.top_h(c.T))
print("max gap", max(c.bird_h(t_ / 4) - c.top_h(t_ / 4) for t_ in range(0, int(c.TE * 4))))
print("bird delay", c.BIRD_DELAY, "frames", c.BIRD_DELAY / 60)
print("feet visible frames", t(min(f for f in range(c.L + 1) if p["feet"][f])), t(max(f for f in range(c.L + 1) if p["feet"][f])))
print("mouse fully hidden at t", t(vis[-1]) + 1, "; ball bottom drops below hole top at t", c.T - 3.2)
