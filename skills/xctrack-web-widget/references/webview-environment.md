# XCTrack's WebView: measured capabilities

Raw output from a capability probe served over HTTPS and opened inside
XCTrack's Web page widget. **Android 17, WebView 150, 8 GB RAM, 2026-08-10.**

Re-run it before trusting any of this on a new XCTrack or Android release.

```json
{
 "userAgent": "Mozilla/5.0 (Linux; Android 17; Build/CP41.260717.006; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 ",
 "protocol": "https:",
 "secureContext": true,
 "screen": "448x978 @3",
 "deviceMemoryGB": 8,
 "hardwareConcurrency": 9,

 "XCTrack object": true,
 "XCTrack methods": "getLocation",
 "getLocation() raw": "null",

 "serviceWorker": true,
 "caches": true,
 "indexedDB": true,
 "storageManager": true,
 "localStorage": true,
 "quota": "10250.1 MB",

 "canvas2d": true,
 "webgl": false,
 "OffscreenCanvas": true,
 "webp": true,

 "range status": 206,
 "content-range": "bytes 0-99/4948"
}
```

## What each line settles

**`webgl: false`** on a current WebView with 8 GB of RAM. Not an old-device
artefact: WebGL is simply not exposed to XCTrack's WebView. Any WebGL renderer
(MapLibre, deck.gl, three.js) is unusable. Canvas 2D is the only path, and
`OffscreenCanvas` means rasterisation can move off the main thread if needed.

**`"XCTrack methods": "getLocation"`** — one method, and that is the whole
bridge as probed. Do not assume altitude, heading, ground speed, vario or
airspace state are reachable. Feature-detect anything else and degrade.

**`"getLocation() raw": "null"`** — the probe ran indoors with no GPS fix, which
is how the string-`"null"` behaviour was found. It also means the payload shape
was never captured here; treat field names beyond `lat`, `lon` and `isValid` as
unverified.

**`screen: "448x978 @3"`** — `devicePixelRatio` 3, i.e. 1344×2934 physical
pixels. Rendering a full-screen canvas at native DPR costs about 9× the fill
rate of DPR 1, for no legibility gain at map scales. Cap the backing store at
DPR 1–2.

**`secureContext: true` over HTTPS** — geolocation, service workers and the
clipboard are all available, provided you serve over HTTPS. They are not on
`file://` or on a plain-HTTP LAN address.

**Storage**: ~10 GB quota, all four storage APIs present, and byte ranges
answered with 206. Large offline assets are viable. Note `persist()` was never
requested in this probe, so eviction behaviour under pressure is unverified.

## CORS from inside the WebView

Measured in the same run, and it matters because a widget on static hosting has
no proxy:

- A source sending `access-control-allow-origin` succeeded (200 in ~290 ms).
- A source **without** it failed with `BLOCKED (Failed to fetch)`, exactly
  matching what `curl -H 'Origin: …'` predicted from a laptop.

So you can test CORS from your desk and trust the answer. Check with the real
deployed origin before designing around any data source.

## Writing your own probe

A single static page that collects the values above and prints them as JSON,
opened inside the widget, plus a way to get the text out (the clipboard works;
`tel:` and other schemes do not). Keep it in the repo: it is the only way to
answer "did this break in the new XCTrack?" without guessing.

Two traps when writing one:

- **Wrap every access in `try/catch`.** Touching a missing API can throw and
  abort the whole collection, leaving you with a blank page and no clue why.
- **Print to the DOM, not only to `console`.** There is no DevTools attached to
  a widget in flight.
