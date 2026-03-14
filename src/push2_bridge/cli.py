"""CLI entry point for the Push 2 Display Bridge."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

import cv2

from push2_bridge import __version__
from push2_bridge.bridge import Bridge


def parse_color(value: str) -> tuple[int, int, int]:
    """Parse a color string like '255,0,128' into an (R, G, B) tuple."""
    try:
        parts = [int(x.strip()) for x in value.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid color: {value!r} — expected R,G,B (e.g. 255,0,128)")
    if len(parts) != 3 or not all(0 <= c <= 255 for c in parts):
        raise argparse.ArgumentTypeError(f"Invalid color: {value!r} — expected 3 values 0–255")
    return (parts[0], parts[1], parts[2])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="push2-bridge",
        description="VDMX → Syphon → Push 2 display bridge",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--fps", type=int, default=30,
        help="Target frame rate (default: 30)",
    )
    parser.add_argument(
        "--syphon-server", type=str, default=None,
        help="Syphon server name to connect to (default: Push2)",
    )
    parser.add_argument(
        "--fallback-color", type=parse_color, default=(0, 0, 0),
        metavar="R,G,B",
        help="Fallback color when no frame is available (default: 0,0,0)",
    )
    parser.add_argument(
        "--interpolation", type=str, default="linear",
        choices=["linear", "nearest"],
        help="Resize interpolation method (default: linear)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )
    return parser

INTERPOLATION_MAP = {
    "linear": cv2.INTER_LINEAR,
    "nearest": cv2.INTER_NEAREST,
}


def main(argv: Optional[list[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )

    logger = logging.getLogger(__name__)
    logger.info("push2-bridge %s", __version__)
    logger.info("Target FPS: %d | Syphon server: %s", args.fps, args.syphon_server or "Push2")

    interpolation = INTERPOLATION_MAP[args.interpolation]

    bridge = Bridge(
        target_fps=args.fps,
        syphon_server_name=args.syphon_server,
        fallback_color=args.fallback_color,
        interpolation=interpolation,
    )

    try:
        bridge.run()
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
