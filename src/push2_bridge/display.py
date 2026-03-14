"""Push 2 display driver: handles USB framing via push2-python."""

import logging

import numpy as np
import push2_python
from push2_python.constants import FRAME_FORMAT_BGR565

logger = logging.getLogger(__name__)

DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 160


class Push2Display:
    """Wrapper around push2-python for sending frames to the Push 2 LCD."""

    def __init__(self):
        self._push2 = None

    @property
    def is_connected(self) -> bool:
        return self._push2 is not None and self._push2.display_is_configured()

    def connect(self) -> bool:
        """Connect to the Push 2 display over USB.

        Returns True if connection succeeded, False otherwise.
        """
        try:
            self._push2 = push2_python.Push2()
            # Trigger display setup by checking configuration
            if self._push2.display_is_configured():
                logger.info("Connected to Push 2 display")
                return True
            else:
                logger.warning("Push 2 not found — display not configured")
                return False
        except Exception:
            logger.exception("Failed to connect to Push 2")
            self._push2 = None
            return False

    def disconnect(self):
        """Release the Push 2 connection."""
        if self._push2 is not None:
            try:
                self._push2.stop_active_sensing_thread()
            except Exception:
                logger.exception("Error during disconnect")
            finally:
                self._push2 = None
                logger.info("Disconnected from Push 2")

    def send_frame(self, frame: np.ndarray, fmt: str = FRAME_FORMAT_BGR565):
        """Send a frame to the Push 2 display.

        Args:
            frame: numpy array — shape depends on format:
                   BGR565/RGB565: (960, 160) uint16
                   RGB: (960, 160, 3) float32
            fmt: one of FRAME_FORMAT_BGR565, FRAME_FORMAT_RGB565, FRAME_FORMAT_RGB
        """
        if not self.is_connected:
            raise RuntimeError("Push 2 display not connected")
        self._push2.display.display_frame(frame, input_format=fmt)

    def send_test_frame(self, r: int = 0, g: int = 0, b: int = 255):
        """Send a solid-color test frame in BGR565 format.

        Args:
            r, g, b: color components (0–255)
        """
        r16 = np.uint16(r >> 3)
        g16 = np.uint16(g >> 2)
        b16 = np.uint16(b >> 3)
        pixel = (b16 << 11) | (g16 << 5) | r16
        frame = np.full((DISPLAY_HEIGHT, DISPLAY_WIDTH), pixel, dtype=np.uint16)
        self.send_frame(frame, fmt=FRAME_FORMAT_BGR565)
