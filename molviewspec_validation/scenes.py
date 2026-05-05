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


def _get_emdb_vol_url(emdb_id, detail=4):
    emdb_num = emdb_id.lower().replace("emd-", "").replace("emd", "")
    return EMDB_VOL_URL.format(emdb_id=emdb_num, detail=detail)


def _get_pdb_url(pdb_id):
    return PDB_URL.format(pdb_id=pdb_id.upper())


def _apply_focus(component, view):
    if view in VIEW_DIRECTIONS:
        component.focus(**VIEW_DIRECTIONS[view])


def _add_density(builder, emdb_id, detail=4, absolute_isovalue=None,
                 relative_isovalue=None, color=VA_MAP_COLOR, opacity=VA_MAP_OPACITY):
    vol = builder.download(url=_get_emdb_vol_url(emdb_id, detail)).parse(format="bcif").volume()
    iso_kwargs = {"type": "isosurface"}
    if absolute_isovalue is not None:
        iso_kwargs["absolute_isovalue"] = absolute_isovalue
    elif relative_isovalue is not None:
        iso_kwargs["relative_isovalue"] = relative_isovalue
    else:
        iso_kwargs["relative_isovalue"] = 1.5
    vol.representation(**iso_kwargs).color(color=color).opacity(opacity=opacity)


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
    _add_density(builder, emdb_id, detail, absolute_isovalue, relative_isovalue)
    if view:
        _apply_focus(polymer, view)
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
        _apply_focus(polymer, view)
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
        _apply_focus(polymer, view)
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
        _apply_focus(polymer, view)
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
        _apply_focus(polymer, view)
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
  }}
  init();
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
