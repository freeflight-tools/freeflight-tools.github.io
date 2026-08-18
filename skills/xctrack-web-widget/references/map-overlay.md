# Overlaying XCTrack's own map

Only needed if your widget must draw things that **line up with the map
underneath it**: markers at real coordinates, a scale bar, anything geographic.

The idea is cheap and effective: XCTrack renders a white or absent background as
transparent, so a full-width widget becomes a transparent layer over the moving
map. You draw arrows, dots or labels; XCTrack supplies the terrain. No basemap,
no tiles, no storage.

The hard part is registration: knowing how many metres a pixel is worth.

## XCTrack does not tell you its zoom

There is **no API for the map scale**. The only exposed method is
`getLocation()`. So the widget's scale is a **setting the pilot chooses**, and
your job is to convert it into a projection that matches.

Ask for a **ground distance** (e.g. "8 km across"), not a zoom level. The same
zoom is a different scale on a different screen, so a step number means nothing
to a pilot and cannot be carried between devices.

## The scale ladder

XCTrack's map scale is a resolution on an exact power-of-two ladder, but it is
**not on integer OSM zoom levels**. Measured relation:

```
z = (mapWidget_scale.value - 3) / 2
```

Odd ladder steps land on integer zooms and even steps land on **half** zooms, so
**one ladder step is √2 in scale**. That is why 5 km and 10 km never line up
with anything: they sit exactly half a zoom level off the integers. If your
projector accepts fractional zoom, half-steps need no special case.

Verified at three steps, predicted against measured metres per pixel:

| step | zoom | predicted | measured |
|---|---|---|---|
| 23 | 10 | 109.93 | 109.89 |
| 25 | 11 | 54.96 | 54.95 |
| 27 | 12 | 27.48 | 27.47 |

## The projection, with its correction

```
m per CSS px = 156543.034 · cos(lat) / 2^z / CAL

CAL = 0.942 · 3 / devicePixelRatio
```

Two separate corrections are folded into `CAL`, and they have different causes.

### 1. XCTrack runs 1.062× coarser than OSM: the 0.942

The ladder is power-of-two but offset from the standard Web Mercator resolutions
by a constant factor. `0.942` is that factor, measured against airspace edges at
three ladder steps.

**Caveat, unresolved:** it was confirmed at one latitude (47.36°N). Whether it
holds across a wider latitude span is unverified.

### 2. The map is drawn in DEVICE pixels, not CSS pixels

This is the one that wastes a day if you miss it. Measured on one emulator at
two pixel densities:

| | density A | density B | spread |
|---|---|---|---|
| metres per **device** pixel | 51.5 | 52.9 | **2.8%** |
| metres per **CSS** pixel | 135.1 | 105.9 | **28%** |

Device pixels are nearly invariant; CSS pixels are not. So the constant, which
was measured on a phone at `devicePixelRatio` 3, must be scaled by
`3 / devicePixelRatio`.

**Compute this, never configure it.** Read `window.devicePixelRatio` and apply
it. Do not add a per-device setting; the correction is derivable and a setting
would just be a way to get it wrong.

## Two things that must not be used to compute geometry

- **The printed km labels on XCTrack's own scale bar.** They are rounded, and
  they are a property of the screen rather than of the projection.
- **Any bar-matching done before the DPR correction is applied.** You will
  calibrate against an already-wrong number and bake the error in.

## Build a ruler before you build the overlay

Make a diagnostic page that measures XCTrack's resolution **without using your
calibration at all**: draw a bar of known CSS width, have the pilot compare it
against XCTrack's own scale bar, and report the ratio. That instrument is what
settles arguments like device-versus-CSS pixels. Keep it in the repo; it is the
only way to re-verify after an XCTrack update.

## Declutter, if you draw many markers

Two markers closer together than a marker is wide cannot both be drawn. Some
notes from doing this badly first:

- **Cull to the viewport before applying any "max markers" limit.** Distance
  ranking is a circle and a widget is a tall rectangle, so ranking first spends
  slots on markers off the sides that can never be drawn.
- **Zooming in does not always separate a pair.** Both axes must clear, and the
  vertical requirement is usually larger, so a north-south valley declutters
  hardest along the valley. Expect complaints that a station "is missing" when
  it is being decluttered rather than not fetched.
- If you displace a marker to make it fit, **annotate the displacement** with a
  leader line back to its true position, and make it opt-in. Drawing a
  measurement somewhere it was not taken is a real cost, however small.
