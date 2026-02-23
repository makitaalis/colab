#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


IMG_EXTS = {".jpg", ".jpeg", ".png"}
ID_PREFIX_RE = re.compile(r"^(\d+)_")


@dataclass(frozen=True)
class SplitStats:
    images: int
    labels: int
    empty_labels: int
    boxes_total: int
    boxes_max_per_image: int


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        return p.returncode, p.stdout.strip()
    except Exception as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def iter_images(img_dir: Path) -> list[Path]:
    return sorted([p for p in img_dir.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS])


def iter_labels(lab_dir: Path) -> list[Path]:
    return sorted([p for p in lab_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt"])


def parse_label_file(path: Path) -> list[tuple[int, float, float, float, float]]:
    txt = path.read_text(encoding="utf-8", errors="replace").strip()
    if not txt:
        return []
    out: list[tuple[int, float, float, float, float]] = []
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            raise ValueError(f"bad label line (<5 cols): {line!r}")
        cls = int(float(parts[0]))
        x, y, w, h = map(float, parts[1:5])
        out.append((cls, x, y, w, h))
    return out


def split_ids(images: list[Path]) -> set[str]:
    out: set[str] = set()
    for p in images:
        m = ID_PREFIX_RE.match(p.name)
        if m:
            out.add(m.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Preflight checks for Ultralytics YOLO training (dataset + weights).")
    ap.add_argument("--dataset", required=True, help="Dataset root (contains train/valid/test).")
    ap.add_argument("--data-yaml", required=True, help="Ultralytics data.yaml to be used for training.")
    ap.add_argument("--base-weights", required=True, help="Base weights (.pt) to start from.")
    ap.add_argument("--out", required=True, help="Write preflight JSON to this path.")
    args = ap.parse_args()

    dataset = Path(args.dataset).expanduser().resolve()
    data_yaml = Path(args.data_yaml).expanduser().resolve()
    base_weights = Path(args.base_weights).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    issues: list[str] = []
    warnings: list[str] = []

    if not dataset.exists():
        issues.append(f"dataset root not found: {dataset}")
    if not data_yaml.exists():
        issues.append(f"data yaml not found: {data_yaml}")
    if not base_weights.exists():
        issues.append(f"base weights not found: {base_weights}")

    yaml_declared_path: Path | None = None
    yaml_splits: dict[str, str] = {}
    if data_yaml.exists():
        try:
            for raw in data_yaml.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key == "path" and val:
                    yaml_declared_path = Path(val).expanduser().resolve()
                if key in {"train", "val", "test"} and val:
                    yaml_splits[key] = val
        except Exception as exc:
            warnings.append(f"data yaml parse warning: {type(exc).__name__}: {exc}")

    if yaml_declared_path is not None and dataset.exists() and yaml_declared_path != dataset:
        warnings.append(f"data yaml path differs from --dataset: yaml.path={yaml_declared_path} dataset={dataset}")

    if yaml_declared_path is not None:
        for k, rel in yaml_splits.items():
            p = (yaml_declared_path / rel).resolve() if not os.path.isabs(rel) else Path(rel).expanduser().resolve()
            if not p.exists():
                issues.append(f"data yaml split path missing: {k} -> {p}")

    splits = ["train", "valid", "test"]
    split_stats: dict[str, SplitStats] = {}
    class_ids: set[int] = set()
    oob_coords = 0
    nonpositive_wh = 0

    if dataset.exists():
        for split in splits:
            img_dir = dataset / split / "images"
            lab_dir = dataset / split / "labels"
            if not img_dir.is_dir():
                issues.append(f"missing dir: {img_dir}")
                continue
            if not lab_dir.is_dir():
                issues.append(f"missing dir: {lab_dir}")
                continue

            images = iter_images(img_dir)
            labels = iter_labels(lab_dir)
            img_stems = {p.stem for p in images}
            lab_stems = {p.stem for p in labels}
            missing_labels = sorted(img_stems - lab_stems)
            missing_images = sorted(lab_stems - img_stems)
            if missing_labels:
                issues.append(f"{split}: images without labels: {len(missing_labels)} (sample={missing_labels[:3]})")
            if missing_images:
                issues.append(f"{split}: labels without images: {len(missing_images)} (sample={missing_images[:3]})")

            empty_labels = 0
            boxes_total = 0
            boxes_max = 0
            for lf in labels:
                boxes = parse_label_file(lf)
                if not boxes:
                    empty_labels += 1
                    continue
                boxes_total += len(boxes)
                boxes_max = max(boxes_max, len(boxes))
                for cls, x, y, w, h in boxes:
                    class_ids.add(cls)
                    if w <= 0 or h <= 0:
                        nonpositive_wh += 1
                    if not (-1e-3 <= x <= 1 + 1e-3 and -1e-3 <= y <= 1 + 1e-3 and -1e-3 <= w <= 1 + 1e-3 and -1e-3 <= h <= 1 + 1e-3):
                        oob_coords += 1

            split_stats[split] = SplitStats(
                images=len(images),
                labels=len(labels),
                empty_labels=empty_labels,
                boxes_total=boxes_total,
                boxes_max_per_image=boxes_max,
            )

        # Negatives heuristic: presence of empty label files (images without objects)
        try:
            train_stats = split_stats.get("train")
            if train_stats and train_stats.labels:
                frac_empty = train_stats.empty_labels / max(1, train_stats.labels)
                if train_stats.empty_labels == 0:
                    warnings.append(
                        "No negative/background images in train (empty_labels=0). "
                        "If production has many frames without heads, add negative images (empty .txt labels) "
                        "to reduce false positives."
                    )
                elif frac_empty < 0.01:
                    warnings.append(
                        f"Very few negative/background images in train (empty_labels={train_stats.empty_labels}, "
                        f"{frac_empty:.2%}). Consider adding more negatives to reduce false positives."
                    )
        except Exception as exc:
            warnings.append(f"negative/empty-labels check failed: {type(exc).__name__}: {exc}")

        # Leakage heuristic: overlap of numeric prefixes across splits
        try:
            ids_train = split_ids(iter_images(dataset / "train" / "images"))
            ids_val = split_ids(iter_images(dataset / "valid" / "images"))
            ids_test = split_ids(iter_images(dataset / "test" / "images"))
            ov_tv = len(ids_train & ids_val)
            ov_tt = len(ids_train & ids_test)
            ov_vt = len(ids_val & ids_test)
            if ov_tv or ov_tt or ov_vt:
                warnings.append(
                    "Potential split leakage: numeric id prefix overlaps across splits "
                    f"(train∩val={ov_tv}, train∩test={ov_tt}, val∩test={ov_vt}). "
                    "If these ids come from sequential video frames, rebuild splits by group/video to avoid inflated metrics."
                )
        except Exception as exc:
            warnings.append(f"split leakage check failed: {type(exc).__name__}: {exc}")

        if oob_coords:
            issues.append(f"label coords out-of-bounds: {oob_coords}")
        if nonpositive_wh:
            issues.append(f"label w/h <= 0: {nonpositive_wh}")

    # Environment
    rc, nvidia = run_cmd(["nvidia-smi", "-L"])
    gpu_info = nvidia if rc == 0 else ""
    rc, torch = run_cmd([sys.executable, "-c", "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.device_count())"])
    torch_info = torch
    rc, ultr = run_cmd([sys.executable, "-c", "import ultralytics; print(ultralytics.__version__)"])
    ultralytics_ver = ultr.strip() if rc == 0 else ""
    rc, numpy_info = run_cmd([sys.executable, "-c", "import numpy as np; print(np.__version__); print(int(hasattr(np,'trapz'))); print(int(hasattr(np,'trapezoid')))"])
    numpy_lines = (numpy_info or "").splitlines()
    numpy_ver = numpy_lines[0].strip() if numpy_lines else ""
    numpy_has_trapz = bool(int(numpy_lines[1].strip())) if len(numpy_lines) > 1 and numpy_lines[1].strip().isdigit() else None
    numpy_has_trapezoid = bool(int(numpy_lines[2].strip())) if len(numpy_lines) > 2 and numpy_lines[2].strip().isdigit() else None

    # Disk
    try:
        usage = shutil.disk_usage(str(dataset if dataset.exists() else Path.cwd()))
        disk = {"total_gb": round(usage.total / 1e9, 1), "free_gb": round(usage.free / 1e9, 1)}
    except Exception:
        disk = {}

    payload: dict[str, Any] = {
        "timestamp_utc": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True).strip(),
        "host": {"platform": platform.platform(), "python": sys.version.split()[0]},
        "gpu": gpu_info,
        "torch": torch_info,
        "ultralytics": ultralytics_ver,
        "numpy": {"version": numpy_ver, "has_trapz": numpy_has_trapz, "has_trapezoid": numpy_has_trapezoid},
        "paths": {
            "dataset": str(dataset),
            "data_yaml": str(data_yaml),
            "base_weights": str(base_weights),
        },
        "hashes": {
            "data_yaml_sha256": sha256_file(data_yaml) if data_yaml.exists() else "",
            "base_weights_sha256": sha256_file(base_weights) if base_weights.exists() else "",
        },
        "dataset": {
            "splits": {k: asdict(v) for k, v in split_stats.items()},
            "unique_class_ids": sorted(class_ids),
        },
        "warnings": warnings,
        "issues": issues,
        "ok": not issues,
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
