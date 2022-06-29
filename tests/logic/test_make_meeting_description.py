# -*- coding: utf-8 -*-
from flask import Flask

import pytest

from app.db_actions import (
    create_meeting,
    create_user,
    get_user_by_name,
    set_answer_for_invitation,
)
from app.logic import make_meeting_description
from app.models import Meeting


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
