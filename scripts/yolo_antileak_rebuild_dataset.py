#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


IMG_EXTS = {".jpg", ".jpeg", ".png"}
ID_PREFIX_RE = re.compile(r"^(\d+)_")


@dataclass(frozen=True)
class GroupInfo:
    group_id: str
    images: int


def group_id_from_filename(name: str) -> str:
    m = ID_PREFIX_RE.match(name)
    if m:
        return m.group(1)
    # fallback: stem without roboflow hash tail if present
    stem = Path(name).stem
    # roboflow names often: <orig>.rf.<hash>
    if ".rf." in stem:
        stem = stem.split(".rf.", 1)[0]
    return stem


def iter_images(root: Path) -> Iterable[Path]:
    for p in root.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            yield p


def ensure_pair(img: Path, lab: Path) -> None:
    if not img.exists():
        raise FileNotFoundError(img)
    if not lab.exists():
        raise FileNotFoundError(lab)


def link_or_copy(src: Path, dst: Path, mode: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    if mode == "hardlink":
        os.link(src, dst)
    elif mode == "symlink":
        os.symlink(src, dst)
    elif mode == "copy":
        shutil.copy2(src, dst)
    else:
        raise ValueError(f"unknown mode: {mode}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild YOLO dataset splits to avoid leakage across splits (group-aware).")
    ap.add_argument("--src", required=True, help="Source dataset root (contains train/valid/test with images+labels).")
    ap.add_argument("--dst", required=True, help="Destination dataset root to create.")
    ap.add_argument("--seed", type=int, default=0, help="Shuffle seed for group assignment.")
    ap.add_argument(
        "--mode",
        default="hardlink",
        choices=["hardlink", "symlink", "copy"],
        help="How to place files into dst (default: hardlink).",
    )
    ap.add_argument("--names", default="head", help="Class names CSV (single class recommended). Default: head")
    ap.add_argument("--report", required=True, help="Write JSON report to this path.")
    args = ap.parse_args()

    src = Path(args.src).expanduser().resolve()
    dst = Path(args.dst).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    issues: list[str] = []
    if not src.exists():
        issues.append(f"src not found: {src}")
    for split in ["train", "valid", "test"]:
        if not (src / split / "images").is_dir():
            issues.append(f"missing dir: {src/split/'images'}")
        if not (src / split / "labels").is_dir():
            issues.append(f"missing dir: {src/split/'labels'}")
    if issues:
        report_path.write_text(json.dumps({"ok": False, "issues": issues}, indent=2) + "\n", encoding="utf-8")
        print("\n".join(issues), file=sys.stderr)
        return 2

    # Collect all pairs from all splits
    pairs: list[tuple[Path, Path]] = []
    for split in ["train", "valid", "test"]:
        img_dir = src / split / "images"
        lab_dir = src / split / "labels"
        for img in iter_images(img_dir):
            lab = lab_dir / f"{img.stem}.txt"
            ensure_pair(img, lab)
            pairs.append((img, lab))

    # Group by group_id
    group_to_pairs: dict[str, list[tuple[Path, Path]]] = {}
    for img, lab in pairs:
        gid = group_id_from_filename(img.name)
        group_to_pairs.setdefault(gid, []).append((img, lab))

    groups = [GroupInfo(group_id=k, images=len(v)) for k, v in group_to_pairs.items()]
    groups_sorted = sorted(groups, key=lambda g: (-g.images, g.group_id))

    # Target sizes by image count: keep original proportions
    src_counts = {}
    total = 0
    for split in ["train", "valid", "test"]:
        n = len(list(iter_images(src / split / "images")))
        src_counts[split] = n
        total += n
    if total <= 0:
        issues.append("no images found in src")
        report_path.write_text(json.dumps({"ok": False, "issues": issues}, indent=2) + "\n", encoding="utf-8")
        return 2

    target = {
        "train": src_counts["train"],
        "valid": src_counts["valid"],
        "test": src_counts["test"],
    }

    # Shuffle groups deterministically, then greedy pack to targets
    rnd = random.Random(int(args.seed))
    gids = [g.group_id for g in groups_sorted]
    rnd.shuffle(gids)

    assignment: dict[str, str] = {}
    split_images = {"train": 0, "valid": 0, "test": 0}
    split_groups = {"train": 0, "valid": 0, "test": 0}

    def place(gid: str, split: str) -> None:
        assignment[gid] = split
        split_groups[split] += 1
        split_images[split] += len(group_to_pairs[gid])

    # train first, then valid, rest to test
    for gid in gids:
        if split_images["train"] < target["train"]:
            place(gid, "train")
        elif split_images["valid"] < target["valid"]:
            place(gid, "valid")
        else:
            place(gid, "test")

    # Build dst
    if dst.exists():
        shutil.rmtree(dst)
    for split in ["train", "valid", "test"]:
        (dst / split / "images").mkdir(parents=True, exist_ok=True)
        (dst / split / "labels").mkdir(parents=True, exist_ok=True)

    for gid, split in assignment.items():
        for img, lab in group_to_pairs[gid]:
            out_img = dst / split / "images" / img.name
            out_lab = dst / split / "labels" / lab.name
            link_or_copy(img, out_img, args.mode)
            link_or_copy(lab, out_lab, args.mode)

    # Write dst data.yaml
    class_names = [x.strip() for x in str(args.names).split(",") if x.strip()]
    data_yaml = dst / "data.yaml"
    yaml_lines = [
        f"path: {dst}",
        "train: train/images",
        "val: valid/images",
        "test: test/images",
        "",
        "names:",
    ]
    for i, n in enumerate(class_names):
        yaml_lines.append(f"  {i}: {n}")
    data_yaml.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    # Leakage check: ensure no group_id overlaps across splits now
    def split_gids(split: str) -> set[str]:
        out = set()
        for img in iter_images(dst / split / "images"):
            out.add(group_id_from_filename(img.name))
        return out

    g_train = split_gids("train")
    g_valid = split_gids("valid")
    g_test = split_gids("test")
    overlaps = {
        "train_valid": sorted(list(g_train & g_valid)),
        "train_test": sorted(list(g_train & g_test)),
        "valid_test": sorted(list(g_valid & g_test)),
    }

    payload = {
        "ok": True,
        "src": str(src),
        "dst": str(dst),
        "mode": args.mode,
        "seed": int(args.seed),
        "src_counts": src_counts,
        "dst_counts": {s: len(list(iter_images(dst / s / "images"))) for s in ["train", "valid", "test"]},
        "groups_total": len(group_to_pairs),
        "groups_by_split": split_groups,
        "images_by_split": split_images,
        "overlaps_group_ids": {k: v[:20] for k, v in overlaps.items()},
        "overlaps_group_ids_total": {k: len(v) for k, v in overlaps.items()},
        "data_yaml": str(data_yaml),
    }

    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

