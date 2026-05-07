"""Scene generators for 3DEM validation views.

Replaces ChimeraX dependency for generating validation report images.
Uses MolViewSpec + Mol* for interactive browser-based visualization.

VA Color Scheme:
  Model/structure: #003BFF (blue)
  Map surface: #B8860B (dark goldenrod), transparency 0.65
  Atom inclusion: R=122, G=B=score*255 (dark red to cyan)
  Q-score: R=score*13, G=0, B=score*255 (black to blue/purple)
  Background: white
"""

import json
import os
from typing import Optional, Dict


def _fetch_emdb_contour(emdb_id):
    """Fetch depositor-recommended absolute contour level from EMDB API.
    Returns float or None.
    """
    import json, os, urllib.request
    eid = str(emdb_id).upper().replace("EMD-","").replace("EMD","").strip()
    cache = f"/tmp/emdb_contour_{eid}.json"
    if os.path.exists(cache):
        try:
            with open(cache) as f: return json.load(f).get("level")
        except Exception: pass
    try:
        url = f"https://www.ebi.ac.uk/emdb/api/entry/EMD-{eid}"
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read())
        for c in data.get("map",{}).get("contour_list",{}).get("contour",[]):
            if c.get("primary"):
                level = float(c["level"])
                with open(cache,"w") as f: json.dump({"level":level}, f)
                return level
    except Exception as e:
        print(f"  [warn] EMDB contour fetch failed for EMD-{eid}: {e}")
    return None


def _fetch_emdb_sigma(emdb_id, cache_dir="map_cache"):
    """Download (cached) EMDB .map.gz, read RMS (sigma) from CCP4 header.
    Returns float or None.
    """
    import os, urllib.request, gzip, struct, json, shutil
    eid = str(emdb_id).upper().replace("EMD-","").replace("EMD","").strip()

    sigma_cache = f"/tmp/emdb_sigma_{eid}.json"
    if os.path.exists(sigma_cache):
        try:
            with open(sigma_cache) as f:
                return json.load(f).get("sigma")
        except Exception:
            pass

    os.makedirs(cache_dir, exist_ok=True)
    map_path = os.path.join(cache_dir, f"emd_{eid}.map")
    if not os.path.exists(map_path):
        url = f"https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-{eid}/map/emd_{eid}.map.gz"
        try:
            print(f"  [sigma] downloading EMD-{eid} (one-time)")
            with urllib.request.urlopen(url, timeout=180) as resp:
                with gzip.GzipFile(fileobj=resp) as gz:
                    with open(map_path, "wb") as out:
                        shutil.copyfileobj(gz, out)
        except Exception as e:
            print(f"  [warn] sigma fetch failed for EMD-{eid}: {e}")
            return None

    try:
        with open(map_path, "rb") as f:
            header = f.read(1024)
        rms = struct.unpack_from("<f", header, 54*4)[0]
        if rms > 0:
            with open(sigma_cache, "w") as f:
                json.dump({"sigma": rms}, f)
            return rms
    except Exception as e:
        print(f"  [warn] sigma header read failed for EMD-{eid}: {e}")
    return None


import molviewspec as mvs


EMDB_VOL_URL = "https://maps.rcsb.org/em/emd-{emdb_id}/cell?detail={detail}"
PDB_URL = "https://files.rcsb.org/download/{pdb_id}.cif"

# VA color scheme constants
VA_MODEL_COLOR = "#003BFF"
VA_MAP_COLOR = "#B8860B"
VA_MAP_OPACITY = 0.35  # 1 - 0.65 transparency
VA_BG_COLOR = "white"

# VA atom inclusion palette: #7A0000 (score=0) to #7AFFFF (score=1)
VA_AI_PALETTE = [
    ("#7A0000", 0.0), ("#7A1919", 0.1), ("#7A3333", 0.2),
    ("#7A4C4C", 0.3), ("#7A6666", 0.4), ("#7A7F7F", 0.5),
    ("#7A9999", 0.6), ("#7AB2B2", 0.7), ("#7ACCCC", 0.8),
    ("#7AE5E5", 0.9), ("#7AFFFF", 1.0),
]

# VA Q-score palette: #000000 (score=0) to #0D00FF (score=1)
VA_QS_PALETTE = [
    ("#000000", 0.0), ("#010019", 0.1), ("#020033", 0.2),
    ("#03004C", 0.3), ("#050066", 0.4), ("#06007F", 0.5),
    ("#070099", 0.6), ("#0900B2", 0.7), ("#0A00CC", 0.8),
    ("#0B00E5", 0.9), ("#0D00FF", 1.0),
]

VIEW_DIRECTIONS = {
    "x": {"direction": (1, 0, 0), "up": (0, 1, 0)},
    "y": {"direction": (0, 1, 0), "up": (0, 0, -1)},
    "z": {"direction": (0, 0, 1), "up": (0, 1, 0)},
}



def _structure_extent(pdb_id):
    """Compute geometric extent of structure from CIF.
    Returns dict with: cx, cy, cz (bbox midpoint), and dx, dy, dz (bbox extents).
    Cached to /tmp.
    """
    import os, json, urllib.request
    pdb = pdb_id.upper()
    cache = f"/tmp/extent_{pdb}.json"
    if os.path.exists(cache):
        try:
            with open(cache) as f: return json.load(f)
        except Exception: pass
    try:
        url = f"https://files.rcsb.org/download/{pdb}.cif"
        with urllib.request.urlopen(url, timeout=30) as r:
            text = r.read().decode("utf-8", errors="ignore")
        coords = []
        in_loop = False
        cols = []
        for line in text.splitlines():
            if line.startswith("loop_"):
                in_loop = True; cols = []; continue
            if in_loop:
                if line.startswith("_atom_site."):
                    cols.append(line.strip())
                    continue
                if cols and (line.startswith("ATOM") or line.startswith("HETATM")):
                    try:
                        parts = line.split()
                        ix = cols.index("_atom_site.Cartn_x")
                        iy = cols.index("_atom_site.Cartn_y")
                        iz = cols.index("_atom_site.Cartn_z")
                        coords.append((float(parts[ix]), float(parts[iy]), float(parts[iz])))
                    except (ValueError, IndexError): pass
        if not coords:
            return None
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        zs = [c[2] for c in coords]
        result = {
            "cx": (min(xs) + max(xs)) / 2,  # bbox midpoint, not atom mean
            "cy": (min(ys) + max(ys)) / 2,
            "cz": (min(zs) + max(zs)) / 2,
            "dx": max(xs) - min(xs),
            "dy": max(ys) - min(ys),
            "dz": max(zs) - min(zs),
            "n_atoms": len(coords),
        }
        with open(cache, "w") as f: json.dump(result, f)
        print(f"  [extent] {pdb}: center=({result['cx']:.1f},{result['cy']:.1f},{result['cz']:.1f}) "
              f"extent=({result['dx']:.0f},{result['dy']:.0f},{result['dz']:.0f}) "
              f"({result['n_atoms']} atoms)")
        return result
    except Exception as e:
        print(f"  [warn] structure extent fetch failed for {pdb}: {e}")
    return None


def _get_emdb_vol_url(emdb_id, detail=4):
    emdb_num = emdb_id.lower().replace("emd-", "").replace("emd", "")
    return EMDB_VOL_URL.format(emdb_id=emdb_num, detail=detail)


def _get_pdb_url(pdb_id):
    return PDB_URL.format(pdb_id=pdb_id.upper())


def _apply_focus(component, view, builder=None, pdb_id=None, volume=None):
    """Camera framing using component.focus().

    DO NOT use builder.camera() — Mol* interprets explicit camera
    coordinates in fractional cell space when the CIF has degenerate
    unit cell (length_a=1.0), causing the camera to point at the wrong
    region. component.focus() is computed in Mol*'s scene space and
    works correctly.
    """
    if view not in VIEW_DIRECTIONS:
        return
    direction = VIEW_DIRECTIONS[view]["direction"]
    up = VIEW_DIRECTIONS[view]["up"]
    component.focus(radius_factor=1.5, direction=direction, up=up)


def _add_density(builder, emdb_id, detail=4, absolute_isovalue=None,
                 relative_isovalue=None, color=VA_MAP_COLOR, opacity=VA_MAP_OPACITY):
    vol = builder.download(url=_get_emdb_vol_url(emdb_id, detail)).parse(format="bcif").volume()
    iso_kwargs = {"type": "isosurface"}
    if absolute_isovalue is not None:
        iso_kwargs["absolute_isovalue"] = absolute_isovalue
    elif relative_isovalue is not None:
        iso_kwargs["relative_isovalue"] = relative_isovalue
    else:
        recl = _fetch_emdb_contour(emdb_id)
        sigma = _fetch_emdb_sigma(emdb_id) if recl is not None else None
        if recl is not None and sigma and sigma > 0:
            rel = recl / sigma
            iso_kwargs["relative_isovalue"] = rel
            print(f"  [contour] {emdb_id}: EMDB level {recl} = {rel:.2f} sigma")
        elif recl is not None:
            iso_kwargs["absolute_isovalue"] = recl
            print(f"  [contour] {emdb_id}: EMDB level {recl} (sigma unknown)")
        else:
            iso_kwargs["relative_isovalue"] = 1.0
            print(f"  [contour] {emdb_id}: no recommended level, using 1 sigma")
    vol.representation(**iso_kwargs).color(color=color).opacity(opacity=opacity)
    return vol

def create_map_model_scene(pdb_id, emdb_id, view=None, background=VA_BG_COLOR,
                           detail=4, absolute_isovalue=None, relative_isovalue=None):
    """Structure + density map isosurface (replaces *_xsurface.jpeg).
    Uses VA color scheme: model=#003BFF, map=#B8860B."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    struct = builder.download(url=_get_pdb_url(pdb_id)).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color(color=VA_MODEL_COLOR)
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color=VA_MODEL_COLOR)
    volume = _add_density(builder, emdb_id, detail, absolute_isovalue, relative_isovalue)
    if view:
        _apply_focus(polymer, view, builder, pdb_id=pdb_id, volume=volume)
    return builder


def create_qscore_scene(pdb_id, emdb_id, structure_url=None, view=None,
                        background=VA_BG_COLOR, detail=4,
                        absolute_isovalue=None, relative_isovalue=None):
    """Structure colored by Q-score + transparent density.
    Uses VA Q-score palette: black (#000000) to blue (#0D00FF)."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    url = structure_url or _get_pdb_url(pdb_id)
    struct = builder.download(url=url).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color_from_source(
        schema="all_atomic", category_name="atom_site",
        field_name="B_iso_or_equiv",
        palette={
            "kind": "continuous",
            "colors": [c for c, v in VA_QS_PALETTE],
            "mode": "absolute",
            "value_domain": (0.0, 100.0),
        },
    )
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color=VA_MODEL_COLOR)
    _add_density(builder, emdb_id, detail, absolute_isovalue, relative_isovalue,
                 opacity=0.2)
    if view:
        _apply_focus(polymer, view, builder, pdb_id=pdb_id)
    return builder


def create_atom_inclusion_scene(pdb_id, emdb_id, structure_url=None, view=None,
                                background=VA_BG_COLOR, detail=4,
                                absolute_isovalue=None, relative_isovalue=None):
    """Structure colored by atom inclusion score + transparent density.
    Uses VA AI palette: dark red (#7A0000) to cyan (#7AFFFF)."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    url = structure_url or _get_pdb_url(pdb_id)
    struct = builder.download(url=url).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color_from_source(
        schema="all_atomic", category_name="atom_site",
        field_name="B_iso_or_equiv",
        palette={
            "kind": "continuous",
            "colors": [c for c, v in VA_AI_PALETTE],
            "mode": "absolute",
            "value_domain": (0.0, 100.0),
        },
    )
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color=VA_MODEL_COLOR)
    _add_density(builder, emdb_id, detail, absolute_isovalue, relative_isovalue,
                 opacity=0.2)
    if view:
        _apply_focus(polymer, view, builder, pdb_id=pdb_id)
    return builder


def create_structure_scene(pdb_id, view=None, background=VA_BG_COLOR):
    """Structure only (no density map)."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    struct = builder.download(url=_get_pdb_url(pdb_id)).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color(color=VA_MODEL_COLOR)
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color=VA_MODEL_COLOR)
    if view:
        _apply_focus(polymer, view, builder, pdb_id=pdb_id)
    return builder


def create_va_inclusion_scene(cif_data_url, emdb_id, view=None, background=VA_BG_COLOR,
                              detail=4, absolute_isovalue=None, relative_isovalue=None):
    """Structure colored by actual VA atom inclusion scores + transparent density.
    Uses VA AI palette and custom CIF with scores in B-factor column."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    struct = builder.download(url=cif_data_url).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color_from_source(
        schema="all_atomic", category_name="atom_site",
        field_name="B_iso_or_equiv",
        palette={
            "kind": "continuous",
            "colors": [c for c, v in VA_AI_PALETTE],
            "mode": "absolute",
            "value_domain": (0.0, 100.0),
        },
    )
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color=VA_MODEL_COLOR)
    _add_density(builder, emdb_id, detail, absolute_isovalue, relative_isovalue,
                 opacity=0.2)
    if view:
        _apply_focus(polymer, view, builder, pdb_id=pdb_id)
    return builder


def _builder_to_html(builder, title="Mol* Viewer"):
    state = builder.get_state()
    mvsj_json = json.dumps(state.to_dict())
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
  #viewer {{ width: 100%; height: 100%; }}
</style>
<link rel="stylesheet" type="text/css" href="https://molstar.org/viewer/molstar.css" />
</head>
<body>
<div id="viewer"></div>
<script type="text/javascript" src="https://molstar.org/viewer/molstar.js"></script>
<script type="text/javascript">
  async function init() {{
    const viewer = await molstar.Viewer.create('viewer', {{
      layoutIsExpanded: false,
      layoutShowControls: false,
      layoutShowRemoteState: false,
      layoutShowSequence: true,
      layoutShowLog: false,
      layoutShowLeftPanel: false,
    }});
    const mvsData = {mvsj_json};
    await viewer.loadMvsData(mvsData, 'mvsj');
      window.__viewerInstance = viewer;
  }}
  init();
</script>
<script>
(function() {{
  var checks = 0, stable = 0;
  var poll = setInterval(function() {{
    checks++;
    var canvas = document.querySelector('#viewer canvas');
    var hasContent = canvas && canvas.width > 0;
    if (hasContent) {{
      stable++;
      if (stable >= 5) {{
        clearInterval(poll);
        try {{
        // For large structures, Mol*'s focus() can leave the camera stuck
        // at its initialization point. Force a reset to the actual scene
        // bounding sphere center.
        var v = window.__viewerInstance;
        if (v && v.plugin && v.plugin.canvas3d) {{
          var sphere = v.plugin.canvas3d.boundingSphereVisible;
          if (sphere && sphere.radius > 0) {{
            v.plugin.canvas3d.requestCameraReset({{ snapshot: {{ radius: sphere.radius * 1.4 }} }});
          }}
        }}
      }} catch(e) {{ console.warn('camera reset failed', e); }}
      window.__rendered = true;
        document.title = 'READY ' + document.title;
      }}
    }} else {{ stable = 0; }}
    if (checks > 240) {{
      clearInterval(poll);
      try {{
        // For large structures, Mol*'s focus() can leave the camera stuck
        // at its initialization point. Force a reset to the actual scene
        // bounding sphere center.
        var v = window.__viewerInstance;
        if (v && v.plugin && v.plugin.canvas3d) {{
          var sphere = v.plugin.canvas3d.boundingSphereVisible;
          if (sphere && sphere.radius > 0) {{
            v.plugin.canvas3d.requestCameraReset({{ snapshot: {{ radius: sphere.radius * 1.4 }} }});
          }}
        }}
      }} catch(e) {{ console.warn('camera reset failed', e); }}
      window.__rendered = true;
      document.title = 'TIMEOUT ' + document.title;
    }}
  }}, 1000);
}})();
</script>
</body>
</html>"""


def generate_validation_html(pdb_id, emdb_id, scene_type="map_model", view=None,
                             title=None, absolute_isovalue=None, **kwargs):
    """Generate HTML with Mol* viewer for validation report."""
    if title is None:
        view_label = f" ({view} view)" if view else ""
        title = f"{pdb_id} + {emdb_id} - {scene_type}{view_label}"
    creators = {
        "map_model": create_map_model_scene,
        "qscore": create_qscore_scene,
        "atom_inclusion": create_atom_inclusion_scene,
        "structure": create_structure_scene,
    }
    creator = creators[scene_type]
    if scene_type == "structure":
        builder = creator(pdb_id, view=view, **kwargs)
    else:
        builder = creator(pdb_id, emdb_id, view=view,
                         absolute_isovalue=absolute_isovalue, **kwargs)
    return _builder_to_html(builder, title)


def generate_all_views(pdb_id, emdb_id, output_dir=".", scene_types=None,
                       absolute_isovalue=None, **kwargs):
    """Generate all validation views (3 angles x scene types)."""
    os.makedirs(output_dir, exist_ok=True)
    if scene_types is None:
        scene_types = ["map_model", "qscore", "atom_inclusion"]
    outputs = {}
    for scene_type in scene_types:
        for view in ["x", "y", "z"]:
            fname = f"{pdb_id}_{emdb_id}_{scene_type}_{view}.html"
            fpath = os.path.join(output_dir, fname)
            html = generate_validation_html(
                pdb_id, emdb_id, scene_type=scene_type, view=view,
                absolute_isovalue=absolute_isovalue, **kwargs)
            with open(fpath, "w") as f:
                f.write(html)
            outputs[fname] = fpath
    return outputs
