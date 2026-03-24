# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
Download and extract ToyCustomizer assets (images, meshes, fonts, animations).

Run once before launching the example:
    python fetch_assets.py

Assets are placed in ToyCustomizer/ so that the QML relative-path
references (e.g. "images/Bear.png") resolve correctly from the QML files.
"""

import sys
import zipfile
import urllib.request
from pathlib import Path

ASSET_URL = "https://ordp.qt.io/qt/bundles/toycustomizer/toy-customizer-assets.zip"
DEST_DIR = Path(__file__).resolve().parent / "ToyCustomizer"
SENTINEL_DIRS = ("images", "meshes", "fonts", "animations")


def already_present() -> bool:
    return all((DEST_DIR / d).is_dir() for d in SENTINEL_DIRS)


def download_and_extract() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DEST_DIR.parent.parent / "toy-customizer-assets.zip"

    print(f"Downloading assets from {ASSET_URL} …")
    try:
        urllib.request.urlretrieve(ASSET_URL, zip_path)
    except Exception as exc:
        print(f"Error downloading assets: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting to {DEST_DIR} …")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(DEST_DIR)

    zip_path.unlink(missing_ok=True)
    # Icons are inside the downloaded images/ tree but QML looks them up as
    # "icons/..." relative to the qml directory.  Create a symlink so the
    # relative paths in QML files resolve without modification.
    icons_src = DEST_DIR / "images" / "icons"
    icons_dst = DEST_DIR / "icons"
    if icons_src.is_dir() and not icons_dst.exists():
        icons_dst.symlink_to(icons_src)

    print("Assets ready.")


if __name__ == "__main__":
    if already_present():
        print("Assets already present — nothing to do.")
    else:
        download_and_extract()
