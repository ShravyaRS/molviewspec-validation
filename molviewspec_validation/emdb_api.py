"""EMDB REST API helpers.

Single responsibility: fetch the depositor-recommended contour level
that VA / IHMValidation already use, and cache it locally so repeated
test runs don't hammer the EBI API.

API contract (mirrors what IHMValidation/em.py does):
  GET https://www.ebi.ac.uk/emdb/api/entry/{EMD-XXXXX}
  -> data["map"]["contour_list"]["contour"]  is a list of dicts
  -> the dict where {"primary": True} carries {"level": <float>}
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)

EMDB_ENTRY_URL = "https://www.ebi.ac.uk/emdb/api/entry/{emdb_id}"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "cache" / "emdb"
REQUEST_TIMEOUT = 15


def _normalize_emdb_id(emdb_id: str) -> str:
    """Accept '2984', 'EMD-2984', 'emd-2984', 'EMD2984' -> 'EMD-2984'."""
    s = str(emdb_id).strip().upper().replace("EMD-", "").replace("EMD", "")
    return f"EMD-{s}"


def _cache_path(emdb_id: str, cache_dir: Optional[Path]) -> Path:
    cache_dir = Path(cache_dir or DEFAULT_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{_normalize_emdb_id(emdb_id)}.json"


def fetch_emdb_metadata(
    emdb_id: str,
    cache_dir: Optional[Path] = None,
    refresh: bool = False,
) -> Optional[dict]:
    """Fetch (or load from cache) the full EMDB entry JSON. Returns None on failure."""
    eid = _normalize_emdb_id(emdb_id)
    cpath = _cache_path(eid, cache_dir)

    if cpath.exists() and not refresh:
        try:
            with cpath.open() as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.warning("EMDB cache for %s is corrupt (%s); re-fetching", eid, e)

    url = EMDB_ENTRY_URL.format(emdb_id=eid)
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        log.warning("EMDB API fetch failed for %s: %s", eid, e)
        return None

    try:
        with cpath.open("w") as f:
            json.dump(data, f)
    except OSError as e:
        log.warning("Could not cache EMDB response for %s: %s", eid, e)

    return data


def get_recommended_contour_level(
    emdb_id: str,
    cache_dir: Optional[Path] = None,
    refresh: bool = False,
) -> Optional[float]:
    """Return the depositor-recommended contour level for an EMDB entry.

    Returns None if no primary contour level is set; the caller should
    then fall back to a relative isovalue (~1 sigma) per VA's documented
    behavior for entries without a recommended level.
    """
    data = fetch_emdb_metadata(emdb_id, cache_dir=cache_dir, refresh=refresh)
    if not data:
        return None

    try:
        contours = data["map"]["contour_list"]["contour"]
    except (KeyError, TypeError):
        log.info("No contour_list for %s", emdb_id)
        return None

    if not isinstance(contours, list):
        contours = [contours]

    # Prefer the one explicitly flagged primary
    for c in contours:
        if isinstance(c, dict) and c.get("primary") in (True, "true", "True", 1):
            try:
                return float(c["level"])
            except (KeyError, TypeError, ValueError):
                continue

    # Fallback: first contour with a usable level
    for c in contours:
        if isinstance(c, dict) and "level" in c:
            try:
                return float(c["level"])
            except (TypeError, ValueError):
                continue

    return None
