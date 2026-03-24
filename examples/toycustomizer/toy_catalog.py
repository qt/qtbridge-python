# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from models import Toy


class ToyModelBackend:
    def data(self) -> list[Toy]:
        return [
            Toy("Teddy Bear", "images/Bear.png", 900, 50, 4.85, 451,
                "A classic companion with a fluffy hug and gentle eyes, "
                "this teddy brings comfort and warmth to every moment."),
            Toy("Koala", "images/Koala.png", 450, 0, 4.75, 301,
                "This cuddly koala loves cozy naps and gentle hugs, "
                "always ready to bring a smile and soft comfort to your day."),
            Toy("Lion", "images/Lion.png", 900, 25, 4.85, 315,
                "With a golden mane and a brave heart, "
                "this lion is always ready for big adventures and warm cuddles."),
            Toy("Monkey", "images/Monkey.png", 450, 50, 4.75, 301,
                "Playful and full of mischief, this cheeky monkey loves "
                "to swing, giggle, and share endless fun with friends."),
            Toy("Cat", "images/Cat.png", 900, 50, 4.85, 315,
                "Soft and curious, this cuddly cat loves gentle snuggles "
                "and quiet moments filled with purrs and charm."),
            Toy("Reindeer", "images/Deer.png", 450, 0, 4.75, 212,
                "Soft and sweet, this little reindeer brings "
                "calm charm and cozy friendship everywhere it goes."),
            Toy("Panda", "images/Panda.png", 900, 0, 4.85, 301,
                "Gentle and round, this panda brings "
                "peaceful hugs and quiet joy wherever it goes."),
            Toy("Pig", "images/Pig.png", 450, 0, 4.75, 315,
                "A sweet piglet with a round belly, always ready to play and make friends."),
            Toy("Sloth", "images/Sloth.png", 900, 50, 4.85, 451,
                "A gentle sloth with a sleepy smile, perfect for slow cuddles and quiet moments."),
            Toy("Rabbit", "images/Rabbit.png", 450, 50, 4.75, 376,
                "With a soft coat and a friendly smile, "
                "this bunny is made for fun and friendship."),
            Toy("Raccoon", "images/Raccoon.png", 450, 50, 4.75, 315,
                "A playful raccoon with a soft mask, perfect for cuddles and little adventures."),
            Toy("Sheep", "images/Sheep.png", 900, 0, 4.85, 289,
                "A fluffy sheep with soft wool, always ready for cozy cuddles and gentle play."),
            Toy("Tiger", "images/Tiger.png", 450, 0, 4.75, 212,
                "A bold tiger with dark stripes, ready for wild games and big adventures."),
            Toy("Squirrel", "images/Squirrel.png", 900, 0, 4.85, 376,
                "A lively squirrel with a bushy tail, "
                "always ready to scurry and stash treats for later."),
        ]

    def get(self, index: int) -> dict:
        t = self.data()[index]
        return {
            "name":            t.name,
            "image":           t.image,
            "originalPrice":   t.original_price,
            "discountPercent": t.discount_percent,
            "rating":          t.rating,
            "reviews":         t.reviews,
            "description":     t.description,
        }
