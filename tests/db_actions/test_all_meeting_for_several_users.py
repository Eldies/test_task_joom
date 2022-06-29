# -*- coding: utf-8 -*-
from datetime import datetime
from flask import Flask
import pytest

from app.db_actions import (
    create_user,
    create_meeting,
    get_all_meetings_for_several_users,
    get_meeting_by_id,
    get_user_by_name,
    set_answer_for_invitation,
)
from app.logic import RepeatTypeEnum


@pytest.fixture(autouse=True)
def prepare(app: Flask):
    user1 = create_user('user1', password='')
    user2 = create_user('user2', password='')
    user3 = create_user('user3', password='')
    user4 = create_user('user4', password='')

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
        invitees=[user4],
    )
    create_meeting(
        creator=user4,
        start=4000,
        end=5000,
        invitees=[user2],
    )


def test_user1():
    meetings = get_all_meetings_for_several_users(
        users=[
            get_user_by_name('user1'),
        ],
        start=0,
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 2
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000


def test_user2():
    meetings = get_all_meetings_for_several_users(
        users=[
            get_user_by_name('user2'),
        ],
        start=0,
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 3
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000
    assert meetings[2].start == 4000


def test_user4():
    meetings = get_all_meetings_for_several_users(
        users=[
            get_user_by_name('user4'),
        ],
        start=0,
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 2
    assert meetings[0].start == 3000
    assert meetings[1].start == 4000


def test_user2_user4():
    meetings = get_all_meetings_for_several_users(
        users=[
            get_user_by_name('user2'),
            get_user_by_name('user4'),
        ],
        start=0,
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 4
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000
    assert meetings[2].start == 3000
    assert meetings[3].start == 4000


def test_user1_invitation_declined():
    set_answer_for_invitation(get_user_by_name('user1'), get_meeting_by_id(2), False)
    meetings = get_all_meetings_for_several_users(
        users=[
            get_user_by_name('user1'),
        ],
        start=0,
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 1
    assert meetings[0].start == 1000


def test_user1_first_meeting_already_ended():
    meetings = get_all_meetings_for_several_users(
        users=[
            get_user_by_name('user1'),
        ],
        start=2100,
    )
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 1
    assert meetings[0].start == 2000


@pytest.fixture()
def daily_meeting(app: Flask):
    return create_meeting(
        creator=create_user('user55', password=''),
        start=datetime.fromisoformat('2022-06-22T17:00+00:00'),
        end=datetime.fromisoformat('2022-06-22T18:00+00:00'),
        repeat_type=RepeatTypeEnum.daily,
    )


def test_daily_meeting_before_it(daily_meeting):
    meetings = get_all_meetings_for_several_users(
        users=[get_user_by_name('user55')],
        start=datetime.fromisoformat('2022-01-01T00:00+00:00'),
    )
    assert len(meetings) == 1
    assert meetings[0].start_datetime.isoformat() == '2022-06-22T17:00:00+00:00'


def test_daily_meeting_after_it(daily_meeting):
    meetings = get_all_meetings_for_several_users(
        users=[get_user_by_name('user55')],
        start=datetime.fromisoformat('2023-01-01T00:00+00:00'),
    )
    assert len(meetings) == 1
    assert meetings[0].start_datetime.isoformat() == '2022-06-22T17:00:00+00:00'
