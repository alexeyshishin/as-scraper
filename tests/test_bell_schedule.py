from __future__ import annotations

from datetime import time

import pytest

from domain.bell_schedule import BELL_SCHEDULE, slot_to_times


def test_slot_to_times_known_slot():
    start, end = slot_to_times(1)
    assert start == time(8, 45)
    assert end == time(10, 20)


def test_all_slots_resolve():
    for slot in BELL_SCHEDULE:
        start, end = slot_to_times(slot)
        assert start < end


def test_unknown_slot_raises():
    with pytest.raises(ValueError):
        slot_to_times(99)
