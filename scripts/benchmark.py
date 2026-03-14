#!/usr/bin/env python3
"""Benchmark frame conversion pipeline stages.

Compares INTER_LINEAR vs INTER_NEAREST across multiple input resolutions.
No hardware required — uses synthetic BGRA frames.

Usage:
    python scripts/benchmark.py
"""

import statistics
import time

import cv2
import numpy as np

from push2_bridge.converter import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    bgra_to_bgr565,
    convert_frame,
    resize_frame,
)

ITERATIONS = 100
RESOLUTIONS = [
    (160, 960, "960x160 (native)"),
    (480, 640, "640x480"),
    (720, 1280, "1280x720"),
    (1080, 1920, "1920x1080"),
]
INTERPOLATIONS = [
    ("LINEAR", cv2.INTER_LINEAR),
    ("NEAREST", cv2.INTER_NEAREST),
]


def make_frame(height: int, width: int) -> np.ndarray:
    """Create a synthetic BGRA frame with some variation."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (height, width, 4), dtype=np.uint8)


def bench(fn, iterations: int = ITERATIONS) -> dict:
    """Time a function over multiple iterations, return stats in ms."""
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "mean": statistics.mean(times),
        "stddev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "p99": sorted(times)[int(len(times) * 0.99)],
    }


def print_row(label: str, stats: dict):
    print(f"  {label:<35} {stats['mean']:7.2f} ms  ±{stats['stddev']:6.2f}  p99={stats['p99']:7.2f} ms")


def main():
    print(f"Push 2 Display Bridge — Pipeline Benchmark ({ITERATIONS} iterations)\n")
    print("=" * 80)

    for height, width, res_label in RESOLUTIONS:
        frame = make_frame(height, width)
        print(f"\nInput resolution: {res_label} ({width}x{height})")
        print("-" * 80)

        # Stage 1: Vertical flip
        stats = bench(lambda f=frame: f[::-1])
        print_row("flip", stats)

        flipped = frame[::-1]

        # Stage 2: Resize (compare interpolation methods)
        for interp_name, interp_flag in INTERPOLATIONS:
            stats = bench(lambda f=flipped, flag=interp_flag: resize_frame(f, interpolation=flag))
            print_row(f"resize ({interp_name})", stats)

        # Stage 3: BGR565 conversion
        resized = resize_frame(flipped)
        stats = bench(lambda f=resized: bgra_to_bgr565(f))
        print_row("bgr565", stats)

        # Stage 4: Full pipeline (compare interpolation methods)
        for interp_name, interp_flag in INTERPOLATIONS:
            stats = bench(lambda f=frame, flag=interp_flag: convert_frame(f, use_bgr565=True, interpolation=flag))
            print_row(f"full convert ({interp_name})", stats)

    print("\n" + "=" * 80)
    print("Done.")


if __name__ == "__main__":
    main()
