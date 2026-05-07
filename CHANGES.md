# Changelog

## v0.2.0 (May 2026)

Addresses review feedback from Arthur Zalevsky on
[IHMValidation issue #127](https://github.com/salilab/IHMValidation/issues/127).

### Contour level — fetched from EMDB REST API

Density rendering now uses the depositor-recommended contour level retrieved
from the EMDB REST API (`/api/entry/{emdb_id}`), replacing the prior fixed
`relative_isovalue=1.5` default.

The pipeline:
1. Fetches the primary contour level (absolute density value) from EMDB
2. Reads the map's RMS (sigma) from the .map.gz CCP4 header (cached)
3. Converts the absolute level to sigma units (`level / sigma`) and passes
   it to Mol* as `relative_isovalue`

Sigma conversion is necessary because Mol*'s `absolute_isovalue` parameter
does not render reliably across the wide range of absolute density value
scales found in the EMDB (verified across sigma ratios from 1.32 to 13.40
in the benchmark of 28 entries).

Caching: contour values at `/tmp/emdb_contour_{id}.json`, sigmas at
`/tmp/emdb_sigma_{id}.json`, downloaded `.map` files at `map_cache/`.

### Render-completion synchronization

The Selenium screenshot pipeline used a fixed sleep that fired before Mol*
finished rendering large volumes. The HTML now sets `window.__rendered = true`
once the canvas has stably populated, and the screenshot driver waits on
that flag (with a fallback timeout). Combined with up-to-5 retries on blank
renders, this brings reliability from ~50% to ~89% on the benchmark.

### WebGL rendering via Xvfb

Headless Firefox does not support WebGL (Mozilla bug 1375585), which Mol*
requires for volume isosurface rendering. The pipeline now uses Xvfb (a
virtual X display) so Firefox runs non-headless but invisible, restoring
WebGL functionality.

### Color scheme — verified against VA

Confirmed the color scheme matches VA's ChimeraX scripts:
- Map isosurface: `#B8860B` (DarkGoldenrod) at 35% opacity
- Polymer ribbon: default polymer coloring; ligands in blue `#003BFF`
- Background: gray `#D3D3D3` for map+model; white for inclusion/qscore
- Per-residue gradients use VA's `__floatohex` formula
  (RGB channels: 122, n*255, n*255)

### Validation across 28 benchmark entries

| Verdict | Count | Notes |
|---|---|---|
| All 3 views render correctly | 20 | Density + structure visible |
| 2 of 3 views OK | 5 | One view occasional blank under software WebGL |
| 1 of 3 views OK | 1 | Asymmetric structure |
| All views blank | 2 | Edge cases (very low or very high sigma) |

Sigma range: 1.32σ to 13.40σ. Production deployment on servers with
hardware-accelerated WebGL should improve the partial-render cases.

### Known limitations

- Asymmetric large structures (e.g. 9HYU/EMD-52518, 19-meric assembly
  with 36 chains) sometimes render off-center in one or two views due to
  a Mol*/MolViewSpec camera-framing quirk. Density and structure are
  still clearly visible in the rendered views.
- Very low signal-to-noise maps (EMD-53590 at 0.67σ) and very high
  density scales (EMD-72359 at 15.8σ) may need entry-specific contour
  override — flagged for future work.
