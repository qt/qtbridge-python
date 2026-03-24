# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Toy:
    name: str
    image: str
    original_price: int
    discount_percent: int
    rating: float
    reviews: int
    description: str


@dataclass
class Accessory:
    group: str
    name: str
    new_price: int
    old_price: int
    image: str
    selected: bool
    color: str
    key: str
    model_rating: float


@dataclass
class NamePart:
    group: str   # "adjectives" or "noun"
    name: str
    selected: bool


@dataclass
class AnimalConfig:
    name: str
    mesh_source: str
    base_color: str
    normal_map: str
    eyes_mesh_source: str
    x: float
    y: float
    z: float
    rot_x: float
    rot_y: float
    rot_z: float
    rot_w: float
    custom_mesh: str
    mouth_pos_x: float = 0.0
    mouth_pos_y: float = 0.0
    mouth_pos_z: float = 0.0
    mouth_rot_x: float = 0.0
    mouth_rot_y: float = 0.0
    mouth_rot_z: float = 0.0
