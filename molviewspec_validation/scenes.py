"""Scene generators for 3DEM validation views.

Replaces ChimeraX dependency for generating validation report images.
Uses MolViewSpec + Mol* for interactive browser-based visualization.
"""

import json
import os
from typing import Optional, Literal, Dict

import molviewspec as mvs


EMDB_VOL_URL = "https://maps.rcsb.org/em/emd-{emdb_id}/cell?detail={detail}"
PDB_URL = "https://files.rcsb.org/download/{pdb_id}.cif"

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


def _add_density(builder, emdb_id, detail=4, relative_isovalue=2.0,
                 color="lightskyblue", opacity=0.3):
    vol = builder.download(url=_get_emdb_vol_url(emdb_id, detail)).parse(format="bcif").volume()
    vol.representation(type="isosurface", relative_isovalue=relative_isovalue
    ).color(color=color).opacity(opacity=opacity)


def create_map_model_scene(pdb_id, emdb_id, structure_color="forestgreen",
                           view=None, background="white", detail=4,
                           iso_opacity=0.3, relative_isovalue=2.0):
    """Structure + density map isosurface (replaces *_xsurface.jpeg)."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    struct = builder.download(url=_get_pdb_url(pdb_id)).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color(color=structure_color)
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color="orange")
    _add_density(builder, emdb_id, detail, relative_isovalue, opacity=iso_opacity)
    if view:
        _apply_focus(polymer, view)
    return builder


def create_qscore_scene(pdb_id, emdb_id, structure_url=None, view=None,
                        background="white", detail=4, iso_opacity=0.15,
                        relative_isovalue=2.5):
    """Structure colored by Q-score (B-factor) + transparent density.
    Replaces *_xqscoresurface.jpeg."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    url = structure_url or _get_pdb_url(pdb_id)
    struct = builder.download(url=url).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color_from_source(
        schema="all_atomic", category_name="atom_site",
        field_name="B_iso_or_equiv",
        palette={"kind": "continuous", "colors": "RdYlGn"},
    )
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color="orange")
    _add_density(builder, emdb_id, detail, relative_isovalue, opacity=iso_opacity)
    if view:
        _apply_focus(polymer, view)
    return builder


def create_atom_inclusion_scene(pdb_id, emdb_id, structure_url=None, view=None,
                                background="white", detail=4, iso_opacity=0.15,
                                relative_isovalue=2.5):
    """Structure colored by atom inclusion score + transparent density.
    Replaces *_xfitsurface.jpeg."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    url = structure_url or _get_pdb_url(pdb_id)
    struct = builder.download(url=url).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color_from_source(
        schema="all_atomic", category_name="atom_site",
        field_name="B_iso_or_equiv",
        palette={"kind": "continuous", "colors": "Turbo"},
    )
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color="orange")
    _add_density(builder, emdb_id, detail, relative_isovalue, opacity=iso_opacity)
    if view:
        _apply_focus(polymer, view)
    return builder


def create_structure_scene(pdb_id, color="forestgreen", view=None, background="white"):
    """Structure only (no density map)."""
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    struct = builder.download(url=_get_pdb_url(pdb_id)).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color(color=color)
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color="orange")
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


def generate_validation_html(pdb_id, emdb_id,
                             scene_type="map_model", view=None, title=None, **kwargs):
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
        builder = creator(pdb_id, emdb_id, view=view, **kwargs)
    return _builder_to_html(builder, title)


def generate_all_views(pdb_id, emdb_id, output_dir=".", scene_types=None, **kwargs):
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
                pdb_id, emdb_id, scene_type=scene_type, view=view, **kwargs)
            with open(fpath, "w") as f:
                f.write(html)
            outputs[fname] = fpath
    return outputs


def create_va_inclusion_scene(
    cif_data_url, emdb_id, view=None, background="white",
    detail=4, iso_opacity=0.15, relative_isovalue=2.5,
    palette_name="RdYlGn",
):
    """Structure colored by actual VA atom inclusion scores + transparent density.
    Uses a custom CIF with inclusion scores in B-factor column.
    """
    builder = mvs.create_builder()
    builder.canvas(background_color=background)
    struct = builder.download(url=cif_data_url).parse(format="mmcif").model_structure()
    polymer = struct.component(selector="polymer")
    polymer.representation(type="cartoon").color_from_source(
        schema="all_atomic", category_name="atom_site",
        field_name="B_iso_or_equiv",
        palette={"kind": "continuous", "colors": palette_name},
    )
    struct.component(selector="ligand").representation(type="ball_and_stick").color(color="orange")
    _add_density(builder, emdb_id, detail, relative_isovalue, opacity=iso_opacity)
    if view:
        _apply_focus(polymer, view)
    return builder
