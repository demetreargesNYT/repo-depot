"""ball_physics at any ball size: the world is scaled so the ball's contact radius is ball_physics' RB, and gravity with it."""
import common  # noqa: F401  (puts tools on the path)
import ball_physics as bp
from common import G


class World:
    def __init__(self, Rc):
        self.s = bp.RB / Rc

    def seg(self, a, b, **kw):
        s = self.s
        return bp.Seg((a[0] * s, a[1] * s), (b[0] * s, b[1] * s), **kw)

    def circ(self, c, r, **kw):
        s = self.s
        return bp.Circ((c[0] * s, c[1] * s), r * s, **kw)

    def run(self, p, v, surfaces, frames=400, **kw):
        """Simulate, and sample the path on whole frames 0..frames while the scaled gravity is still in force (the flights' position
        functions read ball_physics.G when they are called). Returns (events, {frame: ((x, y), mode)})."""
        s = self.s
        bp.G = G * s
        try:
            ev = bp.simulate((p[0] * s, p[1] * s), (v[0] * s, v[1] * s), 0.0, surfaces, **kw)
            pieces = bp.build_path(ev, (p[0] * s, p[1] * s), (v[0] * s, v[1] * s), 0.0)
            path = {}
            for f in range(frames + 1):
                q, mode = bp.piece_at(pieces, f)
                path[f] = ((q[0] / s, q[1] / s), mode)
        finally:
            bp.G = G
        return ev, path

    def describe(self, ev):
        s = self.s
        out = []
        for e in ev:
            if e[0] == "hit":
                _, t, srf, p, vi, vo = e
                out.append(f"hit {srf.name} t {t:.1f} at ({p[0]/s:.1f},{p[1]/s:.1f}) in ({vi[0]/s:.2f},{vi[1]/s:.2f}) out ({vo[0]/s:.2f},{vo[1]/s:.2f})")
            elif e[0] == "roll":
                _, t0, t1, seg, s0, s1, v0, v1, kind, extra = e
                out.append(f"roll {seg.name} t {t0:.1f}-{t1:.1f} v {v0/s:.2f}->{v1/s:.2f} {kind}")
            else:
                out.append(f"leave t {e[1]:.1f} at ({e[2][0]/s:.1f},{e[2][1]/s:.1f})")
        return out
