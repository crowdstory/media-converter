#!/usr/bin/env python3
"""
generate_oriented_images.py

Given a source image, create eight versions tagged with EXIF Orientation values 1–8,
and name each file with both the numeric code and a descriptive label.

Usage:
    python generate_oriented_images.py input.jpg output_directory
"""

import argparse
from pathlib import Path
from PIL import Image

ORIENTATION_TAG = 274  # EXIF tag code for Orientation

# Map EXIF orientation codes to descriptive labels
ORIENTATION_LABELS = {
    1: "normal",
    2: "flip_horizontal",
    3: "rotate_180",
    4: "flip_vertical",
    5: "transpose",      # rotate 90° CCW + flip horizontal
    6: "rotate_90",      # rotate 90° CCW
    7: "transverse",     # rotate 90° CW + flip horizontal
    8: "rotate_270",     # rotate 90° CW
}

def generate_oriented_versions(input_path: Path, output_dir: Path) -> None:
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open source image
    img = Image.open(input_path)

    stem = input_path.stem
    suffix = input_path.suffix

    for orientation, label in ORIENTATION_LABELS.items():
        # Read fresh EXIF and set Orientation tag
        exif = img.getexif()
        exif[ORIENTATION_TAG] = orientation

        # Build output filename
        out_file = output_dir / f"{stem}_{orientation}_{label}{suffix}"

        # Save with updated EXIF
        img.save(out_file, exif=exif.tobytes())

    print(f"Generated oriented images in: {output_dir}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate EXIF-orientation variants of an image"
    )
    parser.add_argument("input_image", type=Path, help="Path to source image")
    parser.add_argument(
        "output_dir", type=Path, help="Directory where output images will be saved"
    )
    args = parser.parse_args()

    generate_oriented_versions(args.input_image, args.output_dir)

if __name__ == "__main__":
    main()
