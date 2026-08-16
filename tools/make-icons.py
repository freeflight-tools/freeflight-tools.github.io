#!/usr/bin/env python3
"""Regenerate the PNG app icons from the same artwork as each icon.svg.

The PNGs are NOT the favicons and cannot simply be a copy of them:

  * manifest.webmanifest declares icon-512.png as `purpose: maskable`, which
    means Android crops it to the launcher's own shape (circle, squircle,
    rounded square) and assumes the outer ~20% is disposable background. So a
    maskable icon has to be a FULL-BLEED SQUARE with a solid plate. No rx, no
    transparency: rounded corners get cropped a second time, and transparency
    crops to nothing.
  * Everything therefore sits inside the safe zone, a circle of 80% diameter,
    which is what SAFE below scales the artwork into.

The artwork is duplicated from each icon.svg rather than read out of it,
because the SVGs are the FAVICONS: rounded, and in Windmap's case with no
plate at all. Change one, change the other, and re-run this.

Rendered through headless Chrome at device scale 1, so the output is exactly
the requested pixel size.

    python3 tools/make-icons.py [path-to-the-directory-holding-all-three-repos]
"""
import subprocess, pathlib, sys, tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = pathlib.Path(tempfile.mkdtemp(prefix="iconbuild-"))
# the three repos sit side by side; override with argv[1] if they move
REPOS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                     else pathlib.Path(__file__).resolve().parents[2])

SAFE = 0.80          # maskable safe-zone diameter, as a fraction of the icon

# artwork in a 0 0 64 64 box, plate separate so it can go full bleed
FAMILY = dict(
    plate="#0B1218",
    art='<circle cx="48" cy="19" r="7" fill="#F0A24A"/>'
        '<path d="M30 50 L44 27 L61 50 Z" fill="#4E82AD"/>'
        '<path d="M2 50 L23 12 L44 50 Z" fill="#EAF1F7"/>',
)

# the handset and wordmark, redrawn in the 64 box the others use
HXCALL = dict(
    plate="#1E6FA8",
    art='<g transform="translate(32 18) rotate(-35) scale(0.082)" fill="#fff">'
        '<rect x="-96" y="-24" width="192" height="48" rx="24"/>'
        '<rect x="-124" y="-24" width="66" height="96" rx="30"/>'
        '<rect x="58" y="-24" width="66" height="96" rx="30"/></g>'
        '<text x="32" y="50" text-anchor="middle" fill="#fff"'
        ' font-family="Helvetica Neue,Helvetica,Arial,sans-serif"'
        ' font-size="28.5" font-weight="700" letter-spacing="0.25">HX</text>',
)

# the map marker itself: WG.BANDS widths, PALETTE.green. White plate, because
# the owner asked for the black one to go and a maskable icon cannot be clear.
ARROW = 'M0,-11.75 L9,11.75 L0,4.75 L-9,11.75 Z'
WINDMAP = dict(
    plate="#FFFFFF",
    art=''.join('<path d="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % a for a in [
            (ARROW, 'none', '#FFFFFF', '11'),
            (ARROW, 'none', '#0A1116', '8.5'),
            (ARROW, 'none', '#31A85A', '5'),
            (ARROW, '#31A85A', '#3A4750', '1'),
        ]),
    # Rotated and haloed, the arrow's box is 35.41 across and its centre sits at
    # (-3.69, 2.58) in the arrow's OWN coordinates, not at its origin. Scaling
    # about the origin therefore slides it: measured 8.3% left and 5.8% down of
    # a 64 box. The extra translate is what puts the shape, not the origin, in
    # the middle of the tile.
    box=35.41, bcx=-3.69, bcy=2.58,
)

JOBS = [
    ("freeflight-tools.github.io", FAMILY, [180, 192, 512]),
    ("hx-call",                    HXCALL, [180, 192, 512]),
    ("windgrade",                  WINDMAP, [180, 192, 512]),
]


def svg_for(spec):
    if "box" in spec:
        k = 64 * SAFE / spec["box"]
        inner = ('<g transform="translate(32 32) scale(%.5f) translate(%.3f %.3f) '
                 'rotate(35)" stroke-linejoin="round" stroke-linecap="round">%s</g>'
                 % (k, -spec["bcx"], -spec["bcy"], spec["art"]))
    else:
        inner = ('<g transform="translate(32 32) scale(%.4f) translate(-32 -32)">%s</g>'
                 % (SAFE, spec["art"]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
            'width="100%%" height="100%%">'
            '<rect width="64" height="64" fill="%s"/>%s</svg>' % (spec["plate"], inner))


def build(repo, spec, sizes):
    OUT.mkdir(parents=True, exist_ok=True)
    svg = svg_for(spec)
    for n in sizes:
        page = OUT / ("%s-%d.html" % (repo.replace(".", "_"), n))
        page.write_text(
            '<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0;overflow:hidden}'
            'svg{display:block;width:%dpx;height:%dpx}</style>%s' % (n, n, svg))
        png = OUT / ("%s-icon-%d.png" % (repo.replace(".", "_"), n))
        subprocess.run([CHROME, "--headless=new", "--hide-scrollbars",
                        "--force-device-scale-factor=1",
                        "--virtual-time-budget=3000",
                        "--window-size=%d,%d" % (n, n),
                        "--screenshot=%s" % png,
                        "file://%s" % page], capture_output=True)
        dest = REPOS / repo / ("icon-%d.png" % n)
        if not png.exists():
            print("FAILED", repo, n); sys.exit(1)
        dest.write_bytes(png.read_bytes())
        print("  wrote", dest)


for repo, spec, sizes in JOBS:
    print(repo)
    build(repo, spec, sizes)
