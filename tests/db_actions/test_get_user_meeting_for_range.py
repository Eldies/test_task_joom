# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app.db_actions import (
    create_user,
    create_meeting,
    get_user_by_name,
    get_user_meetings_for_range,
)


@pytest.fixture(autouse=True)
def prepare(app: Flask):
    user1 = create_user('user1')
    user2 = create_user('user2')
    user3 = create_user('user3')

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


def test_all():
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=0, end=5000)
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 2
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000


def test_only_first():
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=0, end=1500)
    assert len(meetings) == 1
    assert meetings[0].start == 1000


def test_only_second():
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=2500, end=5000)
    assert len(meetings) == 1
    assert meetings[0].start == 2000


def test_range_is_before_meetings():
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=0, end=500)
    assert len(meetings) == 0


def test_range_is_after_meetings():
    meetings = get_user_meetings_for_range(user=get_user_by_name('user1'), start=4500, end=5000)
    assert len(meetings) == 0
