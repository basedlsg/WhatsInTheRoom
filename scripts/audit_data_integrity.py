"""Audit data integrity across all dataset versions.

Committee critique S5: 12,942 images but only 774 metadata entries in the
benchmark index — a discrepancy that must be documented and reconciled.

Usage:
    python scripts/audit_data_integrity.py
"""

import os
import json
import glob
from collections import Counter, defaultdict


DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "data")


def count_images(directory):
    """Count image files recursively."""
    exts = ("*.png", "*.jpg", "*.jpeg", "*.svg")
    total = 0
    by_ext = Counter()
    for ext in exts:
        matches = glob.glob(os.path.join(directory, "**", ext), recursive=True)
        total += len(matches)
        by_ext[ext.replace("*", "")] += len(matches)
    return total, dict(by_ext)


def count_metadata_json(directory):
    """Count JSON files that look like floorplan metadata (not index files)."""
    jsons = glob.glob(os.path.join(directory, "**", "*.json"), recursive=True)
    index_files = [f for f in jsons if "index" in os.path.basename(f).lower()]
    metadata_files = [f for f in jsons if "index" not in os.path.basename(f).lower()]
    return len(metadata_files), len(index_files)


def audit_benchmark(benchmark_dir):
    """Detailed audit of the primary benchmark directory."""
    print("\n=== BENCHMARK AUDIT ===")
    print(f"Directory: {benchmark_dir}\n")

    # 1. Count images
    img_dir = os.path.join(benchmark_dir, "images")
    if os.path.isdir(img_dir):
        img_count, img_by_ext = count_images(img_dir)
        print(f"Images: {img_count} {img_by_ext}")
    else:
        img_count = 0
        print("Images directory: NOT FOUND")

    # 2. Count floorplan JSONs
    fp_dir = os.path.join(benchmark_dir, "floorplans")
    if os.path.isdir(fp_dir):
        fp_jsons = glob.glob(os.path.join(fp_dir, "*.json"))
        print(f"Floorplan JSONs: {len(fp_jsons)}")
    else:
        fp_jsons = []
        print("Floorplans directory: NOT FOUND")

    # 3. Check index
    index_path = os.path.join(benchmark_dir, "dataset_index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
        if isinstance(index, list):
            print(f"Index entries: {len(index)}")
        elif isinstance(index, dict) and "samples" in index:
            print(f"Index entries: {len(index['samples'])}")
    else:
        print("Index: NOT FOUND")

    # 4. Cross-reference images ↔ metadata
    if fp_jsons and os.path.isdir(img_dir):
        fp_ids = {os.path.splitext(os.path.basename(f))[0] for f in fp_jsons}
        img_files = glob.glob(os.path.join(img_dir, "*.png"))
        img_ids = set()
        for img in img_files:
            base = os.path.splitext(os.path.basename(img))[0]
            # Strip rendering-style suffixes like _normal, _sketchy
            core_id = base.rsplit("_normal", 1)[0].rsplit("_sketchy", 1)[0]
            img_ids.add(core_id)

        orphan_images = img_ids - fp_ids
        orphan_metadata = fp_ids - img_ids

        print(f"\nCross-reference:")
        print(f"  Unique image base IDs: {len(img_ids)}")
        print(f"  Floorplan metadata IDs: {len(fp_ids)}")
        print(f"  Orphaned images (no metadata): {len(orphan_images)}")
        print(f"  Orphaned metadata (no image): {len(orphan_metadata)}")

        if orphan_images and len(orphan_images) <= 10:
            print(f"  Orphaned image IDs: {sorted(orphan_images)}")
        if orphan_metadata and len(orphan_metadata) <= 10:
            print(f"  Orphaned metadata IDs: {sorted(orphan_metadata)}")


def audit_all_directories():
    """Audit all data subdirectories."""
    print("=" * 60)
    print("FLOORPLANQA DATA INTEGRITY AUDIT")
    print("=" * 60)

    data_root = os.path.abspath(DATA_ROOT)
    if not os.path.isdir(data_root):
        print(f"ERROR: data root not found: {data_root}")
        return

    # Overview of all subdirectories
    subdirs = sorted([
        d for d in os.listdir(data_root)
        if os.path.isdir(os.path.join(data_root, d)) and not d.startswith(".")
    ])

    print(f"\nData root: {data_root}")
    print(f"Subdirectories: {len(subdirs)}\n")

    total_images = 0
    total_metadata = 0
    summary = []

    for subdir in subdirs:
        full_path = os.path.join(data_root, subdir)
        imgs, _ = count_images(full_path)
        metas, indices = count_metadata_json(full_path)
        total_images += imgs
        total_metadata += metas

        summary.append({
            "directory": subdir,
            "images": imgs,
            "metadata_json": metas,
            "index_files": indices,
        })

        print(f"  {subdir:30s}  images={imgs:5d}  metadata={metas:5d}  indices={indices}")

    print(f"\n{'TOTALS':30s}  images={total_images:5d}  metadata={total_metadata:5d}")
    print(f"\nDiscrepancy ratio: {total_images / max(total_metadata, 1):.1f}x")

    # Detailed benchmark audit
    benchmark_dir = os.path.join(data_root, "floorplan_qa_benchmark")
    if os.path.isdir(benchmark_dir):
        audit_benchmark(benchmark_dir)

    # Room type distribution from benchmark index
    index_path = os.path.join(data_root, "floorplan_qa_benchmark", "dataset_index.json")
    if os.path.exists(index_path):
        print("\n=== ROOM TYPE DISTRIBUTION (Benchmark Index) ===")
        with open(index_path) as f:
            index = json.load(f)
        if isinstance(index, list):
            types = Counter()
            for entry in index:
                gt = (
                    entry.get("ground_truth")
                    or entry.get("mystery_room_type")
                    or entry.get("room_type", "unknown")
                )
                types[gt] += 1
            total = sum(types.values())
            for t, c in types.most_common():
                print(f"  {t:20s}  {c:4d}  ({c/total*100:.1f}%)")
            print(f"\nMajority class: {types.most_common(1)[0][0]} "
                  f"at {types.most_common(1)[0][1]/total*100:.1f}%")


if __name__ == "__main__":
    audit_all_directories()
