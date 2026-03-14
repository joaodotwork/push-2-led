"""Tests for the CLI module."""

import argparse

import pytest

from push2_bridge.cli import build_parser, parse_color


class TestParseColor:
    def test_valid_color(self):
        assert parse_color("255,0,128") == (255, 0, 128)

    def test_valid_color_with_spaces(self):
        assert parse_color("255, 0, 128") == (255, 0, 128)

    def test_black(self):
        assert parse_color("0,0,0") == (0, 0, 0)

    def test_white(self):
        assert parse_color("255,255,255") == (255, 255, 255)

    def test_rejects_out_of_range(self):
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid color"):
            parse_color("256,0,0")

    def test_rejects_negative(self):
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid color"):
            parse_color("-1,0,0")

    def test_rejects_wrong_count(self):
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid color"):
            parse_color("255,0")

    def test_rejects_non_numeric(self):
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid color"):
            parse_color("red,green,blue")


class TestArgParsing:
    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.fps == 30
        assert args.syphon_server is None
        assert args.fallback_color == (0, 0, 0)
        assert args.verbose is False

    def test_fps_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--fps", "60"])
        assert args.fps == 60

    def test_syphon_server_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--syphon-server", "MyServer"])
        assert args.syphon_server == "MyServer"

    def test_fallback_color_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--fallback-color", "255,128,0"])
        assert args.fallback_color == (255, 128, 0)

    def test_verbose_short(self):
        parser = build_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose is True

    def test_verbose_long(self):
        parser = build_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_interpolation_default(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.interpolation == "linear"

    def test_interpolation_nearest(self):
        parser = build_parser()
        args = parser.parse_args(["--interpolation", "nearest"])
        assert args.interpolation == "nearest"

    def test_interpolation_invalid(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--interpolation", "cubic"])
