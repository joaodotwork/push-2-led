"""Tests for the bridge module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from push2_bridge.bridge import Bridge


@pytest.fixture
def mock_deps():
    """Mock SyphonReceiver and Push2Display so the bridge can be tested in isolation."""
    with (
        patch("push2_bridge.bridge.SyphonReceiver") as MockReceiver,
        patch("push2_bridge.bridge.Push2Display") as MockDisplay,
    ):
        receiver = MockReceiver.return_value
        receiver.is_connected = False
        receiver.server_description = None
        receiver.start.return_value = False
        receiver.get_frame.return_value = None

        display = MockDisplay.return_value
        display.is_connected = True
        display.connect.return_value = True

        yield {"receiver": receiver, "display": display}


class TestBridgeTick:
    def test_sends_live_frame(self, mock_deps):
        raw = np.zeros((480, 640, 4), dtype=np.uint8)
        mock_deps["receiver"].get_frame.return_value = raw

        bridge = Bridge()
        bridge._display = mock_deps["display"]
        bridge._receiver = mock_deps["receiver"]
        bridge._tick()

        mock_deps["display"].send_frame.assert_called_once()
        sent_frame = mock_deps["display"].send_frame.call_args[0][0]
        assert sent_frame.dtype == np.uint16  # BGR565
        assert sent_frame.shape == (160, 960)

    def test_sends_keepalive_when_no_new_frame(self, mock_deps):
        mock_deps["receiver"].get_frame.return_value = None

        bridge = Bridge()
        bridge._display = mock_deps["display"]
        bridge._receiver = mock_deps["receiver"]

        # Simulate having received a frame previously.
        prev_frame = np.ones((160, 960), dtype=np.uint16)
        bridge._last_frame = prev_frame
        bridge._tick()

        sent_frame = mock_deps["display"].send_frame.call_args[0][0]
        assert sent_frame is prev_frame

    def test_sends_fallback_when_never_received_frame(self, mock_deps):
        mock_deps["receiver"].get_frame.return_value = None

        bridge = Bridge(fallback_color=(0, 0, 0))
        bridge._display = mock_deps["display"]
        bridge._receiver = mock_deps["receiver"]
        bridge._tick()

        sent_frame = mock_deps["display"].send_frame.call_args[0][0]
        assert sent_frame.shape == (160, 960)
        assert sent_frame.dtype == np.uint16
        # Black in BGR565 is 0.
        assert np.all(sent_frame == 0)

    def test_fallback_with_custom_color(self, mock_deps):
        mock_deps["receiver"].get_frame.return_value = None

        bridge = Bridge(fallback_color=(255, 255, 255))
        bridge._display = mock_deps["display"]
        bridge._receiver = mock_deps["receiver"]
        bridge._tick()

        sent_frame = mock_deps["display"].send_frame.call_args[0][0]
        # White in BGR565 is 0xFFFF.
        assert np.all(sent_frame == 0xFFFF)


class TestBridgeStartupShutdown:
    def test_startup_fails_without_push2(self, mock_deps):
        mock_deps["display"].connect.return_value = False

        bridge = Bridge()
        with pytest.raises(RuntimeError, match="Push 2"):
            bridge.run()

    def test_stop_sets_running_false(self, mock_deps):
        bridge = Bridge()
        bridge._running = True
        bridge.stop()
        assert bridge._running is False


class TestBridgeFPS:
    def test_fps_returns_zero_with_no_data(self, mock_deps):
        bridge = Bridge()
        assert bridge.fps == 0.0

    def test_fps_calculation(self, mock_deps):
        bridge = Bridge()
        # Simulate 31 frames over 1 second.
        for i in range(31):
            bridge._fps_window.append(i / 30.0)
        assert abs(bridge.fps - 30.0) < 0.5
