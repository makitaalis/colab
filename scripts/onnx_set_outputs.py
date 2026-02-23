#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import onnx
from onnx import TensorProto, helper, shape_inference


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite ONNX graph outputs to selected internal tensors.")
    parser.add_argument("--in", dest="in_path", required=True, help="Input .onnx path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output .onnx path")
    parser.add_argument(
        "--outputs",
        required=True,
        help="Comma-separated tensor names to set as graph outputs (must exist in graph).",
    )
    parser.add_argument(
        "--dtype",
        default="float32",
        choices=["float16", "float32"],
        help="Fallback dtype for outputs if not inferable (default: float32).",
    )
    args = parser.parse_args()

    in_path = Path(args.in_path).expanduser().resolve()
    out_path = Path(args.out_path).expanduser().resolve()
    outputs = [o.strip() for o in args.outputs.split(",") if o.strip()]
    if not outputs:
        raise SystemExit("--outputs must not be empty")

    model = onnx.load(str(in_path))

    # Run shape inference so we can attach shapes to outputs.
    inferred = shape_inference.infer_shapes(model)
    vi_map = {vi.name: vi for vi in list(inferred.graph.value_info) + list(inferred.graph.input) + list(inferred.graph.output)}

    fallback_dtype = TensorProto.FLOAT16 if args.dtype == "float16" else TensorProto.FLOAT

    new_outputs = []
    for name in outputs:
        if name in vi_map:
            # Keep inferred type/shape if available
            new_outputs.append(vi_map[name])
            continue

        # Fallback: create output with unknown shape
        new_outputs.append(helper.make_tensor_value_info(name, fallback_dtype, None))

    del model.graph.output[:]
    model.graph.output.extend(new_outputs)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(out_path))
    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

