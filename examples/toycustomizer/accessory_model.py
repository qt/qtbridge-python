# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from __future__ import annotations
from QtBridge import Signal, edit, reset
from models import Accessory


class AccessoryModelBackend:
    """
    Backend for all accessory (headwear / eyewear / eyes / items) data and
    selection logic.  Ported from AccessoryModel.qml in C++ toy customizer example.
    """

    # Emitted by QML-connected handler to toggle 3D scene visibility.
    accessory_visibility_changed = Signal(str, bool)

    def __init__(self) -> None:
        self.total_selected_accessory: int = 0

        self._accessories: list[Accessory] = [
            Accessory(
                "headwear", "Beanie", 450, 900,
                "images/HeadwearImages/BeanieImage1.png",
                False, "", "beanieVisible", 3.77,
            ),
            Accessory(
                "headwear", "Cap", 275, 430,
                "images/HeadwearImages/CapImage1.png",
                False, "", "capVisible", 2.69,
            ),
            Accessory(
                "headwear", "Party Hat", 375, 610,
                "images/HeadwearImages/PartyHatImage1.png",
                False, "", "partyHatVisible", 3.31,
            ),
            Accessory(
                "headwear", "Headphones", 450, 840,
                "images/HeadwearImages/HeadphonesImage1.png",
                False, "", "headphonesVisible", 4.56,
            ),
            Accessory(
                "headwear", "Wizard Hat", 475, 890,
                "images/HeadwearImages/WizardHatImage1.png",
                False, "", "wizardHatVisible", 3.92,
            ),
            Accessory(
                "headwear", "Whiskers", 325, 520,
                "images/HeadwearImages/WhiskersImage1.png",
                False, "", "whiskersVisible", 2.87,
            ),
            Accessory(
                "headwear", "Bandana Hat", 650, 1430,
                "images/HeadwearImages/BandanaHatImage1.png",
                False, "", "bandanaVisible", 4.12,
            ),
            Accessory(
                "eyewear", "EyePatch", 300, 660,
                "images/EyewearImages/EyepatchImage1.png",
                False, "", "eyePatchVisible", 3.17,
            ),
            Accessory(
                "eyewear", "Incognito", 650, 1150,
                "images/EyewearImages/IncognitoImage1.png",
                False, "", "incognitoVisible", 1.98,
            ),
            Accessory(
                "eyewear", "Monacle", 250, 685,
                "images/EyewearImages/MonacleImage1.png",
                False, "", "monacleVisible", 2.34,
            ),
            Accessory(
                "eyewear", "Night Vision Goggles", 375, 800,
                "images/EyewearImages/NightVisionGogglesImage1.png",
                False, "", "nvGogglesVisible", 1.58,
            ),
            Accessory(
                "eyewear", "Sunglasses", 325, 590,
                "images/EyewearImages/SunglassesImage1.png",
                False, "", "sunglassesVisible", 5.00,
            ),
            Accessory(
                "eyewear", "Round Glasses", 250, 580,
                "images/EyewearImages/GlassesImage1.png",
                False, "", "roundGlassesVisible", 4.85,
            ),
            Accessory(
                "eyes", "Small Eyes", 0, 0,
                "images/EyesImages/SmallEyesImage1.png",
                True, "", "smallEyesVisible", 3.07,
            ),
            Accessory(
                "eyes", "Cute Eyes", 225, 610,
                "images/EyesImages/CuteEyesImage1.png",
                False, "", "cuteEyesVisible", 4.89,
            ),
            Accessory(
                "eyes", "Annoyed Eyes", 200, 360,
                "images/EyesImages/AnnoyedEyesImage1.png",
                False, "", "annoyedEyesVisible", 2.45,
            ),
            Accessory(
                "eyes", "Surprised Eyes", 200, 330,
                "images/EyesImages/SurprisedEyesImage1.png",
                False, "", "surprisedEyesVisible", 1.73,
            ),
            Accessory(
                "eyes", "Confused Eyes", 225, 390,
                "images/EyesImages/ConfusedEyesImage1.png",
                False, "", "confusedEyesVisible", 4.02,
            ),
            Accessory(
                "eyes", "Power Puff", 250, 530,
                "images/EyesImages/PowerPuffEyesImage1.png",
                False, "", "powerpuffEyesVisible", 4.52,
            ),
            Accessory(
                "eyes", "Wide Eyes", 150, 260,
                "images/EyesImages/WideEyesImage1.png",
                False, "", "wideEyesVisible", 1.92,
            ),
            Accessory(
                "items", "Butterfly Wings", 525, 1250,
                "images/ItemsImages/ButterflyWingsImage1.png",
                False, "", "butterflyWingsVisible", 4.23,
            ),
            Accessory(
                "items", "Angel Wings", 550, 1075,
                "images/ItemsImages/AngelWingsImage1.png",
                False, "", "angelWingsVisible", 4.38,
            ),
            Accessory(
                "items", "Bowtie", 400, 930,
                "images/ItemsImages/BowtieImage1.png",
                False, "", "bowtieVisible", 4.46,
            ),
            Accessory(
                "items", "Backpack", 475, 990,
                "images/ItemsImages/BackpackImage1.png",
                False, "", "backpackVisible", 3.92,
            ),
            Accessory(
                "items", "Necktie", 400, 660,
                "images/ItemsImages/NecktieImage1.png",
                False, "", "necktieVisible", 3.46,
            ),
            Accessory(
                "items", "Bracelets", 450, 790,
                "images/ItemsImages/BracletsImage1.png",
                False, "", "braceletsVisible", 2.68,
            ),
        ]

    def data(self) -> list[Accessory]:
        return self._accessories

    def groups(self) -> list[str]:
        return ["headwear", "eyewear", "eyes", "items"]

    def color_of(self, name: str) -> str:
        for acc in self._accessories:
            if acc.name == name:
                return acc.color
        return ""

    def _emit_visibility(self, key: str, visible: bool) -> None:
        if key == "braceletsVisible":
            self.accessory_visibility_changed.emit("metalBracelet_RightVisible", visible)
            self.accessory_visibility_changed.emit("metalBracelet_LeftVisible", visible)
        else:
            self.accessory_visibility_changed.emit(key, visible)

    @edit
    def select_accessory(self, index: int, group: str) -> None:
        for acc in self._accessories:
            if acc.group == group and acc.selected:
                acc.selected = False
                self._emit_visibility(acc.key, False)

        target = self._accessories[index]
        target.selected = True
        self._emit_visibility(target.key, True)
        self._update_total()

    @edit
    def deselect_accessory(self, index: int) -> None:
        target = self._accessories[index]
        if target.selected:
            target.selected = False
            self._emit_visibility(target.key, False)
            self._update_total()

    @edit
    def set_color(self, index: int, color: str) -> None:
        self._accessories[index].color = color

    @reset
    def reset_all(self) -> None:
        for acc in self._accessories:
            is_default = (acc.group == "eyes" and acc.name == "Small Eyes")
            acc.selected = is_default
            acc.color = ""
            self._emit_visibility(acc.key, is_default)
        self.total_selected_accessory = 0

    def _update_total(self) -> None:
        total = sum(
            1 for acc in self._accessories
            if acc.selected and acc.name != "Small Eyes"
        )
        self.total_selected_accessory = total
