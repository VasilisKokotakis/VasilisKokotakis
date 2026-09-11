"""Generate the custom profile assets.

- assets/header.svg : animated banner with a rotating 3D point-cloud terrain
- assets/mineral.stl: low-poly rock with crystals, embedded in the README as an
                      interactive STL viewer (between the STL markers)

Run: python3 scripts/generate_assets.py
"""

import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

CYAN = (0x28, 0xE6, 0xF4)
BLUE = (0x43, 0x63, 0xFF)
VIOLET = (0x8A, 0x5C, 0xFF)
ICE = (0xD8, 0xFD, 0xFF)


# --------------------------------------------------------------------------- #
# Header: rotating point cloud
# --------------------------------------------------------------------------- #

W, H = 1000, 320
CX, CY = 770, 205          # centre of the cloud's base ring
R = 175                    # base radius in px
TILT = 0.36                # ellipse ratio -> camera pitch
HEIGHT_PX = 95             # vertical scale of the terrain
PERIOD = 26                # seconds per full turn
SAMPLES = 16               # key frames per turn


def lerp_color(stops, t):
    t = min(max(t, 0.0), 1.0)
    seg = t * (len(stops) - 1)
    i = min(int(seg), len(stops) - 2)
    f = seg - i
    a, b = stops[i], stops[i + 1]
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


def terrain(u, v):
    """Height in [0, 1] for a point on the unit disc: hills, a stockpile, a trench."""
    h = 0.38
    h += 0.16 * math.sin(2.1 * u + 0.5) * math.cos(1.7 * v)
    h += 0.10 * math.sin(3.3 * v + 1.2 * u)
    h += 0.30 * math.exp(-((u + 0.45) ** 2 + (v + 0.35) ** 2) / 0.07)   # stockpile
    beta = math.radians(28)
    d = -u * math.sin(beta) + v * math.cos(beta) - 0.18
    h -= 0.42 * math.exp(-(d / 0.11) ** 2)                               # trench
    return min(max(h, 0.0), 1.0)


def arc_keypoints():
    """Path fractions that make motion along the ellipse uniform in *angle*."""
    steps = 2000
    lengths = [0.0]
    for i in range(1, steps + 1):
        a = 2 * math.pi * (i - 0.5) / steps
        lengths.append(lengths[-1] + math.hypot(math.sin(a), TILT * math.cos(a)))
    total = lengths[-1]
    return [lengths[round(k * steps / SAMPLES)] / total for k in range(SAMPLES + 1)]


def header_svg():
    rng = random.Random(7)
    key_times = ";".join(f"{k / SAMPLES:.3g}" for k in range(SAMPLES + 1))
    key_points = ";".join(f"{p:.3f}" for p in arc_keypoints())
    # front of the ring (sin a = 1) is brighter than the back
    opacity = ";".join(
        f"{0.28 + 0.72 * (math.sin(2 * math.pi * k / 8) + 1) / 2:.2f}"
        for k in range(9)
    )

    points = []
    step = 0.085
    n = int(1 / step) + 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            u = i * step + rng.uniform(-0.025, 0.025)
            v = j * step + rng.uniform(-0.025, 0.025)
            rho = math.hypot(u, v)
            if rho > 1 or rho < 0.03:
                continue
            h = terrain(u, v)
            points.append((rho, math.atan2(v, u), h))

    circles = []
    for rho, phi, h in points:
        rx, ry = rho * R, rho * R * TILT
        yc = CY - h * HEIGHT_PX
        path = (
            f"M{CX + rx:.1f},{yc:.1f}"
            f"A{rx:.1f},{ry:.1f} 0 1 1 {CX - rx:.1f},{yc:.1f}"
            f"A{rx:.1f},{ry:.1f} 0 1 1 {CX + rx:.1f},{yc:.1f}"
        )
        begin = -((phi % (2 * math.pi)) / (2 * math.pi)) * PERIOD
        color = lerp_color([VIOLET, BLUE, CYAN, ICE], h * 1.15)
        size = 1.5 + 0.9 * h
        circles.append(
            f'<circle r="{size:.1f}" fill="{color}">'
            f'<animateMotion dur="{PERIOD}s" begin="{begin:.2f}s" repeatCount="indefinite" '
            f'path="{path}" calcMode="linear" keyTimes="{key_times}" keyPoints="{key_points}"/>'
            f'<animate attributeName="opacity" dur="{PERIOD}s" begin="{begin:.2f}s" '
            f'repeatCount="indefinite" values="{opacity}"/>'
            f"</circle>"
        )

    chips = ["backend", "REST APIs", "point clouds", "three.js", "automation"]
    chip_svg, x = [], 58
    for label in chips:
        w = 16 + 7.6 * len(label)
        chip_svg.append(
            f'<g transform="translate({x:.0f},246)"><g class="fade d5">'
            f'<rect width="{w:.0f}" height="26" rx="13" fill="#28e6f4" fill-opacity=".07" '
            f'stroke="#28e6f4" stroke-opacity=".35"/>'
            f'<text x="{w / 2:.0f}" y="17.5" text-anchor="middle" class="mono chip">{label}</text></g></g>'
        )
        x += w + 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Vasilis Kokotakis - Software Engineer">
<title>Vasilis Kokotakis - Software Engineer. From rocks to repos.</title>
<defs>
  <linearGradient id="brand" x1="0" x2="1"><stop offset="0" stop-color="#28e6f4"/><stop offset="1" stop-color="#4363ff"/></linearGradient>
  <radialGradient id="glowR" cx=".77" cy=".62" r=".45"><stop offset="0" stop-color="#1f6fff" stop-opacity=".28"/><stop offset="1" stop-color="#1f6fff" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowL" cx=".08" cy=".05" r=".5"><stop offset="0" stop-color="#28e6f4" stop-opacity=".16"/><stop offset="1" stop-color="#28e6f4" stop-opacity="0"/></radialGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#30363d" fill-opacity=".55"/></pattern>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  <style>
    .sans {{ font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
    .chip {{ font-size: 12.5px; fill: #9ff3fa; }}
    .fade {{ opacity: 0; animation: up .8s cubic-bezier(.2,.7,.2,1) forwards; }}
    .d1 {{ animation-delay: .15s }} .d2 {{ animation-delay: .45s }} .d3 {{ animation-delay: .75s }}
    .d4 {{ animation-delay: 1.05s }} .d5 {{ animation-delay: 1.35s }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(10px) }} to {{ opacity: 1; transform: none }} }}
    .cursor {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0 }} }}
    .ring {{ animation: spin {PERIOD}s linear infinite; }}
    @keyframes spin {{ to {{ stroke-dashoffset: -600 }} }}
  </style>
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="#0d1117"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <rect width="{W}" height="{H}" fill="url(#glowR)"/>
  <rect width="{W}" height="{H}" fill="url(#glowL)"/>

  <!-- left: text -->
  <g class="fade d1"><text x="58" y="78" class="mono" font-size="15" fill="#7d8590"><tspan fill="#28e6f4">~/vasilis</tspan> $ whoami<tspan class="cursor" fill="#28e6f4"> ▍</tspan></text></g>
  <g class="fade d2"><text x="56" y="136" class="sans" font-size="48" font-weight="800" fill="#f0f6fc" letter-spacing="-1">Vasilis Kokotakis</text></g>
  <g class="fade d3"><text x="58" y="176" class="sans" font-size="21" font-weight="600" fill="url(#brand)">Software Engineer · Python · FastAPI · 3D</text></g>
  <g class="fade d4"><text x="58" y="214" class="mono" font-size="15" fill="#7d8590">// from rocks to repos &lt;/&gt;</text></g>
  {"".join(chip_svg)}

  <!-- right: rotating point cloud -->
  <ellipse cx="{CX}" cy="{CY}" rx="{R + 22}" ry="{(R + 22) * TILT:.1f}" fill="none" stroke="#4363ff" stroke-opacity=".35" stroke-dasharray="3 9" class="ring"/>
  <ellipse cx="{CX}" cy="{CY}" rx="{R}" ry="{R * TILT:.1f}" fill="#4363ff" fill-opacity=".05" stroke="#28e6f4" stroke-opacity=".18"/>
  <ellipse cx="{CX}" cy="{CY}" rx="{R + 4}" ry="{(R + 4) * TILT:.1f}" fill="none" stroke="#28e6f4" stroke-width="1.5" opacity="0">
    <animate attributeName="cy" values="{CY};{CY - HEIGHT_PX - 10};{CY}" dur="6s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0;.55;0" dur="6s" repeatCount="indefinite"/>
  </ellipse>
  <g>{"".join(circles)}</g>

  <!-- HUD -->
  <g class="mono" font-size="11.5" fill="#7d8590">
    <text x="{W - 28}" y="{H - 20}" text-anchor="end"><tspan fill="#28e6f4" class="cursor">● </tspan>trench_survey.laz · {len(points)} pts</text>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="#30363d"/>
</g>
</svg>
"""


# --------------------------------------------------------------------------- #
# STL: low-poly rock with crystals
# --------------------------------------------------------------------------- #

def icosphere(subdivisions):
    t = (1 + 5 ** 0.5) / 2
    verts = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t),
             (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    verts = [normalize(v) for v in verts]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
             (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8),
             (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(subdivisions):
        cache, new_faces = {}, []

        def mid(a, b):
            key = tuple(sorted((a, b)))
            if key not in cache:
                verts.append(normalize(tuple((verts[a][k] + verts[b][k]) / 2 for k in range(3))))
                cache[key] = len(verts) - 1
            return cache[key]

        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new_faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = new_faces
    return verts, faces


def normalize(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def sub(a, b):
    return tuple(a[k] - b[k] for k in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def crystal(base, axis, radius, length, rotation):
    """Hexagonal prism with a pointed tip, as a list of triangles."""
    axis = normalize(axis)
    helper = (0, 0, 1) if abs(axis[2]) < 0.9 else (1, 0, 0)
    e1 = normalize(cross(axis, helper))
    e2 = cross(axis, e1)
    ring = lambda offset: [
        tuple(base[k] + axis[k] * offset
              + radius * (math.cos(a) * e1[k] + math.sin(a) * e2[k]) for k in range(3))
        for a in (rotation + i * math.pi / 3 for i in range(6))
    ]
    bottom, top = ring(0), ring(length)
    tip = tuple(base[k] + axis[k] * (length + radius * 1.6) for k in range(3))
    tris = []
    for i in range(6):
        j = (i + 1) % 6
        tris += [(bottom[i], bottom[j], top[j]), (bottom[i], top[j], top[i]), (top[i], top[j], tip)]
    return tris


def mineral_stl():
    rng = random.Random(3)
    verts, faces = icosphere(1)
    rock = []
    for v in verts:
        s = 1 + rng.uniform(-0.13, 0.13)
        rock.append((v[0] * 1.35 * s, v[1] * 1.1 * s, v[2] * 0.72 * s))
    tris = [(rock[a], rock[b], rock[c]) for a, b, c in faces]
    tris += crystal((0.1, 0.0, 0.2), (0.15, 0.1, 1), 0.28, 1.25, 0.2)
    tris += crystal((-0.45, 0.25, 0.15), (-0.55, 0.3, 1), 0.2, 0.85, 0.7)
    tris += crystal((0.55, -0.2, 0.1), (0.6, -0.35, 1), 0.17, 0.7, 1.1)
    tris += crystal((0.0, -0.45, 0.1), (0.05, -0.6, 1), 0.13, 0.5, 0.4)

    fmt = lambda p, scale=10: " ".join(f"{c * scale:.2f}" for c in p)
    lines = ["solid mineral"]
    for a, b, c in tris:
        n = normalize(cross(sub(b, a), sub(c, a)))
        lines += [f"facet normal {fmt(n, 1)}", "outer loop",
                  f"vertex {fmt(a)}", f"vertex {fmt(b)}", f"vertex {fmt(c)}",
                  "endloop", "endfacet"]
    lines.append("endsolid mineral")
    return "\n".join(lines) + "\n"


def main():
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "header.svg").write_text(header_svg())
    stl = mineral_stl()
    (ASSETS / "mineral.stl").write_text(stl)

    readme = ROOT / "README.md"
    text = readme.read_text()
    block = f"<!-- STL:START -->\n```stl\n{stl}```\n<!-- STL:END -->"
    text = re.sub(r"<!-- STL:START -->.*?<!-- STL:END -->", lambda _: block, text, flags=re.S)
    readme.write_text(text)
    print("wrote assets/header.svg, assets/mineral.stl and refreshed README STL block")


if __name__ == "__main__":
    main()
