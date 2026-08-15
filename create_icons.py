#!/usr/bin/env python3
"""Convert neon fungai logo to PNG and ICO formats."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def create_fungai_icon(size=256, filename="app/icon.png"):
    """Create neon fungai icon."""
    # Create image with black background
    img = Image.new('RGBA', (size, size), (5, 8, 5, 255))
    draw = ImageDraw.Draw(img, 'RGBA')

    # Neon green color
    neon_green = (0, 255, 102, 255)
    neon_green_bright = (51, 255, 153, 255)

    margin = size // 8
    inner_size = size - (2 * margin)

    # Outer rectangle
    draw.rectangle(
        [(margin, margin), (margin + inner_size, margin + inner_size)],
        outline=neon_green,
        width=3
    )

    # Inner rectangle
    inner_margin = margin + size // 16
    inner_inner_size = size - (2 * inner_margin)
    draw.rectangle(
        [(inner_margin, inner_margin), (inner_margin + inner_inner_size, inner_margin + inner_inner_size)],
        outline=neon_green,
        width=2
    )

    # Center diamond (neon crystal)
    center = size // 2
    diamond_size = size // 6
    points = [
        (center, center - diamond_size),  # top
        (center + diamond_size, center),  # right
        (center, center + diamond_size),  # bottom
        (center - diamond_size, center),  # left
    ]
    draw.polygon(points, outline=neon_green, width=2)

    # Inner filled diamond
    inner_diamond_size = size // 8
    inner_points = [
        (center, center - inner_diamond_size),
        (center + inner_diamond_size, center),
        (center, center + inner_diamond_size),
        (center - inner_diamond_size, center),
    ]
    draw.polygon(inner_points, fill=neon_green)

    # Apply slight glow effect
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    # Save PNG
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(filename, 'PNG')
    print(f"✓ Created {filename} ({size}x{size})")

    # Create ICO for Windows (multiple sizes)
    ico_path = filename.replace('.png', '.ico')
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_images = []

    for w, h in sizes:
        resized = img.resize((w, h), Image.Resampling.LANCZOS)
        ico_images.append(resized)

    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=sizes
    )
    print(f"✓ Created {ico_path} (multiple sizes)")

    # Create PNG sizes for other platforms
    for size_px in [16, 32, 48, 64, 128]:
        png_size = img.resize((size_px, size_px), Image.Resampling.LANCZOS)
        png_filename = f"app/icon-{size_px}.png"
        png_size.save(png_filename, 'PNG')
        print(f"✓ Created {png_filename}")

if __name__ == "__main__":
    create_fungai_icon(256, "app/icon.png")
    print("\n✨ Neon fungai icons created!")
