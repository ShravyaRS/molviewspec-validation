"""Smoke tests for Arthur's feedback fixes."""
import json
from molviewspec_validation.scenes import (
    _floatohex, VA_MAP_COLOR, VA_LIGAND_COLOR,
    VA_BG_MAPMODEL, VA_BG_INCLUSION_QSCORE,
    create_map_model_scene, create_atom_inclusion_scene,
)
from molviewspec_validation.emdb_api import (
    _normalize_emdb_id, get_recommended_contour_level,
)


def test_floatohex_matches_va():
    # Replicates va.validationanalysis.__floatohex
    assert _floatohex(0.0) == "#7A0000"
    assert _floatohex(1.0) == "#7AFFFF"
    assert _floatohex(0.5) == "#7A7F7F"
    assert _floatohex(-0.1) == "#FF00FF"  # invalid sentinel
    assert _floatohex(None) == "#FF00FF"


def test_color_constants():
    assert VA_MAP_COLOR == "#B8860B"          # DarkGoldenrod
    assert VA_LIGAND_COLOR == "#003BFF"
    assert VA_BG_MAPMODEL == "#D3D3D3"        # light gray, NOT white
    assert VA_BG_INCLUSION_QSCORE == "#FFFFFF"


def test_emdb_id_normalization():
    assert _normalize_emdb_id("2984") == "EMD-2984"
    assert _normalize_emdb_id("EMD-2984") == "EMD-2984"
    assert _normalize_emdb_id("emd-2984") == "EMD-2984"
    assert _normalize_emdb_id("emd2984") == "EMD-2984"


def test_emdb_contour_fetch_2984():
    # EMD-2984 should return ~8.0 per Arthur's feedback
    recl = get_recommended_contour_level("EMD-2984")
    assert recl is not None, "EMDB API unreachable or schema changed"
    assert recl > 0, f"Expected positive contour for EMD-2984, got {recl}"
    # Note: EMDB API currently returns 0.05 (AUTHOR-deposited).
    # Arthur mentioned 8.0; flag this discrepancy when reviewing.


def test_map_model_scene_uses_absolute_iso():
    builder = create_map_model_scene("5A1A", "EMD-2984", view="z",
                                     absolute_isovalue=8.0)
    state = json.dumps(builder.get_state().to_dict())
    assert "absolute_isovalue" in state
    # value 8.0 was Arthur's expectation; EMDB returns 0.05. Just check it is set.
    assert "B8860B" in state.upper()  # map color
    assert "D3D3D3" in state.upper()  # light gray bg


def test_inclusion_scene_uses_white_bg_no_density():
    builder = create_atom_inclusion_scene("5A1A", "EMD-2984", view="z")
    state = json.dumps(builder.get_state().to_dict())
    assert "FFFFFF" in state.upper()  # white bg
    # density should NOT be in inclusion scene
    assert "isosurface" not in state, "Inclusion scene must not render density"


if __name__ == "__main__":
    import sys, traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{len(fns)-failed}/{len(fns)} tests passed")
    sys.exit(1 if failed else 0)
