"""Integration with IHMValidation's em.py pipeline.

Provides a drop-in replacement for the ChimeraX-based image generation.
Generates base64-encoded PNG images matching the format expected by em.py.
"""

import base64
import os
import logging
import tempfile
from pathlib import Path
from typing import Optional

from molviewspec_validation.scenes import (
    create_map_model_scene,
    create_qscore_scene,
    create_atom_inclusion_scene,
    _builder_to_html,
)
from molviewspec_validation.screenshot import screenshot_html, _setup_driver


def _render_to_base64(builder, output_dir, filename, driver, wait_seconds=30):
    """Render a MolViewSpec scene to base64-encoded PNG."""
    html_path = os.path.join(output_dir, f"{filename}.html")
    png_path = os.path.join(output_dir, f"{filename}.png")

    html = _builder_to_html(builder, title=filename)
    with open(html_path, "w") as f:
        f.write(html)

    screenshot_html(html_path, png_path, wait_seconds=wait_seconds, driver=driver)

    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return b64


def generate_validation_images(
    pdb_id: str,
    emdb_id: str,
    structure_url: Optional[str] = None,
    output_dir: Optional[str] = None,
    wait_seconds: int = 30,
) -> dict:
    """Generate validation images matching em.py's expected format.

    Returns a dict with keys matching what em.py expects:
      - 'map_model': {'x': b64, 'y': b64, 'z': b64}
      - 'map_model_q': {'X': b64, 'Y': b64, 'Z': b64}
      - 'map_model_inclusion': {'x': b64, 'y': b64, 'z': b64}

    Parameters
    ----------
    pdb_id : str
        PDB ID (e.g., "5A1A")
    emdb_id : str
        EMDB ID (e.g., "EMD-2984")
    structure_url : str, optional
        URL to structure file. If None, fetches from PDB.
    output_dir : str, optional
        Directory for temp files. If None, uses a temp directory.
    wait_seconds : int
        Seconds to wait for each Mol* render.

    Returns
    -------
    dict
        Image data in the format expected by em.py's fit_plots.
    """
    cleanup = False
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="molviewspec_")
        cleanup = True
    os.makedirs(output_dir, exist_ok=True)

    result = {}
    driver = _setup_driver()

    try:
        # 1. Map-model surface plots (replaces *_xsurface.jpeg)
        logging.info("Generating map-model surface views...")
        map_model = {}
        for view in ["x", "y", "z"]:
            builder = create_map_model_scene(pdb_id, emdb_id, view=view)
            b64 = _render_to_base64(
                builder, output_dir, f"map_model_{view}", driver, wait_seconds
            )
            map_model[view] = b64
        result["map_model"] = map_model

        # 2. Q-score surface plots (replaces *_xqscoresurface.jpeg)
        logging.info("Generating Q-score surface views...")
        map_model_q = {}
        for view in ["x", "y", "z"]:
            builder = create_qscore_scene(
                pdb_id, emdb_id, structure_url=structure_url, view=view
            )
            b64 = _render_to_base64(
                builder, output_dir, f"qscore_{view}", driver, wait_seconds
            )
            map_model_q[view.upper()] = b64  # Note: uppercase keys for Q-score
        result["map_model_q"] = map_model_q

        # 3. Atom inclusion surface plots (replaces *_xfitsurface.jpeg)
        logging.info("Generating atom inclusion surface views...")
        map_model_inclusion = {}
        for view in ["x", "y", "z"]:
            builder = create_atom_inclusion_scene(
                pdb_id, emdb_id, structure_url=structure_url, view=view
            )
            b64 = _render_to_base64(
                builder, output_dir, f"inclusion_{view}", driver, wait_seconds
            )
            map_model_inclusion[view] = b64
        result["map_model_inclusion"] = map_model_inclusion

    finally:
        driver.quit()

    logging.info(f"Generated {sum(len(v) for v in result.values())} images")
    return result
