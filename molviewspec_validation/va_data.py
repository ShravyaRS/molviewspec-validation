"""Read VA (Validation Analysis) output data and create custom CIF files.

Reads per-residue atom inclusion and Q-score data from VA JSON outputs,
injects scores into the B-factor column of a CIF file for Mol* coloring.
"""

import json
import os
import base64
from typing import Optional

import gemmi


def parse_va_residue_inclusion(json_path: str, contour_level: str = None):
    """Parse VA residue inclusion JSON into a (chain, resnum) -> score dict.
    
    Parameters
    ----------
    json_path : str
        Path to emd_*.map_residue_inclusion.json
    contour_level : str, optional
        Contour level key. If None, uses first available.
    
    Returns
    -------
    dict
        Mapping of (chain, resnum) -> inclusion_score (0-1)
    """
    with open(json_path) as f:
        data = json.load(f)
    
    ri = data['residue_inclusion']
    model_key = list(ri.keys())[0]
    model_data = ri[model_key]
    
    if contour_level is None:
        contour_level = list(model_data.keys())[0]
    
    level_data = model_data[contour_level]
    residues = level_data['residue']
    scores = level_data['inclusion']
    
    lookup = {}
    for res_str, score in zip(residues, scores):
        parts = res_str.split()
        chain_res = parts[0]
        chain, resnum = chain_res.split(':')
        lookup[(chain, resnum)] = score
    
    return lookup


def parse_va_chain_scores(json_path: str):
    """Parse VA all.json for per-chain atom inclusion scores.
    
    Returns
    -------
    dict
        Per-chain scores: {chain_id: {'value': float, 'color': str, 'numberOfAtoms': int}}
    """
    with open(json_path) as f:
        data = json.load(f)
    
    key = list(data.keys())[0]
    ai = data[key]['atom_inclusion_by_level']['0']
    return ai.get('chainaiscore', {})


def create_scored_cif(
    input_cif: str,
    output_cif: str,
    score_lookup: dict,
    scale: float = 100.0,
):
    """Create a modified CIF with scores in the B-factor column.
    
    Parameters
    ----------
    input_cif : str
        Path to original CIF file.
    output_cif : str
        Path for output CIF with scores.
    score_lookup : dict
        Mapping of (chain, resnum) -> score (0-1).
    scale : float
        Multiply scores by this factor for B-factor column.
    
    Returns
    -------
    str
        Path to the output CIF.
    """
    doc = gemmi.cif.read(input_cif)
    block = doc.sole_block()
    
    b_col = block.find_loop('_atom_site.B_iso_or_equiv')
    chain_col = block.find_loop('_atom_site.auth_asym_id')
    resnum_col = block.find_loop('_atom_site.auth_seq_id')
    
    modified = 0
    for i in range(len(b_col)):
        key = (chain_col[i], resnum_col[i])
        if key in score_lookup:
            b_col[i] = f"{score_lookup[key] * scale:.2f}"
            modified += 1
    
    os.makedirs(os.path.dirname(output_cif) or '.', exist_ok=True)
    doc.write_file(output_cif)
    return output_cif


def cif_to_data_url(cif_path: str) -> str:
    """Convert a CIF file to a base64 data URL for embedding in HTML."""
    with open(cif_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:text/plain;base64,{b64}"
