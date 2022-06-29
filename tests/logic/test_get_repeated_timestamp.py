# -*- coding: utf-8 -*-
import pytest

from app.logic import get_repeated_timestamp
from app.types import RepeatTypeEnum


def test_get_repeated_timestamp():
    assert get_repeated_timestamp(0, RepeatTypeEnum.daily) == 60*60*24
    assert get_repeated_timestamp(0, RepeatTypeEnum.weekly) == 60*60*24*7
    assert get_repeated_timestamp(0, RepeatTypeEnum.monthly) == 60*60*24*31
    assert get_repeated_timestamp(3000000, RepeatTypeEnum.monthly) == 3000000 + 60*60*24*28  # that was february
    assert get_repeated_timestamp(0, RepeatTypeEnum.yearly) == 60*60*24*365
    assert get_repeated_timestamp(63072000, RepeatTypeEnum.yearly) == 63072000 + 60*60*24*366  # that was leap year
    assert get_repeated_timestamp(0, RepeatTypeEnum.every_working_day) == 60*60*24
    assert get_repeated_timestamp(1950000, RepeatTypeEnum.every_working_day) == 1950000 + 60*60*24*3  # that was friday

    with pytest.raises(AssertionError):
        get_repeated_timestamp(0, RepeatTypeEnum.none)
