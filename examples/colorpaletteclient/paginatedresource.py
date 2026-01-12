# Copyright (C) 2024 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause


import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

from QtBridge import reset, bridge_instance
from abstractresource import AbstractResource


@dataclass
class ColorUser:
    id: int
    email: str
    avatar: str  # URL


@dataclass
class Color:
    color_id: int
    color: str
    name: str
    pantone_value: str


class ColorUserModel:
    """Model for color users that QML can use as a list model"""

    def __init__(self) -> None:
        self._users: list[ColorUser] = []

    def data(self) -> list[ColorUser]:
        """Return the main data list that BridgePyTypeObjectModel will expose to QML"""
        print("ColorUserModel data requested with", len(self._users), "users")
        return self._users

    def clear(self) -> None:
        """Clear all users"""
        self._users.clear()

    @reset
    def set_data(self, json_list: list[dict[str, Any]]) -> None:
        """Set users from JSON data using @reset decorator for proper model updates"""
        print("ColorUserModel set_data called with", len(json_list), "users")
        self._users.clear()
        for item in json_list:
            print("Processing user item:", item)
            try:
                user = ColorUser(
                    id=int(item["id"]),
                    email=item["email"],
                    avatar=item["avatar"]
                )
                self._users.append(user)
                print(f"Added user: {user.email}")
            except (KeyError, ValueError) as e:
                print(f"Error parsing user data: {e}", file=sys.stderr)

    def avatarForEmail(self, email: str) -> str:
        """Get avatar URL for a given email"""
        for user in self._users:
            if user.email == email:
                return user.avatar
        return ""


class ColorModel:
    """Model for colors that QML can use as a list model"""

    def __init__(self) -> None:
        self._colors: list[Color] = []

    def data(self) -> list[Color]:
        """Return the main data list that BridgePyTypeObjectModel will expose to QML"""
        return self._colors

    def clear(self) -> None:
        """Clear all colors"""
        self._colors.clear()

    @reset
    def set_data(self, json_list: list[dict[str, Any]]) -> None:
        """Set colors from JSON data using @reset decorator for proper model updates"""
        self._colors.clear()
        for item in json_list:
            try:
                # Handle both 'id' (reqres.in) and 'color_id' (FastAPI server)
                color_id = int(item.get("color_id") or item.get("id"))
                color = Color(
                    color_id=color_id,
                    color=item["color"],
                    name=item["name"],
                    pantone_value=item["pantone_value"]
                )
                self._colors.append(color)
                print(f"Added color: {color.name}")
            except (KeyError, ValueError) as e:
                print(f"Error parsing color data: {e}", file=sys.stderr)


class PaginatedResource(AbstractResource):
    """This class manages a simple paginated CRUD resource,
       where the resource is a paginated list of JSON items."""

    def __init__(self) -> None:
        super().__init__()
        # The total number of pages as reported by the server responses
        self._pages: int = 0
        # The default page we request if the user hasn't set otherwise
        self._current_page: int = 1
        self._path: str = ""
        self._data_updated: bool = False

    def _clear_model(self) -> None:
        """Override in subclasses to clear the specific model"""
        pass

    def _populate_model(self, json_list: list[dict[str, Any]]) -> None:
        """Override in subclasses to populate the specific model"""
        pass

    @property
    def data(self) -> bool:
        """Data property that triggers signal when data changes"""
        return self._data_updated

    @data.setter
    def data(self, value: bool) -> None:
        self._data_updated = value

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, p: str) -> None:
        self._path = p

    @property
    def pages(self) -> int:
        return self._pages

    @property
    def page(self) -> int:
        return self._current_page

    @page.setter
    def page(self, page: int) -> None:
        if self._current_page == page or page < 1:
            return
        self._current_page = page
        self.refreshCurrentPage()

    def refreshCurrentPage(self) -> bool:
        """Refresh the current page data from the server. Returns True on success."""
        if not self._service:
            print("No service configured for pagination", file=sys.stderr)
            return False

        try:
            # Add page parameter to the request
            params = {"page": str(self._current_page)}
            response = self._service.get(self._path, params)

            if response:
                self.refreshRequestFinished(response)
                return True
            else:
                self.refreshRequestFailed()
                return False
        except Exception as e:
            print(f"PaginatedResource error: {e}", file=sys.stderr)
            self.refreshRequestFailed()
            return False

    def refreshRequestFinished(self, json_data: dict[str, Any]) -> None:
        """Handle successful refresh response"""
        try:
            self._populate_model(json_data.get("data", []))
            self._pages = int(json_data.get("total_pages", 0))
            self._current_page = int(json_data.get("page", 1))
            # NOTE: Setting self.data from Python doesn't trigger signals for bridge_type
            # Signal emission must come from QML property write or explicit C++ call
            print(f"Refreshed page {self._current_page} of {self._pages}")
        except (ValueError, KeyError) as e:
            print(f"Error parsing pagination data: {e}", file=sys.stderr)
            self.refreshRequestFailed()

    def refreshRequestFailed(self) -> None:
        """Handle failed refresh"""
        if self._current_page != 1:
            # A failed refresh. If we weren't on page 1, try that.
            # Last resource on currentPage might have been deleted, causing a failure
            self.page = 1
        else:
            # Refresh failed and we were already on page 1 => clear data
            self._pages = 0
            self._clear_model()

    def update(self, data: dict[str, Any], item_id: int) -> None:
        """Update an existing item"""
        if not self._service:
            print("No service configured for update", file=sys.stderr)
            return

        try:
            response = self._service.put(f"{self._path}/{item_id}", data)
            if response:
                self.refreshCurrentPage()
        except Exception as e:
            print(f"Update error: {e}", file=sys.stderr)

    def add(self, data: dict[str, Any]) -> None:
        """Add a new item"""
        if not self._service:
            print("No service configured for add", file=sys.stderr)
            return

        try:
            print(f"Adding item with data: {data}")  # Debug
            response = self._service.post(self._path, data)
            if response:
                self.refreshCurrentPage()
        except Exception as e:
            print(f"Add error: {e}", file=sys.stderr)

    def remove(self, item_id: int) -> None:
        """Remove an item by ID"""
        if not self._service:
            print("No service configured for remove", file=sys.stderr)
            return

        try:
            response = self._service.delete(f"{self._path}/{item_id}")
            if response is not None:  # DELETE might return empty response
                self.refreshCurrentPage()
        except Exception as e:
            print(f"Remove error: {e}", file=sys.stderr)


class PaginatedColorUsersResource(PaginatedResource):
    """Paginated resource for color users"""

    def __init__(self) -> None:
        super().__init__()
        self._model = ColorUserModel()
        bridge_instance(self._model, name="ColorUserModel")

    @property
    def model(self) -> ColorUserModel:
        """Return the Python model"""
        return self._model

    def _clear_model(self) -> None:
        self._model.clear()

    def _populate_model(self, json_list: list[dict[str, Any]]) -> None:
        self._model.set_data(json_list)

    def avatarForEmail(self, email: str) -> str:
        """Get avatar URL for a given email"""
        return self._model.avatarForEmail(email)


class PaginatedColorsResource(PaginatedResource):
    """Paginated resource for colors"""

    def __init__(self) -> None:
        super().__init__()
        self._model = ColorModel()
        bridge_instance(self._model, name="ColorModel")

    @property
    def model(self) -> ColorModel:
        """Return the Python model"""
        return self._model

    def _clear_model(self) -> None:
        self._model.clear()

    def _populate_model(self, json_list: list[dict[str, Any]]) -> None:
        self._model.set_data(json_list)
