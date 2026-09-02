#!/usr/bin/env python3
"""
Generate synthetic test keyframes for AMD Radeon 660M validation.
Creates beach_v1-v4, car_v1-v4, forest_v1-v4, etc.
Generates as 1280x720 PNG files with distinct motion characteristics.
"""
import os
import struct
import zlib
import sys
from pathlib import Path

def png_create(width, height, rgb_data):
    """Create valid PNG from raw RGB bytes using only stdlib (struct + zlib)."""
    assert len(rgb_data) == width * height * 3, f"RGB data size mismatch"

    # PNG signature
    png = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk: image header
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png += struct.pack('>I', 13) + b'IHDR' + ihdr_data
    png += struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)

    # IDAT chunk: image data (scanlines with filter byte)
    scanlines = b''
    for y in range(height):
        scanlines += b'\x00'  # Filter type: None
        scanlines += rgb_data[y * width * 3 : (y+1) * width * 3]

    idat_data = zlib.compress(scanlines, 9)
    png += struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data
    png += struct.pack('>I', zlib.crc32(b'IDAT' + idat_data) & 0xffffffff)

    # IEND chunk: end marker
    png += struct.pack('>I', 0) + b'IEND'
    png += struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)

    return png

def gen_scene(location, version, width=1280, height=720):
    """Generate synthetic test frame with location-specific color gradient."""
    colors = {
        'beach': (255, 200, 100),    # Sandy beach tone
        'car': (80, 80, 90),         # Dark car interior
        'forest': (40, 100, 40),     # Green forest
        'kitchen': (200, 180, 160),  # Warm kitchen
        'park': (100, 180, 100),     # Green park
        'schoolyard': (200, 200, 200)# Gray schoolyard
    }

    base_r, base_g, base_b = colors.get(location, (128, 128, 128))

    # Add version variation: each version shifts color slightly
    version_shift = (version - 1) * 20
    r = max(0, min(255, base_r + version_shift))
    g = max(0, min(255, base_g + version_shift // 2))
    b = max(0, min(255, base_b - version_shift // 2))

    # Create simple gradient
    rgb_data = bytearray()
    for y in range(height):
        for x in range(width):
            # Horizontal gradient for motion simulation
            grad = int((x / width) * 50)
            rgb_data.append(max(0, min(255, r + grad)))
            rgb_data.append(max(0, min(255, g + grad // 2)))
            rgb_data.append(max(0, min(255, b + grad)))

    return png_create(width, height, bytes(rgb_data))

def main():
    """Generate all 24 test keyframes."""
    locations = ['beach', 'car', 'forest', 'kitchen', 'park', 'schoolyard']

    # Create keyframes directory if needed
    keyframes_dir = Path.cwd()

    count = 0
    for location in locations:
        for version in range(1, 5):
            filename = f"{location}_v{version}.png"
            filepath = keyframes_dir / filename

            print(f"Generating {filename}... ", end='', flush=True)
            png_data = gen_scene(location, version)

            with open(filepath, 'wb') as f:
                f.write(png_data)

            size_mb = filepath.stat().st_size / (1024*1024)
            print(f"✓ ({size_mb:.2f}M)")
            count += 1

    print(f"\n✓ Generated {count} test keyframes")
    print(f"  Ready for micro test: beach_v1.png → beach_v2.png")

if __name__ == '__main__':
    main()
