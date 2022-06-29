# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask import Flask

import pytest

from app.db_actions import (
    create_meeting,
    create_user,
)
from app.logic import (
    find_first_free_window_among_meetings,
    RepeatTypeEnum,
)


@pytest.fixture()
def many_meetings(app: Flask):
    creator = create_user('creator', password='')
    return [
        create_meeting(creator=creator, start=1000, end=2000),
        create_meeting(creator=creator, start=1000, end=4000),
        create_meeting(creator=creator, start=4500, end=6000),
        create_meeting(creator=creator, start=7000, end=8000),
    ]


def test_find_first_free_window_among_meetings_has_time_before_first_meeting(many_meetings):
    assert find_first_free_window_among_meetings(many_meetings, 900, 0) == 0


def test_find_first_free_window_among_meetings_has_time_only_after_all_meetings(many_meetings):
    assert find_first_free_window_among_meetings(many_meetings, 1100, 0) == 8000


def test_find_first_free_window_among_meetings(many_meetings):
    assert find_first_free_window_among_meetings(many_meetings, 900, 600) == 6000


def test_find_first_free_window_among_meetings_no_meetings():
    assert find_first_free_window_among_meetings([], 900, 0) == 0


@pytest.fixture()
def with_daily_meeting(app: Flask):
    creator = create_user('user1', password='')
    m1 = create_meeting(
        creator=creator,
        start=datetime.fromisoformat('2022-06-22T17:00+00:00'),
        end=datetime.fromisoformat('2022-06-22T18:00+00:00'),
        repeat_type=RepeatTypeEnum.daily,
    )
    m2 = create_meeting(
        creator=creator,
        start=datetime.fromisoformat('2022-06-21T17:00+00:00'),
        end=datetime.fromisoformat('2022-06-23T17:00+00:00'),
    )
    return [m1, m2]


def test_find_first_free_window_among_meetings_with_daily_meeting(with_daily_meeting):
    start = find_first_free_window_among_meetings(
        meetings=with_daily_meeting,
        window_size=60*60,
        start=datetime.fromisoformat('2022-06-21T17:00+00:00'),
    )
    assert datetime.fromtimestamp(start, tz=timezone.utc).isoformat() == '2022-06-23T18:00:00+00:00'



@pytest.fixture()
def infinite_daily_meeting(app: Flask):
    creator = create_user('user1', password='')
    m1 = create_meeting(
        creator=creator,
        start=datetime.fromisoformat('2022-06-22T00:00+00:00'),
        end=datetime.fromisoformat('2022-06-22T23:30+00:00'),
        repeat_type=RepeatTypeEnum.daily,
    )
    return m1


@pytest.mark.timeout(10)
def test_find_first_free_window_among_meetings_no_window(infinite_daily_meeting):
    start = find_first_free_window_among_meetings(
        meetings=[infinite_daily_meeting],
        window_size=60*60,
        start=datetime.fromisoformat('2022-06-22T17:00+00:00'),
    )
    assert start is None
