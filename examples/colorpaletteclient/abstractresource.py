# Copyright (C) 2024 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from restservice import RestService


class AbstractResource:
    """Base class for resources that interact with REST API"""

    def __init__(self) -> None:
        self._service: 'RestService' = None

    def set_service(self, service: 'RestService') -> None:
        """Set the REST service for making HTTP requests"""
        self._service = service
