# Copyright (C) 2024 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause


import sys
import requests
from typing import List, Any, Optional, Dict
from abstractresource import AbstractResource
from QtBridge import complete


class RestService:
    """RestService using Python requests instead of Qt networking"""

    def __init__(self) -> None:
        self._resources: list[AbstractResource] = []
        self._base_url: str = ""
        self._session: requests.Session = requests.Session()
        # Enable SSL verification by default
        self._session.verify = True
        # Add reqres.in API key header
        self._session.headers.update({"x-api-key": "reqres-free-v1"})
        self._component_complete_called: bool = False
        self._initialization_pending: bool = True

    @property
    def url(self) -> str:
        return self._base_url

    @url.setter
    def url(self, url: str) -> None:
        if self._base_url != url:
            self._base_url = url

    @property
    def sslSupported(self) -> bool:
        # Python requests always supports SSL
        return True

    @property
    def resources(self) -> list[AbstractResource]:
        """List of resources managed by this service"""
        return self._resources

    @resources.setter
    def resources(self, value: list[AbstractResource]) -> None:
        """Set the list of resources"""
        self._resources = value
        # If component is already complete, initialize new resources
        if self._component_complete_called:
            for resource in self._resources:
                resource.set_service(self)

    @complete
    def componentComplete(self) -> None:
        """Called automatically when QML component is complete - setup resources"""
        for resource in self._resources:
            resource.set_service(self)
        self._component_complete_called = True
        self._initialization_pending = False

    def initialize(self) -> None:
        """Public method to manually initialize the service from QML if needed"""
        if not self._component_complete_called:
            self.componentComplete()

    def _ensure_initialized(self) -> None:
        """Ensure all resources are initialized before making requests"""
        if self._initialization_pending or not self._component_complete_called:
            self.componentComplete()

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Perform GET request"""
        self._ensure_initialized()
        try:
            url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
            response = self._session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GET request failed: {e}", file=sys.stderr)
            return {}

    def post(self, path: str, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Send POST request"""
        self._ensure_initialized()
        try:
            url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
            response = self._session.post(url, json=data)
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            print(f"POST request failed: {e}", file=sys.stderr)
            return {}

    def put(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """Perform PUT request"""
        try:
            url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
            response = self._session.put(url, json=data)
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            print(f"PUT request failed: {e}", file=sys.stderr)
            return {}

    def delete(self, path: str) -> dict[str, Any]:
        """Perform DELETE request"""
        try:
            url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
            response = self._session.delete(url)
            response.raise_for_status()
            return response.json() if response.content else {}
        except Exception as e:
            print(f"DELETE request failed: {e}", file=sys.stderr)
            return {}

    def setAuthToken(self, token: str) -> None:
        """Set authentication token for requests"""
        if token:
            # Qt HTTP server expects 'token' header, not 'Authorization: Bearer'
            self._session.headers.update({"token": token})
        else:
            self._session.headers.pop("token", None)

    def set_auth_token(self, token: str) -> None:
        """Deprecated: use setAuthToken instead"""
        self.setAuthToken(token)
