#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tarfile
import tempfile
from pathlib import Path


def _parse_csv_list(value: str) -> list[str]:
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Patch Luxonis NNArchive (.tar.xz) config.json to include a YOLO head parser section."
    )
    parser.add_argument("--archive", required=True, help="Input NNArchive path (*.tar.xz)")
    parser.add_argument(
        "--out",
        default="",
        help="Output NNArchive path. If omitted, patches in-place and creates a .bak next to it.",
    )
    parser.add_argument("--classes", default="head", help="Comma-separated class names (default: head)")
    parser.add_argument(
        "--subtype",
        default="yolov8",
        help="YOLO parser subtype, e.g. yolov6r2, yolov8 (default: yolov8)",
    )
    parser.add_argument("--conf-th", type=float, default=0.4, help="YOLO conf threshold (default: 0.4)")
    parser.add_argument("--iou-th", type=float, default=0.5, help="YOLO IoU threshold (default: 0.5)")
    parser.add_argument("--max-det", type=int, default=300, help="YOLO max detections (default: 300)")
    parser.add_argument(
        "--yolo-outputs",
        default="",
        help="Comma-separated model output tensor names to parse as YOLO outputs. "
        "If omitted, uses all outputs from config.json.",
    )

    args = parser.parse_args()
    archive_path = Path(args.archive).expanduser().resolve()
    if not archive_path.exists():
        raise SystemExit(f"Archive not found: {archive_path}")

    out_path = Path(args.out).expanduser().resolve() if args.out else archive_path
    classes = _parse_csv_list(args.classes)
    if not classes:
        raise SystemExit("--classes must not be empty")

    with tempfile.TemporaryDirectory(prefix="nnarchive_patch_") as td:
        tmp_dir = Path(td)
        with tarfile.open(archive_path, mode="r:xz") as tf:
            tf.extractall(tmp_dir)

        config_path = tmp_dir / "config.json"
        if not config_path.exists():
            raise SystemExit("config.json not found inside archive")

        cfg = _load_json(config_path)
        model = cfg.get("model") if isinstance(cfg, dict) else None
        if not isinstance(model, dict):
            raise SystemExit("Invalid config.json: missing 'model' object")

        outputs = model.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            raise SystemExit("Invalid config.json: missing model.outputs")

        output_names = [o.get("name") for o in outputs if isinstance(o, dict)]
        output_names = [n for n in output_names if isinstance(n, str) and n]
        if not output_names:
            raise SystemExit("Invalid config.json: outputs have no names")

        yolo_outputs = _parse_csv_list(args.yolo_outputs) if args.yolo_outputs else output_names
        missing = sorted(set(yolo_outputs) - set(output_names))
        if missing:
            raise SystemExit(f"--yolo-outputs contains unknown outputs: {missing}. Known: {output_names}")

        head = {
            "name": None,
            "parser": "YOLO",
            "metadata": {
                "postprocessor_path": None,
                "classes": classes,
                "n_classes": len(classes),
                "is_softmax": None,
                "iou_threshold": float(args.iou_th),
                "conf_threshold": float(args.conf_th),
                "max_det": int(args.max_det),
                "anchors": None,
                "yolo_outputs": yolo_outputs,
                "mask_outputs": None,
                "protos_outputs": None,
                "keypoints_outputs": None,
                "angles_outputs": None,
                "subtype": str(args.subtype),
                "n_prototypes": None,
                "n_keypoints": None,
            },
            "outputs": yolo_outputs,
        }

        model["heads"] = [head]
        _dump_json(config_path, cfg)

        # Write output archive
        if out_path == archive_path:
            bak = archive_path.with_suffix(archive_path.suffix + ".bak")
            if not bak.exists():
                archive_path.replace(bak)
            else:
                # If .bak already exists, keep it and overwrite archive directly.
                archive_path.unlink()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(out_path, mode="w:xz") as tf:
            for name in ["config.json", "buildinfo.json"]:
                p = tmp_dir / name
                if p.exists():
                    tf.add(p, arcname=name)
            # Add any blob/superblob files from root of archive
            for p in sorted(tmp_dir.glob("*.blob")) + sorted(tmp_dir.glob("*.superblob")):
                tf.add(p, arcname=p.name)

    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

