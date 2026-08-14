# Free Flight Tools

The landing page for a small set of free tools for cross-country paraglider
pilots. Live at **[freeflight-tools.github.io](https://freeflight-tools.github.io/)**.

| | |
|---|---|
| **[Windmap](https://github.com/freeflight-tools/xctrack-windmap)** | Wind stations near you, drawn where they actually are. An XCTrack overlay plus a standalone list. |
| **[HX Call](https://github.com/freeflight-tools/hx-call)** | The phone number that says whether a Swiss HX airspace is active. Needs no data connection, only enough signal to dial. |

## What's in here

    index.html      the whole site
    404.html        recovers a truncated link to a working tool
    icon.svg        the family mark, a ridge in contour lines
    img/            screenshots and the social preview cards
    img/screenshots/     the full-resolution masters the web files come from
    tools/og-card.html   regenerates img/og-hub.png

One file, no dependencies, no build step, same as the tools it links to.

## Running it

    python3 -m http.server 8080     # then http://localhost:8080

## Regenerating the preview image

The 1200×630 card chat apps show when the link is pasted. Serve the repo root,
then:

    CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "$CH" --headless=new --virtual-time-budget=5000 \
          --window-size=1200,630 --screenshot=img/og-hub.png \
          "http://localhost:8080/tools/og-card.html"

## Regenerating the tool screenshots

They are photographs of a phone running the widget over XCTrack's own map, not
captures of the standalone pages: that is what a pilot actually sees, and it is
the thing a stranger understands without reading anything. Take a new one on a
device, keep the transparent surround, and drop the master in `img/screenshots/`.
Then, from the repo root:

    for n in windmap hxcall; do
      magick "img/screenshots/$n-widget-source.png" -trim +repage \
             -resize 780x -strip /tmp/$n-big.png
      cwebp -q 82 -alpha_q 90 -m 6 -quiet /tmp/$n-big.png -o "img/$n-widget.webp"
      magick "img/screenshots/$n-widget-source.png" -trim +repage \
             -resize 560x -dither FloydSteinberg -colors 64 -strip "img/$n-widget.png"
    done

**The webp is what everyone gets** (~150 KB, full 780px). The png is the
fallback for a browser without webp, so it is deliberately smaller and coarser:
560px and 64 colours holds it near 230 KB, where a straight 780px png is 1.5 MB.
Regenerate the pair together, and update the `width`/`height` on the `<img>` if
the capture's aspect ratio changes.

The four older files, `img/windmap.png`, `img/hxcall.png` and their `-dark`
twins, were captures of the standalone list pages at 436px inside a card that
rendered ~640px, so they were upscaled and soft. `index.html` no longer uses
them; `_gtpreview.html` still does.

## Translation

English is the source language and stays that way in the apps themselves:
readings are read in the air, and aviation English is the right register for
them. This page and the two setup pages carry an automatic translation widget
instead. The slot for it is marked at the bottom of `index.html`.

It must never be added to `app.html` or `widget.html` in either tool. HX Call's
whole point is working with no data connection, and a third-party script would
put a network dependency inside that guarantee.

## Licence

MIT. No warranty of fitness for flight preparation.
