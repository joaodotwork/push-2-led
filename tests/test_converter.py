"""Tests for the frame converter module."""

import numpy as np
import pytest

from push2_bridge.converter import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    bgra_to_bgr565,
    bgra_to_rgb_float,
    convert_frame,
    resize_frame,
)


class TestResize:
    def test_resize_from_larger(self):
        frame = np.zeros((480, 1920, 4), dtype=np.uint8)
        result = resize_frame(frame)
        assert result.shape == (DISPLAY_HEIGHT, DISPLAY_WIDTH, 4)

    def test_noop_when_already_correct_size(self):
        frame = np.ones((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
        result = resize_frame(frame)
        assert result is frame  # same object, no copy

    def test_preserves_dtype(self):
        frame = np.zeros((100, 200, 4), dtype=np.uint8)
        result = resize_frame(frame)
        assert result.dtype == np.uint8


class TestBgraToRgbFloat:
    def test_output_shape_and_dtype(self):
        frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 4), dtype=np.uint8)
        result = bgra_to_rgb_float(frame)
        assert result.shape == (DISPLAY_HEIGHT, DISPLAY_WIDTH, 3)
        assert result.dtype == np.float32

    def test_white_pixel(self):
        frame = np.full((1, 1, 4), 255, dtype=np.uint8)  # BGRA white
        result = bgra_to_rgb_float(frame)
        np.testing.assert_allclose(result[0, 0], [1.0, 1.0, 1.0])

    def test_pure_red_bgra(self):
        # BGRA: B=0, G=0, R=255, A=255
        frame = np.array([[[0, 0, 255, 255]]], dtype=np.uint8)
        result = bgra_to_rgb_float(frame)
        np.testing.assert_allclose(result[0, 0], [1.0, 0.0, 0.0])

    def test_rejects_wrong_channels(self):
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="BGRA"):
            bgra_to_rgb_float(frame)

    def test_rejects_wrong_dtype(self):
        frame = np.zeros((10, 10, 4), dtype=np.float32)
        with pytest.raises(ValueError, match="uint8"):
            bgra_to_rgb_float(frame)


class TestBgraToBgr565:
    def test_output_shape_and_dtype(self):
        frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 4), dtype=np.uint8)
        result = bgra_to_bgr565(frame)
        assert result.shape == (DISPLAY_HEIGHT, DISPLAY_WIDTH)
        assert result.dtype == np.uint16

    def test_black(self):
        frame = np.zeros((1, 1, 4), dtype=np.uint8)
        result = bgra_to_bgr565(frame)
        assert result[0, 0] == 0

    def test_white(self):
        frame = np.full((1, 1, 4), 255, dtype=np.uint8)
        result = bgra_to_bgr565(frame)
        # b=31, g=63, r=31 → (31 << 11) | (63 << 5) | 31 = 0xFFFF
        assert result[0, 0] == 0xFFFF

    def test_pure_red(self):
        # BGRA: B=0, G=0, R=255, A=255
        frame = np.array([[[0, 0, 255, 255]]], dtype=np.uint8)
        result = bgra_to_bgr565(frame)
        # r=31, g=0, b=0 → 31
        assert result[0, 0] == 31

    def test_pure_green(self):
        # BGRA: B=0, G=255, R=0, A=255
        frame = np.array([[[0, 255, 0, 255]]], dtype=np.uint8)
        result = bgra_to_bgr565(frame)
        # g=63 → 63 << 5 = 2016
        assert result[0, 0] == (63 << 5)

    def test_pure_blue(self):
        # BGRA: B=255, G=0, R=0, A=255
        frame = np.array([[[255, 0, 0, 255]]], dtype=np.uint8)
        result = bgra_to_bgr565(frame)
        # b=31 → 31 << 11 = 63488
        assert result[0, 0] == (31 << 11)

    def test_rejects_wrong_channels(self):
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="BGRA"):
            bgra_to_bgr565(frame)


class TestConvertFrame:
    def test_bgr565_path(self):
        frame = np.zeros((480, 1920, 4), dtype=np.uint8)
        result = convert_frame(frame, use_bgr565=True)
        assert result.shape == (DISPLAY_HEIGHT, DISPLAY_WIDTH)
        assert result.dtype == np.uint16

    def test_rgb_float_path(self):
        frame = np.zeros((480, 1920, 4), dtype=np.uint8)
        result = convert_frame(frame, use_bgr565=False)
        assert result.shape == (DISPLAY_HEIGHT, DISPLAY_WIDTH, 3)
        assert result.dtype == np.float32
