"""Frame conversion: resize to 960x160, color space transforms (BGRA → RGB/BGR565)."""

import cv2
import numpy as np

DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 160


def resize_frame(
    frame: np.ndarray,
    width: int = DISPLAY_WIDTH,
    height: int = DISPLAY_HEIGHT,
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    """Resize a frame to the target dimensions.

    Args:
        frame: input image as numpy array (any shape accepted by cv2.resize)
        width: target width (default 960)
        height: target height (default 160)
        interpolation: OpenCV interpolation flag (default INTER_LINEAR)

    Returns:
        Resized numpy array with same dtype and channel count.
    """
    if frame.shape[1] == width and frame.shape[0] == height:
        return frame
    return cv2.resize(frame, (width, height), interpolation=interpolation)


def bgra_to_rgb_float(frame: np.ndarray) -> np.ndarray:
    """Convert a BGRA uint8 frame to RGB float32 [0.0–1.0].

    Args:
        frame: (H, W, 4) uint8 BGRA image

    Returns:
        (H, W, 3) float32 RGB image normalized to [0.0, 1.0]
    """
    _validate_bgra(frame)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
    return rgb.astype(np.float32) / 255.0


def bgra_to_bgr565(frame: np.ndarray) -> np.ndarray:
    """Convert a BGRA uint8 frame to BGR565 uint16 (Push 2 native format).

    Bit layout per pixel: [b4 b3 b2 b1 b0 g5 g4 g3 g2 g1 g0 r4 r3 r2 r1 r0]

    Args:
        frame: (H, W, 4) uint8 BGRA image

    Returns:
        (H, W) uint16 BGR565 image
    """
    _validate_bgra(frame)
    b = (frame[:, :, 0].astype(np.uint16)) >> 3
    g = (frame[:, :, 1].astype(np.uint16)) >> 2
    r = (frame[:, :, 2].astype(np.uint16)) >> 3
    return (b << 11) | (g << 5) | r


def convert_frame(
    frame: np.ndarray,
    use_bgr565: bool = True,
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    """Resize and convert a BGRA frame for the Push 2 display.

    Args:
        frame: (H, W, 4) uint8 BGRA image (e.g. from Syphon)
        use_bgr565: if True, output BGR565 uint16; otherwise RGB float32
        interpolation: OpenCV interpolation flag (default INTER_LINEAR)

    Returns:
        Resized and converted frame ready for Push2Display.send_frame()
    """
    # Metal textures have origin at bottom-left — flip vertically.
    # The display wrapper transposes for push2-python's (W,H) layout,
    # which also mirrors X, so only a vertical flip is needed here.
    frame = frame[::-1]
    resized = resize_frame(frame, interpolation=interpolation)
    if use_bgr565:
        return bgra_to_bgr565(resized)
    return bgra_to_rgb_float(resized)


def _validate_bgra(frame: np.ndarray):
    """Validate that a frame is BGRA uint8."""
    if frame.ndim != 3 or frame.shape[2] != 4:
        raise ValueError(f"Expected BGRA frame with shape (H, W, 4), got {frame.shape}")
    if frame.dtype != np.uint8:
        raise ValueError(f"Expected uint8 dtype, got {frame.dtype}")
