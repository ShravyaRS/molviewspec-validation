# Validation results across full benchmark (v0.2.0)

Rendered with the EMDB-API contour fetch + sigma-conversion pipeline.
PNG sizes in KB shown for x/y/z views. Verdict based on file size > 500KB
threshold (below = blank canvas due to render race or contour edge case).

| PDB | EMDB | Sigma ratio | x (KB) | y (KB) | z (KB) | Verdict |
|---|---|---|---|---|---|---|
| 5A1A | EMD-2984 | 2.99 | 994 | 734 | 969 | PERFECT |
| 5A63 | EMD-3061 | 5.32 | 708 | 1006 | 707 | PERFECT |
| 9E9D | EMD-47792 | 4.09 | 1066 | 951 | 1211 | PERFECT |
| 9HYU | EMD-52518 | 6.42 | 2439 | 2967 | 1176 | PERFECT |
| 9IVJ | EMD-60928 | 3.06 | 1416 | 1419 | 1435 | PERFECT |
| 9LDX | EMD-63009 | 1.32 | 801 | 745 | 771 | PERFECT |
| 9LE2 | EMD-63013 | 1.54 | 736 | 667 | 747 | PERFECT |
| 9MKW | EMD-48340 | 2.91 | 919 | 979 | 1022 | PERFECT |
| 9N09 | EMD-48779 | 7.59 | 851 | 687 | 847 | PERFECT |
| 9NU5 | EMD-49797 | 13.40 | 1239 | 1133 | 1055 | PERFECT |
| 9P9C | EMD-71406 | 10.49 | 1396 | 1516 | 1174 | PERFECT |
| 9R0I | EMD-53483 | 8.37 | 1179 | 1084 | 995 | PERFECT |
| 9R1Q | EMD-53512 | 7.78 | 1326 | 1361 | 1257 | PERFECT |
| 9R5K | EMD-53590 | 0.67 | 518 | 392 | 402 | OK_1of3 |
| 9R85 | EMD-53804 | 8.06 | 367 | 993 | 851 | OK_2of3 |
| 9S98 | EMD-54674 | 3.59 | 3473 | 3487 | 2427 | PERFECT |
| 9SIQ | EMD-54930 | 5.84 | 1388 | 1423 | 348 | OK_2of3 |
| 9SYV | EMD-55355 | 5.81 | 1778 | 1634 | 1793 | PERFECT |
| 9T9U | EMD-55737 | 4.22 | 550 | 552 | 482 | OK_2of3 |
| 9TEO | EMD-55831 | 12.52 | 908 | 976 | 962 | PERFECT |
| 9TNZ | EMD-56096 | 7.52 | 817 | 864 | 421 | OK_2of3 |
| 9U2S | EMD-56518 | 13.34 | 696 | 745 | 622 | PERFECT |
| 9UCL | EMD-64047 | 3.17 | 557 | 542 | 427 | OK_2of3 |
| 9VBT | EMD-64933 | 2.90 | 618 | 700 | 709 | PERFECT |
| 9WUF | EMD-66260 | 5.64 | 1103 | 1083 | 901 | PERFECT |
| 9XED | EMD-66788 | 4.07 | 1539 | 613 | 588 | PERFECT |
| 9XZK | EMD-72359 | 15.80 | 236 | 213 | 233 | ALL_BLANK |
| 9Z8M | EMD-73900 | 1.53 | 161 | 168 | 167 | ALL_BLANK |

## Atom inclusion + Q-score sanity check

A 4-entry subset was rendered for the additional scene types to verify the
non-density-based pipeline (per-residue coloring, no isosurface):

| PDB | EMDB | Atom inclusion (3 views) | Q-score (3 views) |
|---|---|---|---|
| 5A1A | EMD-2984 | OK | OK |
| 9MKW | EMD-48340 | OK | OK |
| 9NU5 | EMD-49797 | OK | OK |
| 9R0I | EMD-53483 | OK | OK |

24/24 renders successful, with VA per-residue color gradients applied via
the `__floatohex` formula.
