#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import onnx
from onnx import shape_inference


@dataclass(frozen=True)
class Candidate:
    name: str
    c: int
    h: int
    w: int


def _dims_from_vi(vi: onnx.ValueInfoProto) -> list[int] | None:
    tt = vi.type.tensor_type
    if not tt.HasField("shape"):
        return None
    dims: list[int] = []
    for d in tt.shape.dim:
        if d.HasField("dim_value"):
            dims.append(int(d.dim_value))
        else:
            return None
    return dims


def _iter_value_infos(model: onnx.ModelProto) -> list[onnx.ValueInfoProto]:
    g = model.graph
    return list(g.value_info) + list(g.input) + list(g.output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Heuristically find YOLOv8 raw multi-scale output tensors (DFL head) inside an Ultralytics-exported ONNX.\n"
            "Typical shapes: [1,C,H,W] where H,W are imgsz/8, imgsz/16, imgsz/32 and C is ~ (4*reg_max + n_classes).\n"
            "Outputs are printed as a comma-separated list ordered from largest scale to smallest."
        )
    )
    parser.add_argument("--model", required=True, help="Input ONNX path")
    parser.add_argument("--imgsz", type=int, default=416, help="Model input size (default: 416)")
    parser.add_argument(
        "--max-channels",
        type=int,
        default=200,
        help="Max channels to consider for YOLO head outputs (default: 200)",
    )
    parser.add_argument(
        "--prefer-substr",
        default="cat,concat",
        help="Comma-separated substrings to prefer when multiple candidates exist (default: cat,concat)",
    )
    parser.add_argument(
        "--print-candidates",
        action="store_true",
        help="Print all candidates before selecting (debug)",
    )
    args = parser.parse_args()

    model_path = Path(args.model).expanduser().resolve()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}")
    imgsz = int(args.imgsz)
    if imgsz <= 0 or imgsz % 32 != 0:
        raise SystemExit("--imgsz must be a positive multiple of 32 (e.g. 416, 640)")

    target_hw = [imgsz // 8, imgsz // 16, imgsz // 32]
    prefer = [s.strip().lower() for s in str(args.prefer_substr).split(",") if s.strip()]

    model = onnx.load(str(model_path))
    inferred = shape_inference.infer_shapes(model)

    candidates: list[Candidate] = []
    for vi in _iter_value_infos(inferred):
        dims = _dims_from_vi(vi)
        if not dims or len(dims) != 4:
            continue
        n, c, h, w = dims
        if n != 1:
            continue
        if h != w:
            continue
        if h not in target_hw:
            continue
        if c < 5 or c > int(args.max_channels):
            continue
        candidates.append(Candidate(name=str(vi.name), c=int(c), h=int(h), w=int(w)))

    if args.print_candidates:
        for cand in sorted(candidates, key=lambda x: (-x.h, x.c, x.name)):
            print(f"cand: name={cand.name} shape=[1,{cand.c},{cand.h},{cand.w}]")

    by_h: dict[int, list[Candidate]] = {h: [] for h in target_hw}
    for cand in candidates:
        by_h[cand.h].append(cand)

    selected: list[Candidate] = []
    for h in target_hw:
        opts = by_h.get(h) or []
        if not opts:
            continue
        opts = sorted(opts, key=lambda x: (x.c, x.name))
        preferred = []
        for s in prefer:
            preferred.extend([o for o in opts if s in o.name.lower()])
        pool = preferred or opts
        selected.append(pool[0])

    if len(selected) != 3:
        msg = [
            "Failed to locate 3 YOLO raw outputs.",
            f"imgsz={imgsz} expected HW={target_hw}",
            "Found candidates:",
        ]
        for cand in sorted(candidates, key=lambda x: (-x.h, x.c, x.name))[:50]:
            msg.append(f"  - {cand.name}: [1,{cand.c},{cand.h},{cand.w}]")
        raise SystemExit("\n".join(msg))

    selected_sorted = sorted(selected, key=lambda x: (-x.h, x.name))
    print(",".join([c.name for c in selected_sorted]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

