# -*- coding: utf-8 -*-
from flask import Flask

import pytest

from app.db_actions import (
    create_meeting,
    create_user,
    set_answer_for_invitation,
)
from app.logic import make_meeting_description
from app.models import Meeting


@pytest.fixture()
def meeting(app: Flask):
    creator = create_user('creator')
    user1 = create_user('user1')
    user2 = create_user('user2')
    user3 = create_user('user3')

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
        'invitees': [
            {'accepted_invitation': None, 'username': 'user1'},
            {'accepted_invitation': True, 'username': 'user2'},
            {'accepted_invitation': False, 'username': 'user3'},
        ],
    }