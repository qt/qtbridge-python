# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
ToyCustomizer — QtBridge port of the Qt Quick 3D ToyCustomizer demo.

On first run, `main.py` will automatically download and extract the required
binary assets (images, meshes, fonts, animations) into the `ToyCustomizer/`
directory if they are not already present. You may also pre-download the
assets manually with:

    python fetch_assets.py

Then launch the example with:

    python main.py
"""

import sys

from QtBridge import qtbridge, bridge_instance

from toy_catalog import ToyModelBackend
from animation_config import AnimationConfigBackend
from accessory_model import AccessoryModelBackend
from name_model import NameModelBackend
from order_model import OrderBackend


@qtbridge(module="ToyCustomizer", type_name="Main", import_paths=["."])
def main():
    toy_model = ToyModelBackend()
    anim_config = AnimationConfigBackend()
    accessory_model = AccessoryModelBackend()
    name_model = NameModelBackend()
    order = OrderBackend(toy_model, accessory_model, name_model)

    bridge_instance(toy_model,      name="ToyModelData",       uri="backend")
    bridge_instance(anim_config,    name="AnimationModelData", uri="backend")
    bridge_instance(accessory_model, name="AccessoryModelData", uri="backend")
    bridge_instance(name_model,     name="NameModelData",      uri="backend")
    bridge_instance(order,          name="OrderData",          uri="backend")


if __name__ == "__main__":
    # If the ToyCustomizer assets haven't been downloaded yet, fetch them
    # automatically so the user doesn't need to run `fetch_assets.py` manually.
    try:
        from fetch_assets import already_present, download_and_extract
    except Exception:
        # If the helper script can't be imported, continue and let the
        # application fail later if assets are truly missing.
        pass
    else:
        if not already_present():
            print("ToyCustomizer assets missing; fetching now...")
            download_and_extract()

    sys.exit(main())
