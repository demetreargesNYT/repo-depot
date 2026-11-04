"""The Mini's ball paths (2026-11-04, the speed solve): flights at the project's one gravity between the cubes' surfaces.

Everything here is in room space with the room's 0.85 scale applied (what the screen shows, the planes at rest). The ball's contact
radius is RC (centre to the surface it touches; the stroke sits a little into it). Each contact has its own restitution along the
normal (e) and along the surface (kt), so a path can be aimed; the build asserts the contacts come out in the order planned.
"""
import math

G = 0.40                                   # artboard units per frame squared
RC = 17.2 * 1.7                            # the ball's centre to what it rests on (ball scale 1.7)

# the surfaces the ball can meet (the upper cube's top is its mouth: the ball goes in, it never lands on it)
FLOOR_Y = 711.5
A_TOP = 625.1                              # the left box's top edge
A_RIGHT = 654.0                            # and its right side
C_LEFT = 755.9                             # the upper cube's left side (its back edge), from y 552 down to 633.4
C_TOP_BACK = 552.0
C_LOW = 633.4
SURFACES = {
    "left box top": ("seg", (543.4, A_TOP), (A_RIGHT, A_TOP), (0.0, -1.0)),
    "left box corner": ("pt", (A_RIGHT, A_TOP)),
    "left box side": ("seg", (A_RIGHT, A_TOP), (A_RIGHT, FLOOR_Y), (1.0, 0.0)),
    "floor": ("seg", (A_RIGHT, FLOOR_Y), (760.0, FLOOR_Y), (0.0, -1.0)),
    "upper cube side": ("seg", (C_LEFT, C_TOP_BACK), (C_LEFT, C_LOW), (-1.0, 0.0)),
    "upper cube corner": ("pt", (C_LEFT, C_TOP_BACK)),
    "upper cube low corner": ("pt", (C_LEFT, C_LOW)),
}


def _contact(p, v, s):
    """The surface's normal if the ball at p moving with v touches it (and is moving into it), else None."""
    if s[0] == "pt":
        d = math.dist(p, s[1])
        if d <= RC:
            n = ((p[0] - s[1][0]) / d, (p[1] - s[1][1]) / d)
            if v[0] * n[0] + v[1] * n[1] < 0:
                return n
        return None
    _, a, b, n = s
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    along = (p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1]
    off = (p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1]
    if 0 <= along <= L and -0.5 * RC <= off <= RC and v[0] * n[0] + v[1] * n[1] < 0:
        return n
    return None


def _reflect(v, n, e, kt):
    vn = v[0] * n[0] + v[1] * n[1]
    vt = (v[0] - vn * n[0], v[1] - vn * n[1])
    return (kt * vt[0] - e * vn * n[0], kt * vt[1] - e * vn * n[1])


def fly(p, v, rules, done, tmax=300, sub=8, extra=None):
    """The ball from p with velocity v (frame 0) until done(p, v) is true on a whole frame. rules: (e, kt) for each contact in
    turn. Each touch is found to the exact moment (by halving the step), and the whole frames are read off the parabola they fall
    on, so the path does not depend on the step size. Returns ([centre on frames 0..n], [(t, surface name, centre, v in, v out,
    normal)])."""
    x, y = p
    vx, vy = v
    dt = 1.0 / sub
    t = 0.0
    frames = [(x, y)]
    contacts = []
    last, t_last = None, -9.0
    at = lambda tau: (x + vx * tau, y + vy * tau + 0.5 * G * tau * tau)
    surfaces = dict(SURFACES, **(extra or {}))
    while t < tmax:
        hit = None
        for name, s in surfaces.items():
            if name == last and t + dt - t_last < 2:
                continue
            q = at(dt)
            if _contact(q, (vx, vy + G * dt), s):
                lo, hi = 0.0, dt
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if _contact(at(mid), (vx, vy + G * mid), s):
                        hi = mid
                    else:
                        lo = mid
                if hit is None or hi < hit[0]:
                    hit = (hi, name, s)
        step = hit[0] if hit else dt
        # whole frames inside this step lie on the current parabola
        while len(frames) <= t + step + 1e-12:
            frames.append(at(len(frames) - t))
            if done(frames[-1], (vx, vy + G * (len(frames) - 1 - t))):
                return frames, contacts
        x, y = at(step)
        vy += G * step
        t += step
        if hit:
            _, name, s = hit
            n = _contact((x, y), (vx, vy), s)
            assert len(contacts) < len(rules), f"an unplanned contact: {name} at {t:.1f}"
            e, kt = rules[len(contacts)]
            vin = (vx, vy)
            vx, vy = _reflect(vin, n, e, kt)
            contacts.append((t, name, (x, y), vin, (vx, vy), n))
            last, t_last = name, t
        at = lambda tau, x=x, y=y, vx=vx, vy=vy: (x + vx * tau, y + vy * tau + 0.5 * G * tau * tau)
    raise RuntimeError("the path never ended")


def spin_rate(vout, n, r):
    """The turn per frame a contact leaves the ball with (it grips): the speed along the surface over the radius, clockwise positive
    (on the floor, rolling right turns it clockwise; on a wall to its left, rising turns it anticlockwise)."""
    t = (-n[1], n[0])
    return (vout[0] * t[0] + vout[1] * t[1]) / r
