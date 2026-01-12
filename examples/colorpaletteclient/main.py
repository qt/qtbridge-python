# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""QtBridges port of the Qt RESTful API client demo from Qt v6.x"""

from QtBridge import qtbridge, bridge_type

from basiclogin import BasicLogin
from paginatedresource import PaginatedColorUsersResource, PaginatedColorsResource
from restservice import RestService
from abstractresource import AbstractResource
import rc_colorpaletteclient  # noqa: F401

@qtbridge(
    module="ColorPalette",
    type_name="Main",
)
def main() -> None:
    bridge_type(AbstractResource, uri="ColorPalette", version="1.0")
    bridge_type(RestService, uri="ColorPalette", version="1.0", default_property="resources")
    bridge_type(BasicLogin, uri="ColorPalette", version="1.0")
    bridge_type(PaginatedColorUsersResource, uri="ColorPalette", version="1.0")
    bridge_type(PaginatedColorsResource, uri="ColorPalette", version="1.0")

if __name__ == "__main__":
    main()
