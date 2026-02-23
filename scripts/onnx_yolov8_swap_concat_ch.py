#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import onnx
from onnx import helper, shape_inference


def _find_node_by_output(model: onnx.ModelProto, output_name: str) -> onnx.NodeProto | None:
    for node in model.graph.node:
        if output_name in node.output:
            return node
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="For YOLOv8-style DFL heads: swap Concat inputs for selected tensors (puts cls before reg)."
    )
    parser.add_argument("--in", dest="in_path", required=True, help="Input .onnx path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output .onnx path")
    parser.add_argument(
        "--tensors",
        default="cat_13,cat_14,cat_15",
        help="Comma-separated tensor names to swap (default: cat_13,cat_14,cat_15).",
    )
    parser.add_argument(
        "--suffix",
        default="_swapped",
        help="Suffix for new tensor outputs (default: _swapped).",
    )
    args = parser.parse_args()

    in_path = Path(args.in_path).expanduser().resolve()
    out_path = Path(args.out_path).expanduser().resolve()
    tensors = [t.strip() for t in args.tensors.split(",") if t.strip()]
    if not tensors:
        raise SystemExit("--tensors must not be empty")

    model = onnx.load(str(in_path))

    new_output_names: list[str] = []
    for t in tensors:
        node = _find_node_by_output(model, t)
        if node is None or node.op_type != "Concat":
            raise SystemExit(f"Tensor '{t}' is not produced by a Concat node (found: {node.op_type if node else None})")
        if len(node.input) != 2:
            raise SystemExit(f"Concat for '{t}' expected 2 inputs, got {len(node.input)}")

        axis = None
        for a in node.attribute:
            if a.name == "axis":
                axis = int(a.i)
        if axis is None:
            raise SystemExit(f"Concat for '{t}' has no axis attribute")
        if axis != 1:
            raise SystemExit(f"Concat for '{t}' axis expected 1 (channel), got {axis}")

        reg, cls = node.input[0], node.input[1]
        new_name = f"{t}{args.suffix}"
        new_node = helper.make_node(
            "Concat",
            inputs=[cls, reg],
            outputs=[new_name],
            axis=axis,
            name=f"swap_{t}",
        )
        model.graph.node.append(new_node)
        new_output_names.append(new_name)

    # Update outputs to the swapped tensors
    inferred = shape_inference.infer_shapes(model)
    vi_map = {vi.name: vi for vi in list(inferred.graph.value_info) + list(inferred.graph.input) + list(inferred.graph.output)}
    del model.graph.output[:]
    for name in new_output_names:
        if name in vi_map:
            model.graph.output.append(vi_map[name])
        else:
            # Should not happen, but keep model valid
            model.graph.output.append(helper.make_tensor_value_info(name, onnx.TensorProto.FLOAT, None))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(out_path))
    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

