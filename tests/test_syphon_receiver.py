"""Tests for the Syphon receiver module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from push2_bridge.syphon_receiver import SyphonReceiver


@pytest.fixture
def mock_directory():
    """Create a mock SyphonServerDirectory."""
    with patch("push2_bridge.syphon_receiver.SyphonServerDirectory") as MockDir:
        directory = MockDir.return_value
        directory.run_loop_interval = 1.0
        directory.servers = []
        directory.servers_matching_name.return_value = []
        directory.update_run_loop = MagicMock()
        yield directory


@pytest.fixture
def fake_server():
    """Create a fake SyphonServerDescription."""
    server = MagicMock()
    server.name = "Main Output"
    server.app_name = "VDMX5"
    server.uuid = "test-uuid"
    server.raw = {}
    return server


class TestSyphonReceiverDiscovery:
    def test_connects_to_first_available_server(self, mock_directory, fake_server):
        mock_directory.servers = [fake_server]

        with patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient:
            client = MockClient.return_value
            client.is_valid = True

            receiver = SyphonReceiver()
            assert receiver.start() is True
            assert receiver.is_connected is True

    def test_matches_by_app_name(self, mock_directory, fake_server):
        mock_directory.servers_matching_name.return_value = [fake_server]

        with patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient:
            client = MockClient.return_value
            client.is_valid = True

            receiver = SyphonReceiver(app_name="VDMX5")
            assert receiver.start() is True
            mock_directory.servers_matching_name.assert_called_with(app_name="VDMX5")

    def test_matches_by_server_name(self, mock_directory, fake_server):
        mock_directory.servers_matching_name.return_value = [fake_server]

        with patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient:
            client = MockClient.return_value
            client.is_valid = True

            receiver = SyphonReceiver(server_name="Main Output")
            assert receiver.start() is True
            mock_directory.servers_matching_name.assert_called_with(name="Main Output")

    def test_returns_false_when_no_servers(self, mock_directory):
        receiver = SyphonReceiver()
        assert receiver.start() is False
        assert receiver.is_connected is False

    def test_returns_false_on_client_error(self, mock_directory, fake_server):
        mock_directory.servers = [fake_server]

        with patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient:
            MockClient.side_effect = RuntimeError("Metal not available")

            receiver = SyphonReceiver()
            assert receiver.start() is False


class TestSyphonReceiverFrames:
    def test_get_frame_returns_numpy_array(self, mock_directory, fake_server):
        mock_directory.servers = [fake_server]
        fake_texture = MagicMock()
        fake_image = np.zeros((480, 640, 4), dtype=np.uint8)

        with (
            patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient,
            patch("push2_bridge.syphon_receiver.copy_mtl_texture_to_image") as mock_copy,
        ):
            client = MockClient.return_value
            client.is_valid = True
            client.has_new_frame = True
            client.new_frame_image = fake_texture
            mock_copy.return_value = fake_image

            receiver = SyphonReceiver()
            receiver.start()
            frame = receiver.get_frame()

            assert frame is not None
            assert frame.shape == (480, 640, 4)
            assert frame.dtype == np.uint8

    def test_get_frame_returns_none_when_no_new_frame(self, mock_directory, fake_server):
        mock_directory.servers = [fake_server]

        with patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient:
            client = MockClient.return_value
            client.is_valid = True
            client.has_new_frame = False

            receiver = SyphonReceiver()
            receiver.start()
            assert receiver.get_frame() is None

    def test_get_frame_returns_none_when_disconnected(self, mock_directory):
        receiver = SyphonReceiver()
        receiver.start()
        assert receiver.get_frame() is None

    def test_stop_cleans_up(self, mock_directory, fake_server):
        mock_directory.servers = [fake_server]

        with patch("push2_bridge.syphon_receiver.SyphonMetalClient") as MockClient:
            client = MockClient.return_value
            client.is_valid = True

            receiver = SyphonReceiver()
            receiver.start()
            receiver.stop()

            client.stop.assert_called_once()
            assert receiver.is_connected is False
