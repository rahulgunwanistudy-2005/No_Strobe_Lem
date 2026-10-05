"""Independent byte-level fidelity check for the live capture's PNG writer."""

import importlib.util
import struct
import zlib
from pathlib import Path

import pytest


def test_capture_png_preserves_rgb_rows_and_valid_checksums():
    path = Path(__file__).resolve().parents[3] / "tools/capture_vvd.py"
    spec = importlib.util.spec_from_file_location("capture_vvd", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pixels = bytes([0, 255, 17, 32, 70, 128, 219, 235, 255, 48, 64, 16])
    encoded = module.png_rgb(pixels, 2, 2)
    assert encoded[:8] == b"\x89PNG\r\n\x1a\n"
    position, chunks = 8, {}
    while position < len(encoded):
        size = struct.unpack(">I", encoded[position : position + 4])[0]
        kind = encoded[position + 4 : position + 8]
        data = encoded[position + 8 : position + 8 + size]
        crc = struct.unpack(">I", encoded[position + 8 + size : position + 12 + size])[0]
        assert zlib.crc32(kind + data) & 0xFFFFFFFF == crc
        chunks[kind] = data
        position += 12 + size
    assert struct.unpack(">IIBBBBB", chunks[b"IHDR"]) == (2, 2, 8, 2, 0, 0, 0)
    assert zlib.decompress(chunks[b"IDAT"]) == b"\0" + pixels[:6] + b"\0" + pixels[6:]
    assert chunks[b"IEND"] == b""
    with pytest.raises(ValueError, match="RGB"):
        module.png_rgb(pixels[:-1], 2, 2)
