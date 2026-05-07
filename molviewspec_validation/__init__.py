"""MolViewSpec-based 3DEM validation visualization.
Replaces ChimeraX dependency for generating structural views.
"""

from molviewspec_validation.scenes import (
    create_structure_scene,
    create_map_model_scene,
    create_qscore_scene,
    create_atom_inclusion_scene,
    create_va_inclusion_scene,
    generate_validation_html,
    generate_all_views,
)
from molviewspec_validation.screenshot import (
    screenshot_html,
    generate_screenshots,
)
from molviewspec_validation.integration import (
    generate_validation_images,
)
from molviewspec_validation.va_data import (
    parse_va_residue_inclusion,
    parse_va_chain_scores,
    create_scored_cif,
    cif_to_data_url,
)
from molviewspec_validation.emdb_api import (
    get_recommended_contour_level,
    fetch_emdb_metadata,
)

__version__ = "0.2.0"
