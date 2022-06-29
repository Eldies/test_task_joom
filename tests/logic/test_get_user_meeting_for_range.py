# -*- coding: utf-8 -*-
from datetime import datetime

from flask import Flask
import pytest

from app.db_actions import (
    create_user,
    create_meeting,
    get_user_by_name,
)
from app.logic import get_user_meetings_for_range
from app.types import RepeatTypeEnum


@pytest.fixture()
def prepare(app: Flask):
    user1 = create_user('user1', password='')
    user2 = create_user('user2', password='')
    user3 = create_user('user3', password='')

    create_meeting(
        creator=user1,
        start=1000,
        end=2000,
        invitees=[user2, user3],
    )
    create_meeting(
        creator=user2,
        start=2000,
        end=3000,
        invitees=[user1],
    )
    create_meeting(
        creator=user3,
        start=3000,
        end=4000,
        invitees=[user2],
    )


def test_all(prepare):
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=0, end=5000)
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 2
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000


def test_only_first(prepare):
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=0, end=1500)
    assert len(meetings) == 1
    assert meetings[0].start == 1000


def test_only_second(prepare):
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=2500, end=5000)
    assert len(meetings) == 1
    assert meetings[0].start == 2000


def test_range_is_before_meetings(prepare):
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=0, end=500)
    assert len(meetings) == 0


def test_range_is_after_meetings(prepare):
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=4500, end=5000)
    assert len(meetings) == 0


@pytest.fixture()
def repeating_meeting(app: Flask):
    user1 = create_user('user1', password='')
    user2 = create_user('user2', password='')
    user3 = create_user('user3', password='')

    create_meeting(
        creator=user1,
        start=datetime.fromisoformat('2022-01-01T17:00+00:00'),
        end=datetime.fromisoformat('2022-01-01T18:00+00:00'),
        invitees=[user2, user3],
        repeat_type=RepeatTypeEnum.daily,
    )


def test_repeating_meeting(repeating_meeting):
    meetings = get_user_meetings_for_range(
        user=get_user_by_name('user1'),
        start=datetime.fromisoformat('2022-06-22T10:00+00:00'),
        end=datetime.fromisoformat('2022-06-25T10:00+00:00'),
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 3
    assert meetings[0].id == 1
    assert meetings[0].start_datetime.isoformat() == '2022-06-22T17:00:00+00:00'
    assert meetings[0].end_datetime.isoformat() == '2022-06-22T18:00:00+00:00'
    assert meetings[1].id == 1
    assert meetings[1].start_datetime.isoformat() == '2022-06-23T17:00:00+00:00'
    assert meetings[1].end_datetime.isoformat() == '2022-06-23T18:00:00+00:00'
    assert meetings[2].id == 1
    assert meetings[2].start_datetime.isoformat() == '2022-06-24T17:00:00+00:00'
    assert meetings[2].end_datetime.isoformat() == '2022-06-24T18:00:00+00:00'
