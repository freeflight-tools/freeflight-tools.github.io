# Free Flight Tools

The landing page for a small set of free tools for cross-country paraglider
pilots. Live at **[freeflight-tools.github.io](https://freeflight-tools.github.io/)**.

| | |
|---|---|
| **[Windmap](https://github.com/freeflight-tools/xctrack-windmap)** | Wind stations near you, drawn where they actually are. An XCTrack overlay plus a standalone list. |
| **[HX Call](https://github.com/freeflight-tools/hx-call)** | The phone number that says whether a Swiss HX airspace is active. Works with no signal. |

## What's in here

    index.html      the whole site
    404.html        recovers a truncated link to a working tool
    icon.svg        the family mark — a ridge in contour lines
    img/            screenshots and the social preview cards
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

The screenshots in `img/` are captured from the running apps — see
`tools/og-card.html` in each tool's repo for those two commands, including the
note about picking a moment when the readings are fresh.

## Translation

English is the source language and stays that way in the apps themselves:
readings are read in the air, and aviation English is the right register for
them. This page and the two setup pages carry an automatic translation widget
instead — the slot for it is marked at the bottom of `index.html`.

It must never be added to `app.html` or `widget.html` in either tool. HX Call's
whole point is working with no data connection, and a third-party script would
put a network dependency inside that guarantee.

## Licence

MIT. No warranty of fitness for flight preparation.
