#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time

import depthai as dai


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Headless OAK-D Lite smoke test for DepthAI v3.")
    parser.add_argument("--duration-sec", type=float, default=5.0, help="Capture duration in seconds (default: 5).")
    parser.add_argument("--min-frames", type=int, default=5, help="Minimum frames required to pass (default: 5).")
    parser.add_argument("--width", type=int, default=640, help="Output frame width (default: 640).")
    parser.add_argument("--height", type=int, default=400, help="Output frame height (default: 400).")
    parser.add_argument("--fps", type=float, default=15.0, help="Requested FPS (default: 15).")
    return parser.parse_args()


def run_smoke(duration_sec: float, min_frames: int, width: int, height: int, fps: float) -> int:
    print(f"depthai={dai.__version__}")
    with dai.Pipeline() as pipeline:
        camera = pipeline.create(dai.node.Camera).build()
        queue = camera.requestOutput(
            size=(width, height),
            type=dai.ImgFrame.Type.BGR888p,
            resizeMode=dai.ImgResizeMode.CROP,
            fps=fps,
        ).createOutputQueue()

        pipeline.start()
        start_ts = time.time()
        frame_count = 0
        while pipeline.isRunning() and (time.time() - start_ts) < duration_sec:
            packet = queue.tryGet()
            if packet is not None:
                _ = packet.getCvFrame()
                frame_count += 1
            time.sleep(0.01)

        device = pipeline.getDefaultDevice()
        print(f"device={device.getDeviceName()}")
        print(f"usb_speed={device.getUsbSpeed().name}")
        print(f"frames={frame_count}")

        if frame_count < min_frames:
            print(
                f"SMOKE_FAIL: frames={frame_count} < min_frames={min_frames}",
                file=sys.stderr,
            )
            return 1

    print("SMOKE_OK")
    return 0


def main() -> int:
    args = parse_args()
    return run_smoke(
        duration_sec=args.duration_sec,
        min_frames=args.min_frames,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )


if __name__ == "__main__":
    raise SystemExit(main())
