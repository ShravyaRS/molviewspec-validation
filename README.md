# molviewspec-validation

MolViewSpec-based 3DEM validation visualization for [IHMValidation](https://github.com/salilab/IHMValidation).

Replaces ChimeraX dependency for generating structural views in the validation pipeline ([issue #127](https://github.com/salilab/IHMValidation/issues/127)).

## Features

### Scene Types
- **Map-model fit** -- structure + density map isosurface (replaces `*_xsurface.jpeg`)
- **Q-score colored** -- structure colored by Q-score with RdYlGn palette (replaces `*_xqscoresurface.jpeg`)
- **Atom inclusion colored** -- structure colored by real VA per-residue atom inclusion scores with RdYlGn palette (replaces `*_xfitsurface.jpeg`)

### Rendering
- 3 orthogonal views (X, Y, Z) with auto-centering via `focus()`
- HD static images (3840x1990 px) via headless Firefox + Selenium
- Interactive HTML with embedded Mol* viewer (rotate, zoom, click atoms)
- Density streaming from EMDB volume server (no local map download needed)

### VA Data Integration
- Reads per-residue atom inclusion scores from VA JSON output
- Creates custom CIF with scores in B-factor column for Mol* coloring
- Works with the actual VA pipeline data (not B-factor proxy)

### Integration
- Drop-in replacement for ChimeraX image generation in `em.py`
- Returns base64-encoded images in the format expected by `fit_plots`

## Usage

### Generate interactive HTML views
```python
from molviewspec_validation import generate_all_views

outputs = generate_all_views("5A1A", "EMD-2984", output_dir="views/")
# Creates 9 HTML files (3 views x 3 scene types)
```

### Use real VA atom inclusion data
```python
from molviewspec_validation import (
    parse_va_residue_inclusion, create_scored_cif,
    cif_to_data_url, create_va_inclusion_scene,
)

scores = parse_va_residue_inclusion("emd_2984.map_residue_inclusion.json")
create_scored_cif("5a1a.cif", "5a1a_scored.cif", scores)
data_url = cif_to_data_url("5a1a_scored.cif")
builder = create_va_inclusion_scene(data_url, "EMD-2984", view="z")
```

### Integration with IHMValidation em.py
```python
from molviewspec_validation import generate_validation_images

images = generate_validation_images("5A1A", "EMD-2984")
fit_plots['map_model'] = images['map_model']           # {'x': b64, 'y': b64, 'z': b64}
fit_plots['map_model_q'] = images['map_model_q']       # {'X': b64, 'Y': b64, 'Z': b64}
fit_plots['map_model_inclusion'] = images['map_model_inclusion']
```

## Validation

Tested on all 28 EMDB entries from the Q-score validation set (1.84-4.2 A resolution):

| Test | Result |
|------|--------|
| HTML generation (3 scene types x 3 views) | 28/28 pass, 252 files, 0 failures |
| VA data pipeline (real inclusion scores) | 28/28 pass |
| HD screenshot export (3840x1990) | Verified on 5 entries |
| Edge cases (small, large, nucleic acid, low-variance) | All pass |

## Architecture
molviewspec_validation/
init.py       -- Package exports
scenes.py         -- MolViewSpec scene builders (5 scene types)
screenshot.py     -- Headless Firefox HD PNG export
integration.py    -- Drop-in interface for em.py
va_data.py        -- VA JSON parsing + custom CIF creation

## Dependencies

- `molviewspec>=1.0`
- `gemmi` (for CIF manipulation)
- `selenium>=4.0` (for static image export)
- Firefox + geckodriver (for headless rendering)

## Related

- [IHMValidation #127](https://github.com/salilab/IHMValidation/issues/127) -- Re-implement plotting routines with Mol*
- [IHMValidation #119](https://github.com/salilab/IHMValidation/issues/119) -- Re-implement Q-score
- [qscore-mapq](https://github.com/ShravyaRS/qscore-mapq) -- Pure Python Q-score matching MapQ
