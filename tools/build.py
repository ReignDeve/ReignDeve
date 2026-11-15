"""
Generates the profile graphics in assets/ in the AEVAR look:
near-black, hairlines, wide-tracked uppercase, Geist / Geist Mono, ice blue only as accent.

All text is converted to outlines, so the SVGs look identical everywhere
(GitHub serves README images without access to web fonts).

    python -m pip install fonttools brotli
    python tools/build.py
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "assets"

# ───────────────────────── tokens ─────────────────────────
BG = "#000"
PANEL = "#060606"
FG = "#f2f2ef"
FG2 = "#a3a6a6"
FG3 = "#686c6c"
FG4 = "#3e4141"
ICE = "#a9cfe0"
LINE = 'stroke="#fff" stroke-opacity="0.075"'
LINE2 = 'stroke="#fff" stroke-opacity="0.14"'
EASE = "cubic-bezier(0.2, 0.7, 0.1, 1)"

# ───────────────────────── text → outlines ─────────────────────────
FONT_FILES = {"sans": "geist-latin-wght-normal.woff2", "mono": "geist-mono-latin-wght-normal.woff2"}


@lru_cache(maxsize=None)
def font(kind: str, weight: int) -> TTFont:
    f = TTFont(FONTS / FONT_FILES[kind])
    return instancer.instantiateVariableFont(f, {"wght": weight})


def fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def text(
    s: str,
    x: float,
    y: float,
    size: float,
    *,
    kind: str = "sans",
    weight: int = 400,
    track: float = 0.0,
    fill: str = FG,
    anchor: str = "start",
    cls: str = "",
    style: str = "",
) -> str:
    """Render a single line as an outlined <path>. `track` is letter-spacing in em."""
    d, width = text_d(s, size, kind, weight, track)
    if anchor == "end":
        x -= width
    elif anchor == "middle":
        x -= width / 2
    attrs = f' class="{cls}"' if cls else ""
    attrs += f' style="{style}"' if style else ""
    return f'<path{attrs} transform="translate({fmt(x)} {fmt(y)})" fill="{fill}" d="{d}"/>'


def text_width(s: str, size: float, kind: str = "sans", weight: int = 400, track: float = 0.0) -> float:
    return text_d(s, size, kind, weight, track)[1]


@lru_cache(maxsize=None)
def text_d(s: str, size: float, kind: str, weight: int, track: float) -> tuple[str, float]:
    f = font(kind, weight)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    scale = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs, ntos=fmt)
    cx = 0.0
    for i, ch in enumerate(s):
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, 0)))
        cx += hmtx[g][0] * scale
        if i < len(s) - 1:
            cx += track * size
    return pen.getCommands(), cx


# ───────────────────────── helpers ─────────────────────────
def svg(w: int, h: int, body: str, css: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
        f"<title>{title}</title><style>{css}{BASE_CSS}</style>{body}</svg>\n"
    )


BASE_CSS = f"""
.fade{{animation:fade 1.4s {EASE} both}}
.rise{{animation:rise 1.4s {EASE} both}}
.draw{{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 2.4s {EASE} forwards}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2.8s 1s ease-out infinite;opacity:0}}
@keyframes fade{{from{{opacity:0}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes pulse{{0%{{opacity:.8;transform:scale(1)}}70%,100%{{opacity:0;transform:scale(3.4)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation-duration:.01ms!important;animation-delay:0s!important;animation-iteration-count:1!important}}.pulse{{display:none}}}}
"""


def delay(s: float) -> str:
    return f"animation-delay:{s}s"


def frame(w: int, h: int) -> str:
    return f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="none" {LINE}/>'


def dot(x: float, y: float, r: float = 3, pulse: bool = True) -> str:
    ring = (
        f'<circle class="pulse" cx="{fmt(x)}" cy="{fmt(y)}" r="{r}" fill="none" stroke="{ICE}" stroke-width="1"/>'
        if pulse
        else ""
    )
    return f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{r}" fill="{ICE}"/>{ring}'


def mono(s, x, y, size=14, fill=FG3, anchor="start", cls="", style="", weight=400, track=0.2):
    return text(s, x, y, size, kind="mono", weight=weight, track=track, fill=fill, anchor=anchor, cls=cls, style=style)


def label(s, x, y, size=13, fill=FG3, anchor="start", cls="", style="", weight=500, track=0.32):
    return text(s, x, y, size, kind="sans", weight=weight, track=track, fill=fill, anchor=anchor, cls=cls, style=style)


# ───────────────────────── landscape (same seeds as aevar-website HeroScene) ─────────────────────────
def mulberry(seed: int):
    a = seed & 0xFFFFFFFF

    def imul(x, y):
        return (x * y) & 0xFFFFFFFF

    def r():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return r


def ridge_ys(seed, base, amp, rough, bias, vw=1600, n=256):
    r = mulberry(seed)
    ys = [0.0] * (n + 1)
    ys[0] = (r() - 0.5) * amp
    ys[n] = (r() - 0.5) * amp
    step, sc = n, amp
    while step > 1:
        half = step // 2
        for i in range(half, n, step):
            ys[i] = (ys[i - half] + ys[i + half]) / 2 + (r() - 0.5) * sc
        step = half
        sc *= rough
    return [(i / n * vw, base + y * bias(i / n)) for i, y in enumerate(ys)]


def closed(pts, vw=1600, vh=900):
    return f"M0,{vh} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f" L{vw},{vh} Z"


def hero() -> str:
    W, H = 1280, 560
    far = closed(ridge_ys(11, 585, 150, 0.63, lambda t: 0.5 + t * 0.4))
    mid = closed(ridge_ys(27, 615, 300, 0.62, lambda t: 1.25 - t * 0.85))
    near = closed(ridge_ys(5, 660, 420, 0.6, lambda t: 1.2 - t * 0.6 if t < 0.5 else 0.25 + (1 - t) * 0.3))
    right = closed(ridge_ys(41, 720, 420, 0.6, lambda t: (t - 0.82) * 5 if t > 0.82 else 0.08))

    scene = f"""
<svg x="0" y="0" width="{W}" height="{H}" viewBox="0 0 1600 900" preserveAspectRatio="xMaxYMid slice">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#141516"/><stop offset=".45" stop-color="#3c3e41"/><stop offset=".66" stop-color="#7d7b78"/><stop offset=".75" stop-color="#9a928a"/></linearGradient>
<radialGradient id="sun" cx=".98" cy=".66" r=".45"><stop offset="0" stop-color="#f3dcc2" stop-opacity=".85"/><stop offset=".35" stop-color="#c9b6a3" stop-opacity=".35"/><stop offset="1" stop-color="#c9b6a3" stop-opacity="0"/></radialGradient>
<linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6f6f70"/><stop offset=".3" stop-color="#3a3b3d"/></linearGradient>
<linearGradient id="midfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2b2d2f"/><stop offset=".4" stop-color="#161718"/></linearGradient>
<linearGradient id="ceiling" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#030303"/><stop offset=".7" stop-color="#0b0b0b"/><stop offset="1" stop-color="#1a1816"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".6" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity=".45"/></linearGradient>
<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".1" stop-color="#fff" stop-opacity=".42"/><stop offset=".7" stop-color="#fff" stop-opacity=".5"/><stop offset=".9" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity=".05"/></linearGradient>
<filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>
</defs>
<g class="scene">
<rect width="1600" height="900" fill="url(#sky)"/>
<rect width="1600" height="900" fill="url(#sun)"/>
<path class="trail" pathLength="1" d="M-40,300 C300,360 640,650 1000,560 Q1360,470 1580,300" stroke="url(#trail)" stroke-width="1.4" fill="none"/>
<path d="{far}" fill="url(#haze)" opacity=".85"/>
<g class="fog"><ellipse cx="900" cy="600" rx="520" ry="26" fill="#b9b4ae" opacity=".14" filter="url(#blur)"/></g>
<path d="{mid}" fill="url(#midfill)"/>
<g class="fog fog2"><ellipse cx="700" cy="700" rx="640" ry="30" fill="#b9b4ae" opacity=".09" filter="url(#blur)"/></g>
<path d="{right}" fill="#121314"/>
<path d="{near}" fill="#0b0c0c"/>
<path d="M0,780 L1600,760 L1600,900 L0,900 Z" fill="#0a0a0a"/>
<path d="M1540,742 C1460,750 1420,758 1380,752 S1300,762 1240,770" stroke="#d8cfc4" stroke-opacity=".35" stroke-width="1.4" fill="none"/>
<path d="M0,0 H1600 V8 L470,118 L0,146 Z" fill="url(#ceiling)"/>
<path d="M470,118 L1600,8" stroke="url(#edge)" stroke-width="1.5"/>
<path d="M0,830 L1600,790 V900 H0 Z" fill="#040404"/>
<path d="M0,830 L1600,790" stroke="#fff" stroke-opacity=".07"/>
</g>
</svg>"""

    shade = f"""
<defs>
<linearGradient id="shadeL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset=".2" stop-color="#000" stop-opacity=".9"/><stop offset=".46" stop-color="#000" stop-opacity=".5"/><stop offset=".74" stop-color="#000" stop-opacity="0"/></linearGradient>
<linearGradient id="shadeB" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#000"/><stop offset=".24" stop-color="#000" stop-opacity="0"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#shadeL)"/><rect width="{W}" height="{H}" fill="url(#shadeB)"/>"""

    x0 = 72
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>', scene, shade]
    # ghost glyph, like the hero on aevar-website (minus the crossbar)
    body.append(
        f'<g class="fade" style="{delay(0.2)}"><path d="M150 520 L300 70 H372 L522 520 M222 520 L336 178 L450 520" '
        f'fill="none" stroke="#fff" stroke-opacity=".05"/></g>'
    )
    body.append(mono("REIGNDEVE / 001", x0, 64, 13, fill=FG3, cls="fade", style=delay(0.3)))
    body.append(mono("49.45° N / 11.08° E", W - 40, 64, 13, fill=FG3, anchor="end", cls="fade", style=delay(0.3)))
    body.append(label("FULL-STACK DEVELOPER  /  M.SC. INFORMATICS · FAU", x0, 168, 13, fill=FG3, cls="fade", style=delay(0.5)))
    body.append(text("MARIUS", x0, 262, 66, weight=400, track=0.16, cls="rise", style=delay(0.7)))
    body.append(text("BUNGERT", x0, 344, 66, weight=400, track=0.16, cls="rise", style=delay(0.85)))
    body.append(f'<rect class="grow" x="{x0}" y="384" width="40" height="1" fill="{FG2}" style="{delay(1.2)}"/>')
    body.append(f'<g class="fade" style="{delay(1.4)}">{dot(x0 + 3, 427)}'
                f'{mono("FOCUS  —  FULL-STACK · LOCAL AI", x0 + 20, 432, 13, fill=FG2)}</g>')
    body.append(label("NUREMBERG AREA  /  GERMANY", x0, H - 34, 11, fill=FG3, cls="fade", style=delay(1.6)))
    body.append(label("BUILDING WHAT COMES NEXT", W - 40, H - 34, 11, fill=FG3, anchor="end", cls="fade", style=delay(1.6)))
    body.append(frame(W, H))

    css = f"""
.scene{{transform-origin:72% 62%;animation:settle 2s {EASE} both,breathe 60s 2s ease-in-out infinite alternate}}
.fog{{animation:drift 28s ease-in-out infinite alternate}}
.fog2{{animation-duration:40s;animation-direction:alternate-reverse}}
.trail{{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 6.5s .3s cubic-bezier(.3,.35,.35,1) forwards}}
.grow{{transform-box:fill-box;transform-origin:left;animation:growx 1.2s {EASE} both}}
@keyframes settle{{from{{opacity:0;transform:scale(1.06)}}}}
@keyframes breathe{{to{{transform:scale(1.05) translateX(-1.2%)}}}}
@keyframes drift{{to{{transform:translateX(-180px)}}}}
@keyframes growx{{from{{transform:scaleX(0)}}}}
"""
    return svg(W, H, "".join(body), css, "Marius Bungert — full-stack developer, M.Sc. Informatics at FAU")


# ───────────────────────── stack: a summit panorama ─────────────────────────
STACK = [
    # name, primary, label row (0 = high, 1 = low)
    ("REACT", False, 1),
    ("NEXT.JS", False, 0),
    ("ANGULAR", True, 1),
    ("TYPESCRIPT", True, 0),
    ("KOTLIN", True, 1),
    ("SPRING BOOT", True, 0),
    (".NET", False, 1),
    ("AZURE", False, 0),
]


def displace(p0, p1, rough, seed, depth=5):
    """Midpoint displacement between two points -> natural, jagged ridge segment (without p0)."""
    r = mulberry(seed)
    pts = [p0, p1]
    amp = math.dist(p0, p1) * rough
    for _ in range(depth):
        nxt = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            nxt.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + (r() - 0.5) * amp))
            nxt.append(b)
        pts = nxt
        amp *= 0.6
    return pts[1:]


def stack() -> str:
    W, H = 1280, 430
    base_y = 400
    left, rightx = 70, W - 70
    n = len(STACK)
    xs = [left + 40 + i * (rightx - left - 80) / (n - 1) for i in range(n)]
    peak_h = [150, 132, 196, 222, 206, 186, 118, 104]
    peaks = [(x, base_y - h) for x, h in zip(xs, peak_h)]

    # key points: edge, saddle, peak, saddle, peak, ... edge; then roughen every segment
    r = mulberry(7)
    keys = [(0, base_y - 70)]
    for i, (px, py) in enumerate(peaks):
        prev = keys[-1]
        if i:
            keys.append(((prev[0] + px) / 2 + (r() - 0.5) * 30, max(prev[1], py) + 52 + r() * 40))
        keys.append((px, py))
    keys.append((W, base_y - 64))
    pts = [keys[0]]
    for j, (a, b) in enumerate(zip(keys, keys[1:])):
        seg = displace(a, b, 0.3, 100 + j, 6)
        seg[-1] = b  # keep the summit exact
        pts.extend(seg)
    line_d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    fill_d = line_d + f" L{W},{H} L0,{H} Z"

    # a hazy range further back for depth
    back = [(0.0, base_y - 120)]
    back.extend(displace((0.0, base_y - 120), (W / 2, base_y - 170), 0.18, 900, 6))
    back.extend(displace((W / 2, base_y - 170), (float(W), base_y - 110), 0.18, 901, 6))
    back_d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in back) + f" L{W},{H} L0,{H} Z"

    body = [f'<rect width="{W}" height="{H}" fill="{PANEL}"/>']
    body.append(
        '<defs><linearGradient id="mass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#17181a"/>'
        '<stop offset=".55" stop-color="#070707"/></linearGradient>'
        '<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity=".035"/></linearGradient></defs>'
    )
    body.append(f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')
    body.append(mono("02 / STACK", 40, 52, 13, fill=FG3, cls="fade"))
    # legend
    lx = W - 40
    body.append(label("ALSO", lx, 52, 11, fill=FG3, anchor="end", cls="fade"))
    lx -= text_width("ALSO", 11, "sans", 500, 0.32) + 14
    body.append(f'<circle class="fade" cx="{lx}" cy="48" r="3.2" fill="none" stroke="{FG3}"/>')
    lx -= 30
    body.append(label("PRIMARY", lx, 52, 11, fill=FG2, anchor="end", cls="fade"))
    lx -= text_width("PRIMARY", 11, "sans", 500, 0.32) + 14
    body.append(f'<circle class="fade" cx="{lx}" cy="48" r="3.2" fill="{FG}"/>')
    body.append(f'<path d="M40 76 H{W - 40}" {LINE}/>')

    body.append(f'<path class="fade" style="{delay(0.2)}" d="{back_d}" fill="#101113" opacity=".9"/>')
    body.append(f'<path class="fade" style="{delay(0.4)}" d="{fill_d}" fill="url(#mass)"/>')
    body.append(f'<path class="draw" pathLength="1" d="{line_d}" fill="none" stroke="#fff" stroke-opacity=".38" stroke-width="1.1"/>')

    label_y = {0: 116, 1: 146}
    for i, ((name, primary, row), (px, py)) in enumerate(zip(STACK, peaks)):
        d0 = 1.4 + i * 0.12
        ty = label_y[row]
        col = FG if primary else FG3
        lead = f'<path class="lead" style="{delay(d0)}" d="M{px:.1f} {py - 8:.1f} V{ty + 12}" stroke="#fff" stroke-opacity="{".22" if primary else ".12"}" stroke-dasharray="2 4"/>'
        mark = (
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{FG}"/>'
            if primary
            else f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{PANEL}" stroke="{FG3}"/>'
        )
        body.append(lead)
        body.append(f'<g class="fade" style="{delay(d0)}">{mark}</g>')
        body.append(
            label(name, px, ty, 15 if primary else 13, fill=col, anchor="middle", weight=500 if primary else 400,
                  track=0.22, cls="rise", style=delay(d0 + 0.1))
        )
    body.append(f'<path d="M0 {H - 1} H{W}" {LINE}/>')
    body.append(frame(W, H))
    css = f"""
.lead{{transform-box:fill-box;transform-origin:bottom;animation:growy 1s {EASE} both}}
@keyframes growy{{from{{transform:scaleY(0)}}}}
"""
    return svg(W, H, "".join(body), css, "Stack: Angular, TypeScript, Kotlin, Spring Boot. Also React, Next.js, .NET, Azure.")


# ───────────────────────── projects ─────────────────────────
def projects_header() -> str:
    W, H = 1280, 96
    body = [
        mono("03 / PROJECTS", 40, 58, 13, fill=FG3, cls="fade"),
        f'<path class="grow" d="M{40 + text_width("03 / PROJECTS", 13, "mono", 400, 0.2) + 28} 53.5 H{W - 40}" {LINE2}/>',
    ]
    css = f".grow{{transform-box:fill-box;transform-origin:left;animation:growx 2s {EASE} both}}@keyframes growx{{from{{transform:scaleX(0)}}}}"
    return svg(W, H, "".join(body), css, "Projects")


def glyph_stage(cx, cy):
    # spotlight cone onto a stage floor
    return f"""
<g fill="none" stroke="#fff">
<path class="draw" pathLength="1" d="M{cx} {cy - 74} L{cx - 64} {cy + 46} M{cx} {cy - 74} L{cx + 64} {cy + 46}" stroke-opacity=".35" style="{delay(0.4)}"/>
<ellipse class="draw" pathLength="1" cx="{cx}" cy="{cy + 46}" rx="64" ry="12" stroke-opacity=".5" style="{delay(1)}"/>
<path class="sway" d="M{cx} {cy - 74} L{cx - 30} {cy + 46} L{cx + 30} {cy + 46} Z" fill="#fff" fill-opacity=".05" stroke="none"/>
<circle cx="{cx}" cy="{cy - 74}" r="3" fill="{FG}" stroke="none"/>
</g>"""


def glyph_route(cx, cy):
    d = f"M{cx - 80} {cy + 40} C{cx - 40} {cy + 40} {cx - 50} {cy - 10} {cx - 10} {cy - 10} S{cx + 30} {cy - 60} {cx + 80} {cy - 50}"
    nodes = [(cx - 80, cy + 40), (cx - 10, cy - 10), (cx + 80, cy - 50)]
    out = f'<path class="draw" pathLength="1" d="{d}" fill="none" stroke="#fff" stroke-opacity=".4" stroke-dasharray="1" style="{delay(0.4)}"/>'
    out += f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity=".08" stroke-dasharray="2 5"/>'
    for i, (x, y) in enumerate(nodes):
        out += f'<circle class="fade" cx="{x}" cy="{y}" r="4.5" fill="{PANEL}" stroke="#fff" stroke-opacity=".5" style="{delay(0.6 + i * 0.5)}"/>'
    out += (
        f'<circle r="3" fill="{ICE}"><animateMotion dur="5s" begin="2.6s" repeatCount="indefinite" '
        f'keyPoints="0;1;1" keyTimes="0;.75;1" calcMode="spline" keySplines=".45 0 .35 1;0 0 1 1" path="{d}"/></circle>'
    )
    return out


def glyph_rings(cx, cy):
    out = ""
    rings = [(70, [(0.0, 0.42), (0.46, 0.7), (0.74, 0.93)]), (52, [(0.05, 0.3), (0.34, 0.8)]), (34, [(0.1, 0.62)])]
    k = 0
    for r, segs in rings:
        out += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".06"/>'
        for a0, a1 in segs:
            t0, t1 = a0 * 2 * math.pi - math.pi / 2, a1 * 2 * math.pi - math.pi / 2
            x0, y0 = cx + r * math.cos(t0), cy + r * math.sin(t0)
            x1, y1 = cx + r * math.cos(t1), cy + r * math.sin(t1)
            large = 1 if (a1 - a0) > 0.5 else 0
            op = ".55" if k == 0 else ".3"
            out += (
                f'<path class="draw" pathLength="1" d="M{x0:.1f} {y0:.1f} A{r} {r} 0 {large} 1 {x1:.1f} {y1:.1f}" '
                f'fill="none" stroke="#fff" stroke-opacity="{op}" stroke-width="2" style="{delay(0.4 + k * 0.25)}"/>'
            )
            k += 1
    out += f'<circle cx="{cx}" cy="{cy}" r="2.5" fill="{FG}"/>'
    return out


def glyph_wave(cx, cy):
    hs = [10, 22, 40, 64, 46, 80, 58, 34, 52, 26, 14, 8]
    w = 9
    x0 = cx - (len(hs) - 1) * w * 1.6 / 2
    out = ""
    for i, h in enumerate(hs):
        x = x0 + i * w * 1.6
        out += (
            f'<rect class="bar" x="{x - 1:.1f}" y="{cy - h / 2:.1f}" width="2" height="{h}" fill="#fff" '
            f'fill-opacity="{".55" if 3 <= i <= 8 else ".28"}" style="animation-delay:{i * 0.13:.2f}s"/>'
        )
    return out


CARDS = [
    ("01", "WEB APP", "ENSEMBLEOS", "Props inventory for a local", "musical theatre club.", "IN USE", glyph_stage),
    ("02", "RESEARCH · AI", "CODEPILOT", "Feedback for beginners stuck", "on C# programming exercises.", "RESEARCH", glyph_route),
    ("03", "WINDOWS · RUST", "CLARITY", "See what's filling your", "drive on Windows.", "PRIVATE BETA", glyph_rings),
    ("04", "LOCAL AI", "LUCY", "A room assistant with", "persistent local memory.", "EXPLORING", glyph_wave),
]


def card(idx, kind, name, l1, l2, status, glyph) -> str:
    W, H = 640, 380
    body = [f'<rect width="{W}" height="{H}" fill="{PANEL}"/>']
    body.append(
        '<defs><radialGradient id="g" cx=".82" cy=".3" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".045"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#g)"/>'
    )
    body.append(mono(idx, 36, 52, 13, fill=FG2, cls="fade"))
    body.append(mono(f"/ {kind}", 70, 52, 13, fill=FG3, cls="fade"))
    # status pill
    sw = text_width(status, 10, "sans", 500, 0.26)
    px1 = W - 36
    px0 = px1 - sw - 46
    body.append(
        f'<g class="fade" style="{delay(0.3)}"><rect x="{px0:.1f}" y="31.5" width="{px1 - px0:.1f}" height="28" rx="14" fill="none" {LINE2}/>'
        f'{dot(px0 + 17, 45.5, 2.6)}{label(status, px1 - 15, 49.5, 10, fill=FG2, anchor="end", track=0.26)}</g>'
    )
    body.append(f'<g>{glyph(470, 168)}</g>')
    body.append(text(name, 36, 284, 34, weight=400, track=0.14, cls="rise", style=delay(0.5)))
    body.append(f'<rect class="grow" x="36" y="306" width="32" height="1" fill="{FG3}" style="{delay(0.8)}"/>')
    body.append(text(l1, 36, 334, 15, fill=FG2, track=0.03, cls="fade", style=delay(0.9)))
    body.append(text(l2, 36, 356, 15, fill=FG2, track=0.03, cls="fade", style=delay(0.95)))
    body.append(frame(W, H))
    css = f"""
.grow{{transform-box:fill-box;transform-origin:left;animation:growx 1.2s {EASE} both}}
.sway{{transform-box:view-box;transform-origin:470px 94px;animation:sway 7s ease-in-out infinite alternate}}
.bar{{transform-box:fill-box;transform-origin:center;animation:bar 1.6s ease-in-out infinite alternate}}
@keyframes growx{{from{{transform:scaleX(0)}}}}
@keyframes sway{{from{{transform:rotate(-9deg)}}to{{transform:rotate(9deg)}}}}
@keyframes bar{{from{{transform:scaleY(.35)}}}}
"""
    return svg(W, H, "".join(body), css, f"{name.title()} — {l1} {l2}")


# ───────────────────────── off the grid ─────────────────────────
def glyph_ski(cx, cy):
    x0, x1 = cx - 112, cx + 112

    def slope(x):
        return cy - 52 + (x - x0) * 108 / (x1 - x0)

    pts = []
    for i in range(61):
        x = cx - 92 + i * 184 / 60
        pts.append((x, slope(x) - 4 + 11 * math.sin((x - cx + 92) / 15)))
    trail = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (
        f'<path d="M{x0} {slope(x0):.1f} L{x1} {slope(x1):.1f} L{x1} {cy + 70} L{x0} {cy + 70} Z" fill="#fff" fill-opacity=".025"/>'
        f'<path d="M{x0} {slope(x0):.1f} L{x1} {slope(x1):.1f}" stroke="#fff" stroke-opacity=".3"/>'
        f'<path class="carve" pathLength="1" d="{trail}" fill="none" stroke="#fff" stroke-opacity=".6"/>'
        f'<circle r="3.2" fill="{ICE}"><animateMotion dur="4.5s" repeatCount="indefinite" keyPoints="0;1;1" '
        f'keyTimes="0;.7;1" calcMode="linear" path="{trail}"/></circle>'
    )


def glyph_throw(cx, cy):
    a, b = (cx - 46, cy + 44), (cx + 46, cy + 44)
    arc = f"M{a[0]} {a[1]} C{a[0]} {cy - 70} {b[0]} {cy - 70} {b[0]} {b[1]}"
    return (
        f'<path d="M{cx - 100} {cy + 56} H{cx + 100}" stroke="#fff" stroke-opacity=".3"/>'
        f'<path d="{arc}" fill="none" stroke="#fff" stroke-opacity=".16" stroke-dasharray="2 5"/>'
        f'<circle cx="{a[0]}" cy="{a[1]}" r="5" fill="none" stroke="#fff" stroke-opacity=".45"/>'
        f'<circle cx="{b[0]}" cy="{b[1]}" r="5" fill="none" stroke="#fff" stroke-opacity=".45"/>'
        f'<g><animateMotion dur="3.2s" repeatCount="indefinite" keyPoints="0;1;1;0;0" keyTimes="0;.4;.5;.9;1" '
        f'calcMode="spline" keySplines=".45 0 .55 1;0 0 1 1;.45 0 .55 1;0 0 1 1" path="{arc}"/>'
        f'<circle r="3.4" fill="{FG}"/><path d="M-9 0 H9" stroke="#fff" stroke-opacity=".5">'
        f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="1.6s" repeatCount="indefinite"/></path></g>'
    )


def glyph_coffee(cx, cy):
    cup = (
        f"M{cx - 38} {cy - 6} H{cx + 38} V{cy + 24} C{cx + 38} {cy + 46} {cx + 22} {cy + 54} {cx} {cy + 54} "
        f"C{cx - 22} {cy + 54} {cx - 38} {cy + 46} {cx - 38} {cy + 24} Z"
    )
    handle = f"M{cx + 38} {cy + 2} C{cx + 62} {cy + 2} {cx + 62} {cy + 34} {cx + 36} {cy + 34}"
    out = (
        f'<path d="{cup}" fill="#fff" fill-opacity=".03" stroke="#fff" stroke-opacity=".5"/>'
        f'<path d="{handle}" fill="none" stroke="#fff" stroke-opacity=".5"/>'
        f'<path d="M{cx - 64} {cy + 64} H{cx + 64}" stroke="#fff" stroke-opacity=".3"/>'
    )
    for i, dx in enumerate((-16, 0, 16)):
        x = cx + dx
        d = f"M{x} {cy - 18} C{x - 10} {cy - 34} {x + 10} {cy - 46} {x} {cy - 62} S{x - 8} {cy - 82} {x + 2} {cy - 96}"
        out += (
            f'<path class="steam" pathLength="1" d="{d}" fill="none" stroke="#fff" stroke-opacity=".45" '
            f'style="animation-delay:{i * 0.9:.1f}s"/>'
        )
    return out


GRID = [
    ("SKIING", "SINCE AGE 2", glyph_ski),
    ("ACROBATIC ROCK ’N’ ROLL", "COMPETITIVE", glyph_throw),
    ("COFFEE", "ENABLED SINCE THE B.SC. THESIS", glyph_coffee),
]


def offgrid() -> str:
    W, H = 1280, 360
    body = [f'<rect width="{W}" height="{H}" fill="{PANEL}"/>']
    body.append(mono("04 / OFF THE GRID", 40, 52, 13, fill=FG3, cls="fade"))
    body.append(f'<path d="M40 76 H{W - 40}" {LINE}/>')
    col = (W - 80) / 3
    for i, (title, sub, glyph) in enumerate(GRID):
        cx = 40 + col * i + col / 2
        if i:
            body.append(f'<path d="M{40 + col * i:.1f} 104 V{H - 36}" {LINE}/>')
        body.append(f'<g class="fade" style="{delay(0.3 + i * 0.25)}">{glyph(cx, 176)}</g>')
        body.append(label(title, cx, 292, 14, fill=FG, anchor="middle", track=0.24, cls="rise", style=delay(0.5 + i * 0.25)))
        body.append(mono(sub, cx, 318, 11, fill=FG3, anchor="middle", track=0.18, cls="fade", style=delay(0.7 + i * 0.25)))
    body.append(frame(W, H))
    css = """
.carve{stroke-dasharray:1;stroke-dashoffset:1;animation:carve 4.5s linear infinite}
@keyframes carve{0%{stroke-dashoffset:1;opacity:1}70%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
.steam{stroke-dasharray:.35 .65;animation:steam 2.7s linear infinite}
@keyframes steam{0%{stroke-dashoffset:.35;opacity:0}30%{opacity:1}100%{stroke-dashoffset:-.65;opacity:0}}
"""
    return svg(W, H, "".join(body), css, "Off the grid: skiing since age 2, competitive acrobatic rock ’n’ roll, coffee.")


# ───────────────────────── footer: sunset ─────────────────────────
def footer() -> str:
    W, H = 1280, 200
    ridge = [(0.0, 150.0)]
    ridge.extend(displace((0.0, 150.0), (420.0, 118.0), 0.22, 300, 6))
    ridge.extend(displace((420.0, 118.0), (860.0, 146.0), 0.22, 301, 6))
    ridge.extend(displace((860.0, 146.0), (float(W), 128.0), 0.22, 302, 6))
    ridge_d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in ridge)
    sx = 980
    sy = round(min(ridge, key=lambda q: abs(q[0] - sx))[1] + 6)  # sun half-sunk behind the ridge
    body = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    body.append(
        f'<defs><radialGradient id="dusk" cx="{sx / W:.3f}" cy="{(sy + 20) / H:.3f}" r=".55">'
        '<stop offset="0" stop-color="#f3dcc2" stop-opacity=".32"/><stop offset=".4" stop-color="#c9b6a3" stop-opacity=".1"/>'
        '<stop offset="1" stop-color="#c9b6a3" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="trail2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".3" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity=".5"/></linearGradient></defs>'
    )
    body.append(f'<rect width="{W}" height="{H}" fill="url(#dusk)"/>')
    body.append(f'<circle class="sun" cx="{sx}" cy="{sy}" r="21" fill="#e9d6c0" fill-opacity=".6"/>')
    body.append(
        f'<path class="trail" pathLength="1" d="M-20 40 C300 30 700 40 {sx - 30} {sy - 6}" fill="none" '
        f'stroke="url(#trail2)" stroke-width="1.2"/>'
    )
    body.append(f'<path d="{ridge_d} L{W},{H} L0,{H} Z" fill="#070708"/>')
    body.append(f'<path d="{ridge_d}" fill="none" stroke="#fff" stroke-opacity=".22"/>')
    body.append(mono("REIGNDEVE · 2026", 40, H - 30, 12, fill=FG3, cls="fade", style=delay(0.6)))
    body.append(label("END OF TRAIL", W - 40, H - 30, 11, fill=FG3, anchor="end", cls="fade", style=delay(0.6)))
    body.append(frame(W, H))
    css = f"""
.sun{{animation:sunset 9s 0.4s {EASE} both}}
@keyframes sunset{{from{{transform:translateY(-34px)}}}}
.trail{{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 4.5s .2s cubic-bezier(.3,.35,.35,1) forwards}}
"""
    return svg(W, H, "".join(body), css, "End of trail")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    files = {
        "hero.svg": hero(),
        "stack.svg": stack(),
        "projects.svg": projects_header(),
        "offgrid.svg": offgrid(),
        "footer.svg": footer(),
    }
    for i, c in enumerate(CARDS, 1):
        files[f"card-{i}.svg"] = card(*c)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name:14} {len(content.encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
