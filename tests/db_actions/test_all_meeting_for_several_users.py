# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app.db_actions import (
    create_user,
    create_meeting,
    get_user_by_name,
    get_all_meetings_for_several_users,
)


@pytest.fixture(autouse=True)
def prepare(app: Flask):
    user1 = create_user('user1')
    user2 = create_user('user2')
    user3 = create_user('user3')
    user4 = create_user('user4')

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
    meetings = get_all_meetings_for_several_users(users=[
        get_user_by_name('user1'),
    ])
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 2
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000


def test_user2():
    meetings = get_all_meetings_for_several_users(users=[
        get_user_by_name('user2'),
    ])
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 3
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000
    assert meetings[2].start == 4000


def test_user4():
    meetings = get_all_meetings_for_several_users(users=[
        get_user_by_name('user4'),
    ])
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 2
    assert meetings[0].start == 3000
    assert meetings[1].start == 4000


def test_user2_user4():
    meetings = get_all_meetings_for_several_users(users=[
        get_user_by_name('user2'),
        get_user_by_name('user4'),
    ])
    meetings.sort(key=lambda m: m.start)
    assert len(meetings) == 4
    assert meetings[0].start == 1000
    assert meetings[1].start == 2000
    assert meetings[2].start == 3000
    assert meetings[3].start == 4000
