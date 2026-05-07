"""Integration with IHMValidation's em.py pipeline.

Drop-in replacement for ChimeraX-based image generation. Generates
base64-encoded PNGs in the format em.py expects.

If `contour_level` is provided (IHMValidation already retrieves it),
it's used directly. Otherwise it's auto-fetched from the EMDB API.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from typing import Optional

from molviewspec_validation.scenes import (
    create_map_model_scene,
    create_qscore_scene,
    create_atom_inclusion_scene,
    _builder_to_html,
)
from molviewspec_validation.screenshot import screenshot_html, _setup_driver
from molviewspec_validation.emdb_api import get_recommended_contour_level

log = logging.getLogger(__name__)


def _render_to_base64(builder, output_dir, filename, driver, wait_seconds=30):
    html_path = os.path.join(output_dir, f"{filename}.html")
    png_path = os.path.join(output_dir, f"{filename}.png")
    html = _builder_to_html(builder, title=filename)
    with open(html_path, "w") as f:
        f.write(html)
    screenshot_html(html_path, png_path, wait_seconds=wait_seconds, driver=driver)
    with open(png_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_validation_images(
    pdb_id: str,
    emdb_id: str,
    structure_url: Optional[str] = None,
    output_dir: Optional[str] = None,
    wait_seconds: int = 30,
    contour_level: Optional[float] = None,
) -> dict:
    """Generate validation images matching em.py's expected format.

    Parameters
    ----------
    pdb_id, emdb_id : str
    structure_url : optional URL to a CIF that already has scores in the
        B-factor column (for qscore/inclusion scenes)
    output_dir : optional directory for intermediate files
    wait_seconds : per-scene render timeout
    contour_level : if provided, used as the absolute isovalue for the
        map+model scene; otherwise auto-fetched from EMDB.
    """
    cleanup = False
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="molviewspec_")
        cleanup = True
    os.makedirs(output_dir, exist_ok=True)

    # Resolve contour ONCE so we don't re-hit the API per view.
    if contour_level is None:
        contour_level = get_recommended_contour_level(emdb_id)
        if contour_level is not None:
            log.info("Auto-fetched contour for %s: %s", emdb_id, contour_level)
        else:
            log.warning(
                "No recommended contour for %s; falling back to relative isovalue",
                emdb_id,
            )

    result: dict = {}
    driver = _setup_driver()
    try:
        # 1. Map+model surface (replaces *_xsurface.jpeg)
        log.info("Generating map+model surface views...")
        map_model = {}
        for view in ["x", "y", "z"]:
            builder = create_map_model_scene(
                pdb_id, emdb_id, view=view,
                absolute_isovalue=contour_level,
                auto_fetch_contour=False,  # already resolved above
            )
            map_model[view] = _render_to_base64(
                builder, output_dir, f"map_model_{view}", driver, wait_seconds,
            )
        result["map_model"] = map_model

        # 2. Q-score (replaces *_xqscoresurface.jpeg)
        log.info("Generating Q-score views...")
        map_model_q = {}
        for view in ["x", "y", "z"]:
            builder = create_qscore_scene(
                pdb_id, emdb_id, structure_url=structure_url, view=view,
            )
            map_model_q[view.upper()] = _render_to_base64(
                builder, output_dir, f"qscore_{view}", driver, wait_seconds,
            )
        result["map_model_q"] = map_model_q

        # 3. Atom inclusion (replaces *_xfitsurface.jpeg)
        log.info("Generating atom-inclusion views...")
        map_model_inclusion = {}
        for view in ["x", "y", "z"]:
            builder = create_atom_inclusion_scene(
                pdb_id, emdb_id, structure_url=structure_url, view=view,
            )
            map_model_inclusion[view] = _render_to_base64(
                builder, output_dir, f"inclusion_{view}", driver, wait_seconds,
            )
        result["map_model_inclusion"] = map_model_inclusion
    finally:
        driver.quit()

    log.info("Generated %d images", sum(len(v) for v in result.values()))
    return result
