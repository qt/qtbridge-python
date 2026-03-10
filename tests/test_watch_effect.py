# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

"""
Tests for the @watch and @effect property-observer decorators.

Run with:
    pytest tests/test_watch_effect.py -v
"""

import pytest
from PySide6.QtQml import QQmlApplicationEngine

from QtBridge import watch, effect, Change, bridge_instance


class TestWatch:
    """Tests for the @watch decorator."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()

    def teardown_method(self):
        if self.engine is not None:
            del self.engine
            self.engine = None

    def test_callback_fires_on_change(self, qapp):
        """@watch callback is called with a Change object when the property changes."""
        changes = []

        class Counter:
            def __init__(self):
                self.count = 0

            @watch("count")
            def _on_count(self, change: Change):
                changes.append(change)

        c = Counter()
        bridge_instance(c, "Counter")
        c.count = 5

        assert len(changes) == 1
        ch = changes[0]
        assert ch.name == "count"
        assert ch.old == 0
        assert ch.new == 5
        assert ch.owner is c

    def test_callback_not_called_when_value_unchanged(self, qapp):
        """@watch callback must NOT fire when the identical value is set."""
        calls = []

        class Counter:
            def __init__(self):
                self.count = 0

            @watch("count")
            def _on_count(self, change: Change):
                calls.append(change)

        c = Counter()
        bridge_instance(c, "Counter")
        c.count = 0  # same value as initial

        assert len(calls) == 0

    def test_change_owner_is_the_specific_instance(self, qapp):
        """change.owner must be the exact instance whose property changed."""
        owners = []

        class Model:
            def __init__(self):
                self.x = 0

            @watch("x")
            def _on_x(self, change: Change):
                owners.append(change.owner)

        a = Model()
        bridge_instance(a, "ModelA")
        b = Model()
        bridge_instance(b, "ModelB")
        a.x = 1
        b.x = 2

        assert owners[0] is a
        assert owners[1] is b

    def test_new_value_matches_current_property(self, qapp):
        """change.new must equal self.<prop> at the time the callback runs."""
        seen = []

        class Model:
            def __init__(self):
                self.val = 0

            @watch("val")
            def _on_val(self, change: Change):
                # change.new should be the same as self.val at callback time
                seen.append((change.new, self.val))

        m = Model()
        bridge_instance(m, "Model")
        m.val = 42

        assert seen == [(42, 42)]

    def test_stacked_on_same_method_observes_both_properties(self, qapp):
        """Stacking @watch on the same method makes it observe both properties."""
        changes = []

        class Rect:
            def __init__(self):
                self.width = 10
                self.height = 20

            @watch("width")
            @watch("height")
            def _on_resize(self, change: Change):
                changes.append(change)

        r = Rect()
        bridge_instance(r, "Rect")
        r.width = 100
        r.height = 200

        assert len(changes) == 2
        names = {ch.name for ch in changes}
        assert names == {"width", "height"}

    def test_multiple_sequential_changes(self, qapp):
        """@watch fires for each distinct change; duplicate values are skipped."""
        log = []

        class Model:
            def __init__(self):
                self.val = 0

            @watch("val")
            def _on_val(self, change: Change):
                log.append((change.old, change.new))

        m = Model()
        bridge_instance(m, "Model")
        m.val = 1
        m.val = 2
        m.val = 2   # duplicate — should not fire
        m.val = 3

        assert log == [(0, 1), (1, 2), (2, 3)]

    def test_separate_methods_for_separate_properties(self, qapp):
        """Each @watch fires only for its own property, not for others."""
        log = []

        class Name:
            def __init__(self):
                self.first_name = "Alice"
                self.last_name = "Smith"

            @watch("first_name")
            def _on_first(self, change: Change):
                log.append(("first_name", change.old, change.new))

            @watch("last_name")
            def _on_last(self, change: Change):
                log.append(("last_name", change.old, change.new))

        n = Name()
        bridge_instance(n, "Name")
        n.first_name = "Bob"
        n.last_name = "Jones"

        assert log == [
            ("first_name", "Alice", "Bob"),
            ("last_name", "Smith", "Jones"),
        ]
        # Changing first_name must not trigger _on_last
        n.first_name = "Carol"
        assert log[-1][0] == "first_name"

    def test_raises_type_error_without_change_param(self, qapp):
        """@watch raises TypeError at decoration time if the change param is missing."""
        with pytest.raises(TypeError, match="change"):
            class Bad:
                def __init__(self):
                    self.x = 0

                @watch("x")
                def _on_x(self):  # missing change param
                    pass

    def test_raises_type_error_with_only_self(self, qapp):
        """@watch with only self (no change param) also raises TypeError."""
        with pytest.raises(TypeError):
            @watch("something")
            def handler(self):
                pass

class TestEffect:
    """Tests for the @effect decorator."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()

    def teardown_method(self):
        if self.engine is not None:
            del self.engine
            self.engine = None

    def test_fires_when_property_changes(self, qapp):
        """@effect callback is called when a listed property changes."""
        calls = []

        class Settings:
            def __init__(self):
                self.theme = "dark"

            @effect("theme")
            def _on_theme(self):
                calls.append(self.theme)

        s = Settings()
        bridge_instance(s, "Settings")
        s.theme = "light"

        assert len(calls) == 1
        assert calls[0] == "light"

    def test_not_called_when_value_unchanged(self, qapp):
        """@effect must NOT fire when the identical value is set."""
        calls = []

        class Settings:
            def __init__(self):
                self.theme = "dark"

            @effect("theme")
            def _on_theme(self):
                calls.append(self.theme)

        s = Settings()
        bridge_instance(s, "Settings")
        s.theme = "dark"  # same value

        assert len(calls) == 0

    def test_fires_for_each_listed_property(self, qapp):
        """@effect fires for each of the listed properties independently."""
        calls = []

        class Config:
            def __init__(self):
                self.font_size = 14
                self.theme = "dark"

            @effect("font_size", "theme")
            def _persist(self):
                calls.append((self.font_size, self.theme))

        cfg = Config()
        bridge_instance(cfg, "Config")
        cfg.font_size = 16
        cfg.theme = "light"

        assert len(calls) == 2
        assert calls[0] == (16, "dark")
        assert calls[1] == (16, "light")

    def test_self_reflects_new_value(self, qapp):
        """Inside @effect, self.<prop> already holds the new value."""
        seen = []

        class Model:
            def __init__(self):
                self.x = 0

            @effect("x")
            def _on_x(self):
                seen.append(self.x)

        m = Model()
        bridge_instance(m, "Model")
        m.x = 42

        assert seen == [42]

    def test_requires_at_least_one_property_name(self, qapp):
        """@effect with no arguments must raise TypeError."""
        with pytest.raises(TypeError):
            @effect()
            def noop(self):
                pass

    def test_multiple_changes_all_fire(self, qapp):
        """@effect fires for every distinct change, skips duplicates."""
        log = []

        class Counter:
            def __init__(self):
                self.val = 0

            @effect("val")
            def _record(self):
                log.append(self.val)

        c = Counter()
        bridge_instance(c, "Counter")
        c.val = 1
        c.val = 1  # duplicate — skipped
        c.val = 2

        assert log == [1, 2]

class TestWatchAndEffectCombined:
    """@watch and @effect can coexist on the same class observing the same or
    different properties."""

    def setup_method(self):
        self.engine = QQmlApplicationEngine()

    def teardown_method(self):
        if self.engine is not None:
            del self.engine
            self.engine = None

    def test_both_fire_for_same_property(self, qapp):
        """@watch and @effect can both observe the same property."""
        watch_log = []
        effect_log = []

        class Model:
            def __init__(self):
                self.score = 0

            @watch("score")
            def _on_score(self, change: Change):
                watch_log.append((change.old, change.new))

            @effect("score")
            def _side_effect(self):
                effect_log.append(self.score)

        m = Model()
        bridge_instance(m, "Model")
        m.score = 10

        assert watch_log == [(0, 10)]
        assert effect_log == [10]

    def test_effect_derived_from_multiple_properties(self, qapp):
        """@effect updates a derived attribute when any dependency changes."""

        class Name:
            def __init__(self):
                self.first_name = "Alice"
                self.last_name = "Smith"
                self.display_name = "Alice Smith"

            @effect("first_name", "last_name")
            def _update_display(self):
                self.display_name = f"{self.first_name} {self.last_name}"

        n = Name()
        bridge_instance(n, "Name")
        n.first_name = "Bob"
        assert n.display_name == "Bob Smith"

        n.last_name = "Jones"
        assert n.display_name == "Bob Jones"

    def test_watch_receives_correct_old_value_in_chain(self, qapp):
        """Chained changes: each @watch receives the correct old/new pair."""
        log = []

        class Counter:
            def __init__(self):
                self.count = 0

            @watch("count")
            def _on_count(self, change: Change):
                log.append((change.old, change.new))

        c = Counter()
        bridge_instance(c, "Counter")

        for new_val in [1, 2, 3]:
            c.count = new_val

        assert log == [(0, 1), (1, 2), (2, 3)]

    def test_independent_instances_do_not_share_callbacks(self, qapp):
        """Each instance's callbacks fire independently."""
        log = []

        class Model:
            def __init__(self):
                self.x = 0

            @watch("x")
            def _on_x(self, change: Change):
                log.append((id(change.owner), change.new))

        a = Model()
        bridge_instance(a, "ModelA")
        b = Model()
        bridge_instance(b, "ModelB")
        a.x = 1
        b.x = 2

        assert log[0] == (id(a), 1)
        assert log[1] == (id(b), 2)
