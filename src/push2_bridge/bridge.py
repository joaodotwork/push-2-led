"""Main bridge loop: Syphon → convert → Push 2 display at target FPS."""

import logging
import signal
import time
from collections import deque
from typing import Optional

import numpy as np
from push2_python.constants import FRAME_FORMAT_BGR565

from push2_bridge.converter import convert_frame
from push2_bridge.display import Push2Display
from push2_bridge.syphon_receiver import SyphonReceiver

logger = logging.getLogger(__name__)

DEFAULT_FPS = 30


class Bridge:
    """Ties the Syphon receiver, frame converter, and Push 2 display together."""

    def __init__(
        self,
        target_fps: int = DEFAULT_FPS,
        syphon_app_name: Optional[str] = None,
        syphon_server_name: Optional[str] = None,
        fallback_color: tuple[int, int, int] = (0, 0, 0),
    ):
        self._target_fps = target_fps
        self._frame_interval = 1.0 / target_fps
        self._fallback_color = fallback_color

        self._receiver = SyphonReceiver(
            app_name=syphon_app_name, server_name=syphon_server_name
        )
        self._display = Push2Display()

        self._running = False
        self._last_frame: Optional[np.ndarray] = None
        self._fps_window: deque[float] = deque(maxlen=60)

    @property
    def fps(self) -> float:
        """Current frames per second (rolling average)."""
        if len(self._fps_window) < 2:
            return 0.0
        dt = self._fps_window[-1] - self._fps_window[0]
        if dt <= 0:
            return 0.0
        return (len(self._fps_window) - 1) / dt

    def run(self):
        """Start the bridge loop. Blocks until stop() is called or Ctrl+C."""
        # Install signal handler for clean shutdown.
        prev_handler = signal.signal(signal.SIGINT, self._signal_handler)

        try:
            self._startup()
            self._loop()
        finally:
            self._shutdown()
            signal.signal(signal.SIGINT, prev_handler)

    def stop(self):
        """Signal the bridge loop to stop."""
        self._running = False

    def _startup(self):
        """Connect to Push 2 and start Syphon discovery."""
        logger.info("Starting bridge (target %d fps)...", self._target_fps)

        if not self._display.connect():
            raise RuntimeError("Could not connect to Push 2 display")

        self._receiver.start()
        if self._receiver.is_connected:
            desc = self._receiver.server_description
            logger.info("Syphon ready: %s (%s)", desc.name, desc.app_name)
        else:
            logger.warning("No Syphon server found yet — will keep looking")

        self._running = True

    def _loop(self):
        """Main frame loop with rate limiting."""
        while self._running:
            t_start = time.monotonic()

            self._tick()

            # Frame-rate cap: sleep for the remainder of the interval.
            elapsed = time.monotonic() - t_start
            sleep_time = self._frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            self._fps_window.append(time.monotonic())

    def _tick(self):
        """Process one frame: receive → convert → send."""
        raw_frame = self._receiver.get_frame()

        if raw_frame is not None:
            # Live frame from Syphon.
            converted = convert_frame(raw_frame, use_bgr565=True)
            self._last_frame = converted
        elif self._last_frame is not None:
            # Keep-alive: resend the last good frame.
            converted = self._last_frame
        else:
            # No frame ever received — send fallback color.
            converted = self._make_fallback_frame()
            self._last_frame = converted

        try:
            self._display.send_frame(converted, fmt=FRAME_FORMAT_BGR565)
        except Exception:
            logger.exception("Failed to send frame to Push 2")

    def _make_fallback_frame(self) -> np.ndarray:
        """Create a solid-color BGR565 fallback frame."""
        r, g, b = self._fallback_color
        r16 = np.uint16(r >> 3)
        g16 = np.uint16(g >> 2)
        b16 = np.uint16(b >> 3)
        pixel = (np.uint16(b16) << 11) | (np.uint16(g16) << 5) | r16
        return np.full((160, 960), pixel, dtype=np.uint16)

    def _signal_handler(self, signum, frame):
        logger.info("Received signal %d — shutting down", signum)
        self._running = False

    def _shutdown(self):
        """Disconnect everything cleanly."""
        logger.info("Shutting down bridge (last fps: %.1f)...", self.fps)
        self._receiver.stop()
        self._display.disconnect()
        logger.info("Bridge stopped")
