---
name: xctrack-web-widget
description: Build a web page widget for XCTrack, the Android flight computer used by paraglider and hang glider pilots. Use when writing, debugging or shipping any page that will be embedded in XCTrack's "Web page" widget, when reading the pilot's position from XCTrack, when a widget renders blank or white, when links or phone-dial schemes fail inside it, or when planning how pilots will install it. Covers the JS bridge, the required XCTrack settings, measured WebView capabilities, the transparent-background rule, battery discipline, offline caching and distribution.
---

# XCTrack web widgets

XCTrack is the dominant flight instrument app for paraglider and hang glider
pilots on Android. Its **Web page widget** embeds a URL in a WebView on the
pilot's navigation screen, alongside the map and the instruments.

Everything below is **measured on device** unless flagged otherwise. Sources are
two production widgets and an on-device capability probe (Android 17, WebView
150, 8 GB RAM). See `references/webview-environment.md` for the raw probe.

## What you are actually building

Assume all of these. They are not edge cases, they are the normal case.

- **A page read one-handed, in gloves, in bright sunlight, on a small screen**,
  by someone whose attention belongs outside the cockpit. Big tap targets, few
  elements, no scrolling.
- **On a battery that has to last the flight.** Every wakeup costs.
- **Often with no data connection.** Thermalling at 3000 m over a valley.
- **Static hosting.** There is no backend. If a data source needs a proxy for
  CORS, that is a finding to report to the user, not a licence to add a server.
- **The Web page widget is an XCTrack Pro feature.** State this once, quietly,
  on your setup page at the first step that needs it. It is a fact about
  XCTrack, not about your tool.

## The settings the pilot must set

Your setup page must list these. Each one has a failure mode if skipped.

| Setting | Why |
|---|---|
| **Allow web page to access XCTrack data** | ON. This is what exposes the `XCTrack` JS object. Without it you get no position at all. |
| **Allow tapping on the web page when locked** | ON, if your widget has any control. Otherwise the pilot cannot press anything in flight. |
| **Disable unlocking** | ON, so a stray swipe does not rearrange the layout. |
| **Refresh rate: 0** | **Critical.** See below. |

### Refresh rate must be 0, and this is not a preference

XCTrack substitutes `${lat}` and `${lng}` in the widget URL. **If the URL
contains those placeholders, XCTrack reloads the entire page at the refresh
rate.** A 5-second refresh means your page restarts every 5 seconds: state lost,
network refetched, battery burned.

Set **refresh rate 0** and poll `XCTrack.getLocation()` yourself. The page then
lives for the whole flight and updates itself.

## Position: the only API you get

The bridge is a **pull** API. There is no callback, no event, no subscription.

```js
var HAS_XCT = (function () {
  try { return typeof XCTrack !== "undefined" &&
               typeof XCTrack.getLocation === "function"; }
  catch (e) { return false; }
})();

function readXCTrack() {
  var raw;
  try { raw = XCTrack.getLocation(); } catch (e) { return null; }
  if (!raw || raw === "null") return null;          // string "null", not null
  var o;
  try { o = JSON.parse(raw); } catch (e) { return null; }
  if (!o || o.isValid === false) return null;
  if (typeof o.lat !== "number" || typeof o.lon !== "number") return null;
  return { lat: o.lat, lon: o.lon };
}
```

Four things that will bite you, all measured:

- **It returns the string `"null"`**, not `null`, before the GPS has a fix.
  Handle it as a string.
- **It carries `isValid`.** Respect it. A payload can parse and still be invalid.
- **XCTrack's GPS runs at 1 Hz**, so polling faster than 1 Hz cannot return
  anything new. It only crosses the JS bridge more often.
- **The probe found exactly one method exposed: `getLocation`.** Do not assume
  altitude, heading, speed or anything else is available. Check before relying
  on it, and degrade gracefully.

### Build a position fallback chain

`getLocation()` returns `"null"` for the first seconds after launch, which is
exactly when the pilot is standing at take-off looking at a blank widget and
concluding your tool is broken. Cover that gap:

1. `XCTrack.getLocation()` when valid.
2. **URL parameters** `?lat=…&lng=…`, which XCTrack fills from its **last known
   position** via `${lat}`/`${lng}`. This is what covers the cold start.
3. Browser geolocation, for the same page opened outside XCTrack.
4. **Last known position from `localStorage`**, so a cold start has something.

### The `${lat}` trap

Append the placeholders **raw**, never percent-encoded:

```
https://example.com/widget.html?scale=8000&lat=${lat}&lng=${lng}
```

**An unsubstituted placeholder arrives as the literal string `${lat}`.** It must
parse to `NaN` and be ignored so the chain falls through, rather than being
treated as a position. Guard it.

And keep refresh rate at 0, per above. The placeholders are only safe there.

## What the WebView can and cannot do

Measured on Android 17, current WebView, 8 GB RAM. Do not re-derive.

- **No WebGL.** `webgl: false`. This is not an old-device artefact; WebGL is not
  exposed to XCTrack's WebView. **MapLibre and any WebGL renderer are out.**
  Canvas 2D, `OffscreenCanvas` and WebP are all available.
- **`devicePixelRatio` was 3** (448×978 CSS, 1344×2934 physical). Rendering a
  map at full DPR costs roughly 9× the fill rate for no legibility gain. Cap a
  canvas backing store at DPR 1–2.
- **`tel:` and every non-http(s) scheme are dead**, and worse than dead. An
  anchor `tel:` link, assignment to `location`, `intent://…ACTION_DIAL` and
  `window.open` **all** land on the "Web page not available" error page, which
  **strands the widget there until it reloads**. `navigator.clipboard` works, so
  copy the number instead. Detect via the JS bridge or the `wv` token in the
  user agent (Chrome proper does not carry it, so a normal browser still dials).
- **CORS applies exactly as in a browser.** A source without
  `access-control-allow-origin` is unreachable from a static widget, whatever
  you write. Verify with the deployed origin before designing around a source.
- **Storage is abundant**: ~10 GB quota, Service Worker, Cache Storage,
  IndexedDB and `localStorage` all present. HTTP range requests return 206.
- **Write ES5.** No modules, no optional chaining, no transpilation step.
  Old Android WebViews are in the field.

## The widget body must stay unpainted

**XCTrack renders a white or absent background as transparent**, so the widget
floats over the moving map. This is the single most useful visual property of
the platform, and it is easy to destroy.

- Never set a background on `body`.
- Every element that needs contrast carries **its own** background.
- Consequently the widget usually **cannot share a stylesheet** with your other
  pages, since any global background defeats it. Duplicate the few tokens you
  need into the widget's own `<style>`.
- Repeat defensive CSS there too. The one that has already bitten:
  `[hidden]{display:none !important}`. Browsers apply `hidden` as a
  low-priority rule, so any author rule setting `display` silently outranks it
  and leaves a supposedly hidden control on screen, mispositioned and inert.

**An empty widget is correct output.** Drawing nothing while the GPS has no fix,
and nothing when there is nothing to say, is right for a panel floating over a
map. Say so on your setup page so it does not read as a bug.

## Cost discipline

A widget runs for hours on a battery that must outlast the flight.

**Compute a cheap key first, and put every expensive thing behind it.**

```js
var key = [qx, qy, w, h, lastFetch, minute].join("|");
if (key === lastKey) return;        // nothing can have changed
lastKey = key;
/* everything expensive lives below this line */
```

Include **the minute** in the key. Staleness is the one thing that changes
without any input changing, so without it a display can silently go stale; with
it you get at most one redraw a minute when parked.

- **Do not move work in front of the key.** In one measured case a widget was
  running its full prepare-and-rank pass plus a synchronous `localStorage`
  write **twice a second**, while a comment claimed it was "nearly free": 82 of
  each per 40 seconds, reduced to 2.
- **Build elements once, then write only changed text nodes.** Compare before
  assigning, `className` included. A stationary pilot should cause zero writes.
- **Pause on `document.hidden`.**
- **Poll no faster than the data changes.** 1 Hz for position is the ceiling
  (XCTrack's GPS rate). For network data, match the source: 10 minutes is
  typical for weather. Throttle `localStorage` writes; they exist for a cold
  start, not as a log.

## Offline

A service worker is an **enhancement, never a dependency**. Swallow every
registration failure so an old WebView still gets a working page.

- **Key the cache on the path, not the full URL.** XCTrack's
  `?lat=…&lng=…` reloads miss a full-URL cache every single time.
- **Prefer stale-while-revalidate** over cache-first, so a correction can still
  reach a pilot who already has the page cached.
- **Never cache a live reading.** Guard by origin. A cache that served an old
  measurement as current would defeat your staleness logic from behind, which
  in a flight tool is a safety problem, not a bug.

## Testing

- **Never open the page via `file://`.** Browsers refuse geolocation there.
- **`localhost` is a secure context; a LAN address like `192.168.x.x` is not**,
  so geolocation is blocked when testing from a phone on your network. Publish
  to the real host, or open a tunnel:
  `cloudflared tunnel --url http://localhost:8080`.
- **Test without a position** by appending `?lat=47.05&lng=8.64`.
- **With a service worker, an edit takes two reloads to appear.** Hard-reload,
  or tick *Bypass for network* in DevTools → Application → Service workers.
  Chasing a change that "didn't take" is a good way to lose an hour.
- **Headless screenshots do not capture a canvas drawn asynchronously.** The
  markers come out blank even when `getImageData` proves they are there. Render
  the same calls synchronously in a test page, or check SVG output instead.
- **A headless capture can be narrower than the page's own viewport**, so
  content at the right edge is cropped rather than overflowing. Screenshot
  100–150 px wider than the layout you are checking before concluding anything
  about the right-hand edge.

## Getting it onto a pilot's phone

- **Never link to your widget URL from your setup page.** Opened in a normal
  browser it is a transparent page that may draw nothing at all, so it renders
  as a blank white page and reads as broken. Both projects behind this skill did
  this and both produced exactly that. A **URL box plus a QR code** is how the
  widget URL reaches a phone.
- Build the URL with a small configurator so the pilot never hand-edits query
  parameters.
- Write the setup page **for a pilot, not for a developer**: numbered steps,
  short sentences, and the reasons kept in HTML comments rather than on screen.

## Checklist

- [ ] Refresh rate 0, and the URL carries `${lat}`/`${lng}` raw
- [ ] Literal `${lat}` is ignored rather than parsed
- [ ] `getLocation()` guarded for `"null"`, `isValid`, and a missing bridge
- [ ] Position falls back: bridge → URL → geolocation → last known
- [ ] `body` has no background; every chip carries its own
- [ ] ES5 only, no modules, no build output required at runtime
- [ ] Tick loop computes a cheap key first, minute included
- [ ] Loop pauses on `document.hidden`
- [ ] No `tel:` or non-http scheme anywhere
- [ ] Service worker keyed on path, never caches a reading
- [ ] Setup page: Pro note once, the four settings, QR, no link to the widget

## Reference files

- `references/webview-environment.md` — the raw on-device probe, and how to run
  your own.
- `references/map-overlay.md` — for widgets that overlay XCTrack's own map:
  its scale ladder, the device-pixel correction, and the calibration constant.
  Only needed if your widget must register against the map underneath it.
