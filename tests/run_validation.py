#!/usr/bin/env python3
"""Reproducible validation script for molviewspec-validation.

Runs the full pipeline on all 28 benchmark entries and reports results.
Exit code 0 = all pass, 1 = failures detected.

Usage:
    python tests/run_validation.py [--va-data-dir PATH] [--output-dir PATH]
"""

import sys, os, csv, glob, time, json, argparse, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from molviewspec_validation import (
    generate_all_views, parse_va_residue_inclusion,
    create_scored_cif, cif_to_data_url, create_va_inclusion_scene,
)
from molviewspec_validation.scenes import _builder_to_html


def load_benchmark():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "benchmark_dataset.csv")
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def test_html_generation(entries, output_dir):
    print("\n[TEST 1] HTML Generation (map_model + qscore, 3 views each)")
    print(f"{chr(35):>2} {'PDB':>5} {'EMDB':<12} {'Res':>5} {'Files':>5} {'Status'}")
    print("-" * 45)
    results = []
    for i, e in enumerate(entries):
        try:
            outputs = generate_all_views(
                e["pdb_id"], e["emdb_id"],
                output_dir=os.path.join(output_dir, "html", e["pdb_id"]),
                scene_types=["map_model", "qscore"],
            )
            for fpath in outputs.values():
                assert os.path.exists(fpath) and os.path.getsize(fpath) > 500
            results.append({"entry": e["pdb_id"], "test": "html", "status": "PASS", "files": len(outputs)})
            print(f"{i+1:>2} {e['pdb_id']:>5} {e['emdb_id']:<12} {e['resolution']:>5} {len(outputs):>5} PASS")
        except Exception as ex:
            results.append({"entry": e["pdb_id"], "test": "html", "status": "FAIL", "error": str(ex)})
            print(f"{i+1:>2} {e['pdb_id']:>5} {e['emdb_id']:<12} {e['resolution']:>5}       FAIL: {ex}")
    return results


def test_va_pipeline(entries, va_data_dir, output_dir):
    print("\n[TEST 2] VA Data Pipeline (residue inclusion scoring)")
    print(f"{chr(35):>2} {'PDB':>5} {'EMDB':<12} {'Residues':>8} {'Views':>5} {'Status'}")
    print("-" * 50)
    results, tested = [], 0
    for e in entries:
        pid = e["pdb_id"].lower()
        ri = glob.glob(f"{va_data_dir}/{pid}/*residue_inclusion.json")
        cifs = glob.glob(f"{va_data_dir}/{pid}/*.cif")
        if not ri or not cifs:
            continue
        tested += 1
        try:
            scores = parse_va_residue_inclusion(ri[0])
            assert len(scores) > 0
            scored = os.path.join(output_dir, "va", f"{pid}_scored.cif")
            os.makedirs(os.path.dirname(scored), exist_ok=True)
            create_scored_cif(cifs[0], scored, scores)
            url = cif_to_data_url(scored)
            views = 0
            for v in ["x", "y", "z"]:
                b = create_va_inclusion_scene(url, e["emdb_id"], view=v)
                h = _builder_to_html(b, f"{pid} {v}")
                fp = os.path.join(output_dir, "va", f"{pid}_incl_{v}.html")
                with open(fp, "w") as f:
                    f.write(h)
                assert os.path.getsize(fp) > 500
                views += 1
            results.append({"entry": pid, "test": "va_data", "status": "PASS", "residues": len(scores), "views": views})
            print(f"{tested:>2} {pid:>5} {e['emdb_id']:<12} {len(scores):>8} {views:>5} PASS")
        except Exception as ex:
            results.append({"entry": pid, "test": "va_data", "status": "FAIL", "error": str(ex)})
            print(f"{tested:>2} {pid:>5} {e['emdb_id']:<12} {'':>8} {'':>5} FAIL: {ex}")
    return results


def test_edge_cases(output_dir):
    print("\n[TEST 3] Edge Cases")
    cases = [
        ("9NU5", "EMD-49797", "Small protein (532 residues)"),
        ("9HYU", "EMD-52518", "Large complex with ligands (4543 residues)"),
        ("9R5K", "EMD-53590", "Protein + nucleic acid (4.2 A)"),
        ("9XZK", "EMD-72359", "Low-variance density map"),
        ("9P9C", "EMD-71406", "Low resolution (4.01 A)"),
    ]
    results = []
    for pid, eid, desc in cases:
        try:
            out = generate_all_views(pid, eid, output_dir=os.path.join(output_dir, "edge", pid), scene_types=["map_model"])
            for fp in out.values():
                assert os.path.getsize(fp) > 500
            results.append({"entry": pid, "test": "edge", "status": "PASS", "description": desc})
            print(f"  {pid} {desc:<45} PASS")
        except Exception as ex:
            results.append({"entry": pid, "test": "edge", "status": "FAIL", "error": str(ex)})
            print(f"  {pid} {desc:<45} FAIL: {ex}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--va-data-dir", default="/root/projects/qscore_validation/test_data")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    output_dir = args.output_dir or tempfile.mkdtemp(prefix="mvs_val_")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("molviewspec-validation: Full Validation Suite")
    print("=" * 60)
    entries = load_benchmark()
    res = [float(e["resolution"]) for e in entries]
    print(f"Benchmark: {len(entries)} entries, {min(res):.2f}-{max(res):.2f} A")

    all_r = []
    t0 = time.time()
    all_r.extend(test_html_generation(entries, output_dir))
    all_r.extend(test_va_pipeline(entries, args.va_data_dir, output_dir))
    all_r.extend(test_edge_cases(output_dir))
    elapsed = time.time() - t0

    p = sum(1 for r in all_r if r["status"] == "PASS")
    f = sum(1 for r in all_r if r["status"] == "FAIL")
    print("\n" + "=" * 60)
    print(f"SUMMARY: {p} passed, {f} failed, {elapsed:.1f}s")
    print("=" * 60)
    if f > 0:
        for r in all_r:
            if r["status"] == "FAIL":
                print(f"  FAIL: {r['entry']}/{r['test']}: {r.get('error','')}")
        return 1
    print("ALL TESTS PASSED")
    with open(os.path.join(output_dir, "results.json"), "w") as fh:
        json.dump({"passed": p, "failed": f, "elapsed": elapsed, "results": all_r}, fh, indent=2)
    return 0

if __name__ == "__main__":
    sys.exit(main())
