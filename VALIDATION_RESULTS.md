# Validation Results

## Benchmark Dataset

28 single-particle cryo-EM entries spanning 1.84-4.20 A resolution.

| # | PDB | EMDB | Res (A) | Residues | Atoms | Category |
|---|-----|------|---------|----------|-------|----------|
| 1 | 9HYU | EMD-52518 | 1.84 | 4543 | 35600 | High-res, large, with ligands |
| 2 | 5A1A | EMD-2984 | 2.20 | 4108 | 32124 | High-res, symmetric tetramer |
| 3 | 9R1Q | EMD-53512 | 2.24 | 3996 | 31300 | High-res, large |
| 4 | 9VBT | EMD-64933 | 2.30 | 3486 | 27300 | High-res, large |
| 5 | 9UCL | EMD-64047 | 2.43 | 2031 | 15900 | Medium-high res |
| 6 | 9N09 | EMD-48779 | 2.57 | 1023 | 8000 | Medium |
| 7 | 9T9U | EMD-55737 | 2.61 | 4120 | 32300 | Large |
| 8 | 9Z8M | EMD-73900 | 2.70 | 2400 | 18800 | Large |
| 9 | 9LDX | EMD-63009 | 2.83 | 1165 | 9100 | Medium |
| 10 | 9SYV | EMD-55355 | 2.89 | 2274 | 17800 | Large |
| 11 | 9SIQ | EMD-54930 | 2.96 | 1785 | 14000 | Medium-large |
| 12 | 9WUF | EMD-66260 | 3.01 | 1212 | 9500 | Medium |
| 13 | 9R85 | EMD-53804 | 3.04 | 886 | 6900 | Medium |
| 14 | 9R0I | EMD-53483 | 3.10 | 551 | 4300 | Small |
| 15 | 9IVJ | EMD-60928 | 3.15 | 1173 | 9200 | Medium |
| 16 | 9U2S | EMD-56518 | 3.20 | 870 | 6800 | Protein + nucleic acid |
| 17 | 9E9D | EMD-47792 | 3.24 | 3882 | 30400 | Large |
| 18 | 9TEO | EMD-55831 | 3.27 | 767 | 6000 | Medium |
| 19 | 9LE2 | EMD-63013 | 3.33 | 1166 | 9100 | Medium |
| 20 | 5A63 | EMD-3061 | 3.40 | 1245 | 9800 | Medium |
| 21 | 9XED | EMD-66788 | 3.40 | 2036 | 16000 | Large |
| 22 | 9TNZ | EMD-56096 | 3.52 | 2574 | 20200 | Large |
| 23 | 9MKW | EMD-48340 | 3.63 | 1253 | 9800 | Medium |
| 24 | 9NU5 | EMD-49797 | 3.70 | 532 | 4200 | Small |
| 25 | 9S98 | EMD-54674 | 3.86 | 567 | 4400 | Small |
| 26 | 9XZK | EMD-72359 | 3.91 | 492 | 3900 | Small, low-variance map |
| 27 | 9P9C | EMD-71406 | 4.01 | 2312 | 18100 | Large, low-res |
| 28 | 9R5K | EMD-53590 | 4.20 | 1066 | 8400 | Protein + nucleic acid, lowest res |

## Test Results

### Test 1: HTML Generation

Generates 6 HTML files per entry (map_model + qscore, 3 views each).

| Metric | Result |
|--------|--------|
| Entries tested | 28/28 |
| Files generated | 168 |
| Failures | 0 |
| Time | <3s |
| Min file size | >500 bytes (all verified) |

### Test 2: VA Data Pipeline

Reads real per-residue atom inclusion scores from VA JSON output,
creates custom CIF with scores in B-factor column, generates colored views.

| Metric | Result |
|--------|--------|
| Entries tested | 28/28 |
| Files generated | 252 (9 per entry) |
| Failures | 0 |
| Score range | 0.0 - 1.0 |
| Residue count range | 492 - 4543 |

### Test 3: Edge Cases

| Entry | Description | Result |
|-------|-------------|--------|
| 9NU5 | Small protein (532 residues) | PASS |
| 9HYU | Large complex with ligands (4543 residues) | PASS |
| 9R5K | Protein + nucleic acid (4.2 A) | PASS |
| 9XZK | Low-variance density map | PASS |
| 9P9C | Low resolution (4.01 A) | PASS |

### Test 4: HD Screenshot Export

| Entry | Scene | Size | Dimensions | Status |
|-------|-------|------|------------|--------|
| 5A1A | map_model | 3631 KB | 3840x1990 | VALID |
| 5A1A | inclusion | 3498 KB | 3840x1990 | VALID |
| 9XZK | map_model | 1581 KB | 3840x1990 | VALID |
| 9XZK | inclusion | 1411 KB | 3840x1990 | VALID |
| 9HYU | map_model | 2813 KB | 3840x1990 | VALID |
| 9HYU | inclusion | 2855 KB | 3840x1990 | VALID |

## Validation Criteria

1. **HTML generation**: Every entry must produce valid HTML files (>500 bytes) for all scene types and views without exceptions.
2. **VA data parsing**: Every residue inclusion JSON must parse into a non-empty score dictionary with values in [0, 1].
3. **CIF modification**: The scored CIF must be writable by gemmi and loadable by Mol* (verified via data URL embedding).
4. **Scene rendering**: Mol* must render the structure, density, and coloring without errors (verified via browser and screenshots).
5. **Screenshot export**: Headless Firefox must produce valid PNG files at 3840x1990 resolution (verified via PIL Image.verify).

## Known Limitations

1. **Very large CIF files** (>8 MB, e.g., 9HYU with 4543 residues): Data URL embedding produces HTML files >11 MB. For screenshots, a local HTTP server is used instead. Does not affect production use since em.py uses base64 images directly.
2. **Headless Firefox memory**: Each screenshot requires a fresh browser instance to avoid memory exhaustion. This makes batch screenshots slower (~40s per image) but reliable.
3. **Color palette accuracy**: Q-score and atom inclusion coloring uses MolViewSpec's continuous palette system (RdYlGn, Turbo). The exact color mapping may differ slightly from ChimeraX's rendering, but the information content is identical.
