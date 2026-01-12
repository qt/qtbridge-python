# Copyright (C) 2024 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause


import sys
from dataclasses import dataclass
from typing import Optional, Any

from abstractresource import AbstractResource


@dataclass
class User:
    email: str
    token: str
    id: int


class BasicLogin(AbstractResource):
    """Handle user authentication using Python requests"""

    def __init__(self) -> None:
        super().__init__()
        self._user: Optional[User] = None
        self._login_path: str = ""
        self._logout_path: str = ""

    @property
    def user(self) -> str:
        return self._user.email if self._user else ""

    @user.setter
    def user(self, value: str) -> None:
        # Dummy setter to allow QML to write to this property
        # This is needed for the workaround where QML writes the property
        # to trigger the userChanged signal
        pass

    @property
    def loggedIn(self) -> bool:
        return bool(self._user)

    @loggedIn.setter
    def loggedIn(self, value: bool) -> None:
        # Dummy setter to allow QML to write to this property
        # This is needed for the workaround where QML writes the property
        # to trigger the loggedInChanged signal
        pass

    @property
    def loginPath(self) -> str:
        return self._login_path

    @loginPath.setter
    def loginPath(self, path: str) -> None:
        self._login_path = path

    @property
    def logoutPath(self) -> str:
        return self._logout_path

    @logoutPath.setter
    def logoutPath(self, path: str) -> None:
        self._logout_path = path

    def login(self, data: dict[str, Any]) -> bool:
        """Perform login with provided credentials

        Returns True if login was successful, False otherwise.
        QML should re-read user and loggedIn properties after this returns True.
        """
        if not self._service:
            print("No service configured for login", file=sys.stderr)
            return False

        try:
            response = self._service.post(self._login_path, data)
            if response:
                token = response.get("token")
                if token:
                    email = data.get("email", "")
                    user_id = response.get("id", data.get("id", 0))
                    self._user = User(email=email, token=token, id=user_id)
                    # Set auth token for future requests
                    self._service.set_auth_token(token)
                    print(f"Login successful for {email}")
                    return True
                else:
                    print("Login failed: No token received", file=sys.stderr)
            else:
                print("Login failed: Empty response", file=sys.stderr)
        except Exception as e:
            print(f"Login error: {e}", file=sys.stderr)

        return False

    def logout(self) -> bool:
        """Perform logout

        Returns True if logout was successful, False otherwise.
        QML should re-read user and loggedIn properties after this returns True.
        """
        if not self._service:
            print("No service configured for logout", file=sys.stderr)
            return False

        try:
            response = self._service.post(self._logout_path, {})
            self._user = None
            # Clear auth token
            self._service.set_auth_token("")
            print("Logout successful")
            return True
        except Exception as e:
            print(f"Logout error: {e}", file=sys.stderr)
            return False
