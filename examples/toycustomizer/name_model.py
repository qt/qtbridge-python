# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from __future__ import annotations
from QtBridge import edit
from models import NamePart


class NameModelBackend:
    """
    Toy-name picker backend.  Ported from the adjectives/noun portion of
    AccessoryModel.qml.

    Registered as QML singleton "NameModelData" (uri="backend").
    """

    def __init__(self) -> None:
        self._parts: list[NamePart] = [
            NamePart("adjectives", "Wobbly",   False),
            NamePart("adjectives", "Clumsy",   False),
            NamePart("adjectives", "Bubbly",   False),
            NamePart("adjectives", "Snuggly",  False),
            NamePart("adjectives", "Zippy",    False),
            NamePart("adjectives", "Sparkly",  False),
            NamePart("adjectives", "Grumpy",   False),
            NamePart("adjectives", "Sleepy",   False),
            NamePart("adjectives", "Jolly",    False),
            NamePart("adjectives", "Witty",    False),
            NamePart("adjectives", "Sassy",    False),
            NamePart("adjectives", "Silly",    False),
            NamePart("adjectives", "Spunky",   False),
            NamePart("noun", "Puff",     False),
            NamePart("noun", "Sprout",   False),
            NamePart("noun", "Greg",     False),
            NamePart("noun", "Nibbles",  False),
            NamePart("noun", "Hops",     False),
            NamePart("noun", "Whiskers", False),
            NamePart("noun", "Breeze",   False),
            NamePart("noun", "Wolf",     False),
            NamePart("noun", "Cloud",    False),
            NamePart("noun", "Blossom",  False),
            NamePart("noun", "Feather",  False),
            NamePart("noun", "Spark",    False),
            NamePart("noun", "Oak",      False),
        ]

    def data(self) -> list[NamePart]:
        return self._parts

    def adjectives(self) -> list[NamePart]:
        return [p for p in self._parts if p.group == "adjectives"]

    def nouns(self) -> list[NamePart]:
        return [p for p in self._parts if p.group == "noun"]

    @edit
    def select_adjective(self, index: int) -> None:
        adj_index = -1
        for part in self._parts:
            if part.group == "adjectives":
                adj_index += 1
                part.selected = (adj_index == index)

    @edit
    def select_noun(self, index: int) -> None:
        noun_index = -1
        for part in self._parts:
            if part.group == "noun":
                noun_index += 1
                part.selected = (noun_index == index)

    def selected_name(self) -> str:
        adj = next((p.name for p in self._parts if p.group == "adjectives" and p.selected), "")
        noun = next((p.name for p in self._parts if p.group == "noun" and p.selected), "")
        return f"{adj} {noun}".strip()
