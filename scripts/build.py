#!/usr/bin/env python3
"""Rebuilds data.json from every GPX in gpx/. Runs in GitHub Actions on each upload."""
import re, math, json, glob, os, datetime

PALETTE = ["#e63946","#2a9d8f","#f4a261","#457b9d","#8338ec","#ff006e",
           "#06d6a0","#ffbe0b","#3a86ff","#fb5607","#118ab2","#9b2226"]

def load(path):
    d = open(path, encoding="utf-8", errors="replace").read()
    pts = [(float(a), float(b)) for a, b in re.findall(r'<trkpt\s+lat="([-\d.]+)"\s+lon="([-\d.]+)"', d)]
    if not pts:
        pts = [(float(a), float(b)) for b, a in re.findall(r'<trkpt\s+lon="([-\d.]+)"\s+lat="([-\d.]+)"', d)]
    m = re.search(r'<trk>.*?<name>(.*?)</name>', d, re.S) or re.search(r'<metadata>.*?<name>(.*?)</name>', d, re.S)
    name = m.group(1).replace("-&gt;", "→").replace("->", "→") if m else os.path.basename(path)
    return name, pts

def dist_mi(pts):
    R, tot = 3958.8, 0.0
    for (a, b), (c, d) in zip(pts, pts[1:]):
        p1, p2 = math.radians(a), math.radians(c)
        h = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
        tot += 2*R*math.asin(math.sqrt(h))
    return tot

def perp(p, a, b):
    k = math.cos(math.radians((a[0]+b[0])/2))
    ax, ay, bx, by, px, py = a[1]*k, a[0], b[1]*k, b[0], p[1]*k, p[0]
    dx, dy = bx-ax, by-ay
    if dx == dy == 0: return math.hypot(px-ax, py-ay)
    t = max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))

def simplify(pts, target=1500):
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

legs = []
files = sorted(glob.glob("gpx/*.gpx"))
for i, f in enumerate(files):
    name, pts = load(f)
    if len(pts) < 2:
        print(f"skip {f}: no track points"); continue
    s = simplify(pts)
    legs.append({
        "name": name,
        "color": PALETTE[i % len(PALETTE)],
        "miles": round(dist_mi(pts), 1),
        "pts": [[round(a, 5), round(b, 5)] for a, b in s],
    })
    print(f"{f}: {len(pts)} pts -> {len(s)}, {legs[-1]['miles']} mi")

out = {
    "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "legs": legs,
}
json.dump(out, open("data.json", "w"))
print(f"data.json written: {len(legs)} legs, {sum(l['miles'] for l in legs):.0f} mi total")
