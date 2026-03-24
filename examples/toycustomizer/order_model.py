# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from __future__ import annotations
from QtBridge import watch

from toy_catalog import ToyModelBackend
from accessory_model import AccessoryModelBackend
from name_model import NameModelBackend


class OrderBackend:
    def __init__(
        self,
        toy_backend: ToyModelBackend,
        accessory_backend: AccessoryModelBackend,
        name_backend: NameModelBackend,
    ) -> None:
        self._toys = toy_backend
        self._accessories = accessory_backend
        self._names = name_backend

        # auto property
        self.total_price: float = 0.0
        self.toy_index: int = -1

        # Per-slot display properties
        self.toy_name: str = ""
        self.toy_image: str = ""
        self.toy_old_price: int = 0
        self.toy_new_price: float = 0.0

        self.face_name: str = ""
        self.face_image: str = ""
        self.face_new_price: int = 0
        self.face_old_price: int = 0

        self.headwear_name: str = ""
        self.headwear_image: str = ""
        self.headwear_new_price: int = 0
        self.headwear_old_price: int = 0

        self.eyewear_name: str = ""
        self.eyewear_image: str = ""
        self.eyewear_new_price: int = 0
        self.eyewear_old_price: int = 0

        self.item_name: str = ""
        self.item_image: str = ""
        self.item_new_price: int = 0
        self.item_old_price: int = 0

        self.selected_name: str = ""

    @watch("toy_index")
    def _on_toy_changed(self, _change) -> None:
        self.calculate_order()

    def calculate_order(self) -> None:
        total: float = 0.0
        self.face_name = self.face_image = ""
        self.face_new_price = self.face_old_price = 0
        self.headwear_name = self.headwear_image = ""
        self.headwear_new_price = self.headwear_old_price = 0
        self.eyewear_name = self.eyewear_image = ""
        self.eyewear_new_price = self.eyewear_old_price = 0
        self.item_name = self.item_image = ""
        self.item_new_price = self.item_old_price = 0

        if self.toy_index >= 0:
            toys = self._toys.data()
            if self.toy_index < len(toys):
                toy = toys[self.toy_index]
                self.toy_name = toy.name
                self.toy_image = toy.image
                self.toy_old_price = toy.original_price
                toy_price = toy.original_price * (1 - toy.discount_percent / 100)
                self.toy_new_price = toy_price
                total += toy_price

        for acc in self._accessories.data():
            if not acc.selected:
                continue
            if acc.group == "eyes" and acc.name != "Small Eyes":
                self.face_name = acc.name
                self.face_image = acc.image
                self.face_new_price = acc.new_price
                self.face_old_price = acc.old_price
                total += acc.new_price
            elif acc.group == "headwear":
                self.headwear_name = acc.name
                self.headwear_image = acc.image
                self.headwear_new_price = acc.new_price
                self.headwear_old_price = acc.old_price
                total += acc.new_price
            elif acc.group == "eyewear":
                self.eyewear_name = acc.name
                self.eyewear_image = acc.image
                self.eyewear_new_price = acc.new_price
                self.eyewear_old_price = acc.old_price
                total += acc.new_price
            elif acc.group == "items":
                self.item_name = acc.name
                self.item_image = acc.image
                self.item_new_price = acc.new_price
                self.item_old_price = acc.old_price
                total += acc.new_price

        self.selected_name = self._names.selected_name()

        self.total_price = total
