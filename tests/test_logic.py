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
    get_user_by_name,
    set_answer_for_invitation,
)
from app.logic import (
    get_repeated_timestamp,
    find_first_free_window_among_meetings,
    make_meeting_description,
    RepeatTypeEnum,
)
from app.models import Meeting


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


@pytest.fixture()
def meeting(app: Flask):
    creator = create_user('creator', password='')
    user1 = create_user('user1', password='')
    user2 = create_user('user2', password='')
    user3 = create_user('user3', password='')

    meeting = create_meeting(
        creator=creator,
        start=1000,
        end=2000,
        description='DESCRIPTION',
        invitees=[user1, user2, user3],
    )
    set_answer_for_invitation(user2, meeting, True)
    set_answer_for_invitation(user3, meeting, False)
    return meeting


def test_make_meeting_description(meeting: Meeting):
    assert make_meeting_description(meeting) == {
        'id': 1,
        'creator': 'creator',
        'description': 'DESCRIPTION',
        'start_datetime': meeting.start_datetime.isoformat(),
        'end_datetime': meeting.end_datetime.isoformat(),
        'repeat_type': 'none',
        'is_private': False,
        'invitees': [
            {'accepted_invitation': None, 'username': 'user1'},
            {'accepted_invitation': True, 'username': 'user2'},
            {'accepted_invitation': False, 'username': 'user3'},
        ],
    }


@pytest.fixture()
def private_meeting(app: Flask):
    creator = create_user('creator', password='')
    user1 = create_user('user1', password='')
    user2 = create_user('user2', password='')
    create_user('user3', password='')

    meeting = create_meeting(
        creator=creator,
        start=1000,
        end=2000,
        description='DESCRIPTION',
        invitees=[user1, user2],
        is_private=True,
    )
    set_answer_for_invitation(user2, meeting, True)
    return meeting


def test_make_meeting_description_private_creator_and_invitees(private_meeting: Meeting):
    for username in ['creator', 'user1', 'user2']:
        assert make_meeting_description(private_meeting, requester=get_user_by_name(username)) == {
            'id': 1,
            'creator': 'creator',
            'description': 'DESCRIPTION',
            'start_datetime': private_meeting.start_datetime.isoformat(),
            'end_datetime': private_meeting.end_datetime.isoformat(),
            'repeat_type': 'none',
            'is_private': True,
            'invitees': [
                {'accepted_invitation': None, 'username': 'user1'},
                {'accepted_invitation': True, 'username': 'user2'},
            ],
        }


def test_make_meeting_description_private_some_random_user(private_meeting: Meeting):
    assert make_meeting_description(private_meeting, requester=get_user_by_name('user3')) == {
        'id': 1,
        'start_datetime': private_meeting.start_datetime.isoformat(),
        'end_datetime': private_meeting.end_datetime.isoformat(),
    }


def test_make_meeting_description_private_requester_unknown(private_meeting: Meeting):
    assert make_meeting_description(private_meeting) == {
        'id': 1,
        'start_datetime': private_meeting.start_datetime.isoformat(),
        'end_datetime': private_meeting.end_datetime.isoformat(),
    }


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
