"""Syphon client: receives GPU-shared frames from VDMX."""

import logging
from typing import Optional

import numpy as np
from syphon import SyphonServerDirectory, SyphonMetalClient
from syphon.server_directory import SyphonServerDescription
from syphon.utils.numpy import copy_mtl_texture_to_image

logger = logging.getLogger(__name__)

DEFAULT_SERVER_NAME = "Push2"


class SyphonReceiver:
    """Discovers a Syphon server and receives BGRA frames from it."""

    def __init__(self, app_name: Optional[str] = None, server_name: Optional[str] = None):
        """Create a receiver that will look for a specific Syphon server.

        Args:
            app_name: match server by application name (e.g. "VDMX6").
            server_name: match server by its published name.
                         Defaults to "Push2" if neither filter is specified.
        """
        if app_name is None and server_name is None:
            server_name = DEFAULT_SERVER_NAME
        self._app_name = app_name
        self._server_name = server_name
        self._directory: Optional[SyphonServerDirectory] = None
        self._client: Optional[SyphonMetalClient] = None
        self._server_desc: Optional[SyphonServerDescription] = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_valid

    @property
    def server_description(self) -> Optional[SyphonServerDescription]:
        return self._server_desc

    def start(self) -> bool:
        """Initialize the server directory and attempt to connect.

        Returns True if a server was found and connected.
        """
        self._directory = SyphonServerDirectory()
        # Use a very short run-loop interval so we don't block the frame loop.
        self._directory.run_loop_interval = 0.001
        return self._try_connect()

    def stop(self):
        """Disconnect from the Syphon server."""
        if self._client is not None:
            try:
                self._client.stop()
            except Exception:
                logger.exception("Error stopping Syphon client")
            finally:
                self._client = None
                self._server_desc = None
        logger.info("Syphon receiver stopped")

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from the Syphon server.

        Returns:
            (H, W, 4) uint8 BGRA numpy array, or None if no new frame.
        """
        if self._directory is not None:
            # Pump the run loop so we receive frame notifications.
            self._directory.update_run_loop()

        # If disconnected, try to reconnect.
        if not self.is_connected:
            if not self._try_connect():
                return None

        if not self._client.has_new_frame:
            return None

        texture = self._client.new_frame_image
        if texture is None:
            return None

        return copy_mtl_texture_to_image(texture)

    def _try_connect(self) -> bool:
        """Find a matching server and connect to it."""
        if self._directory is None:
            return False

        server = self._find_server()
        if server is None:
            return False

        try:
            self._client = SyphonMetalClient(server)
            self._server_desc = server
            logger.info(
                "Connected to Syphon server: %s (%s)", server.name, server.app_name
            )
            return True
        except Exception:
            logger.exception("Failed to connect to Syphon server")
            self._client = None
            self._server_desc = None
            return False

    def _find_server(self) -> Optional[SyphonServerDescription]:
        """Find a Syphon server matching our criteria."""
        if self._server_name is not None:
            matches = self._directory.servers_matching_name(name=self._server_name)
            if matches:
                return matches[0]

        if self._app_name is not None:
            matches = self._directory.servers_matching_name(app_name=self._app_name)
            if matches:
                return matches[0]

        # No filter specified — take the first available server.
        servers = self._directory.servers
        if servers:
            logger.info(
                "Available Syphon servers: %s",
                [(s.name, s.app_name) for s in servers],
            )
            return servers[0]

        return None
