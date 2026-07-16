#!/usr/bin/env python3
"""Rebuilds data.json from GPX in planned/ (gray underlay) and gpx/ (ridden legs).
Auto-detects timestamps/elevation (e.g. Strava exports) and computes stats."""
import re, math, json, glob, os, datetime

PALETTE = ["#e63946","#2a9d8f","#f4a261","#457b9d","#8338ec","#ff006e",
           "#06d6a0","#ffbe0b","#3a86ff","#fb5607","#118ab2","#9b2226"]

def load(path):
    d = open(path, encoding="utf-8", errors="replace").read()
    pts = []
    for m in re.finditer(r'<trkpt\b([^>]*?)(?:/>|>(.*?)</trkpt>)', d, re.S):
        attrs, body = m.group(1), m.group(2) or ""
        la = re.search(r'lat="([-\d.]+)"', attrs); lo = re.search(r'lon="([-\d.]+)"', attrs)
        if not (la and lo): continue
        ele = re.search(r'<ele>([-\d.]+)</ele>', body)
        tim = re.search(r'<time>([^<]+)</time>', body)
        t = None
        if tim:
            try:
                t = datetime.datetime.fromisoformat(tim.group(1).replace("Z", "+00:00")).timestamp()
            except ValueError:
                pass
        pts.append((float(la.group(1)), float(lo.group(1)),
                    float(ele.group(1)) if ele else None, t))
    name = os.path.splitext(os.path.basename(path))[0].replace(" - ", " → ")
    name = re.sub(r'^0*(\d+)\s*', lambda m: f"Day {m.group(1)}: ", name)
    return name, pts

def seg_mi(a, b):
    R = 3958.8
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(b[1]-a[1])/2)**2
    return 2*R*math.asin(math.sqrt(h))

def stats(pts):
    """Moving time, avg moving speed, elevation gain — only if timestamps exist."""
    timed = [p for p in pts if p[3] is not None]
    out = {}
    if len(timed) >= 2:
        moving = 0.0; mdist = 0.0
        for a, b in zip(timed, timed[1:]):
            dt = b[3] - a[3]
            if dt <= 0 or dt > 300: continue          # gaps/pauses don't count
            d = seg_mi(a, b)
            if d / (dt/3600) > 1.5:                   # >1.5 mph = moving
                moving += dt; mdist += d
        if moving > 60:
            h, m = int(moving//3600), int(moving%3600//60)
            out["moving"] = f"{h}h {m:02d}m"
            out["avg"] = round(mdist/(moving/3600), 1)
        start = datetime.datetime.fromtimestamp(timed[0][3], datetime.timezone.utc)
        out["date"] = start.strftime("%b %-d")
    eles = [p[2] for p in pts if p[2] is not None]
    if len(eles) > 10:
        gain, ref = 0.0, eles[0]
        for e in eles:
            if e > ref + 3: gain += e - ref; ref = e   # 3 m hysteresis vs GPS noise
            elif e < ref: ref = e
        out["elev"] = int(gain * 3.28084)
    return out

def perp(p, a, b):
    k = math.cos(math.radians((a[0]+b[0])/2))
    ax, ay, bx, by, px, py = a[1]*k, a[0], b[1]*k, b[0], p[1]*k, p[0]
    dx, dy = bx-ax, by-ay
    if dx == dy == 0: return math.hypot(px-ax, py-ay)
    t = max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))

def simplify(pts, target):
    if len(pts) <= target: return pts
    def dp(eps):
        stack, keep = [(0, len(pts)-1)], [False]*len(pts)
        keep[0] = keep[-1] = True
        while stack:
            i, j = stack.pop()
            dmax, idx = 0, -1
            for k in range(i+1, j):
                dd = perp(pts[k], pts[i], pts[j])
                if dd > dmax: dmax, idx = dd, k
            if dmax > eps and idx > 0:
                keep[idx] = True; stack += [(i, idx), (idx, j)]
        return [p for p, f in zip(pts, keep) if f]
    lo, hi, best = 1e-7, 0.5, None
    for _ in range(30):
        mid = (lo+hi)/2; r = dp(mid)
        if best is None or abs(len(r)-target) < abs(len(best)-target): best = r
        if len(r) > target: lo = mid
        else: hi = mid
    return best

def build(folder, target, with_stats):
    out = []
    for i, f in enumerate(sorted(glob.glob(folder + "/*.gpx"))):
        name, pts = load(f)
        if len(pts) < 2:
            print(f"skip {f}: no track points"); continue
        lls = [(p[0], p[1]) for p in pts]
        s = simplify(lls, target)
        leg = {
            "name": name,
            "color": PALETTE[i % len(PALETTE)],
            "miles": round(sum(seg_mi(a, b) for a, b in zip(lls, lls[1:])), 1),
            "pts": [[round(a, 5), round(b, 5)] for a, b in s],
        }
        if with_stats:
            st = stats(pts)
            if st: leg["stats"] = st
        out.append(leg)
        print(f"{f}: {len(pts)} pts -> {len(s)}, {leg['miles']} mi, stats={leg.get('stats')}")
    return out

legs = build("gpx", 1500, True)
planned = build("planned", 900, False)
out = {
    "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "legs": legs, "planned": planned,
}
json.dump(out, open("data.json", "w"))
print(f"data.json: {len(legs)} legs, {len(planned)} planned")
