# -*- coding: utf-8 -*-
from datetime import datetime
from flask import Flask
import pytest

from app import db
from app.db_actions import (
    create_user,
    create_meeting,
    get_user_by_name,
)
from app.logic import RepeatTypeEnum
from app.models import (
    Invitation,
    Meeting,
)


@pytest.fixture(autouse=True)
def init_db(app: Flask) -> None:
    create_user('creator')
    create_user('user1')
    create_user('user2')
    create_user('user3')


def test_ok():
    assert db.session.query(Meeting).count() == 0
    assert db.session.query(Invitation).count() == 0

    invitees = [get_user_by_name('user1'), get_user_by_name('user2')]
    meeting = create_meeting(
        creator=get_user_by_name('creator'),
        start=1000,
        end=2000,
        invitees=invitees,
    )
    assert db.session.query(Meeting).count() == 1
    assert db.session.query(Invitation).count() == 2
    assert meeting == db.session.query(Meeting).first()
    assert meeting.creator.name == 'creator'
    assert meeting.start == 1000
    assert meeting.end == 2000
    assert len(meeting.invitations) == 2
    for invitee in invitees:
        invitation = db.session.query(Invitation).filter_by(invitee=invitee, meeting=meeting).first()
        assert invitation is not None
        assert invitation.answer is None


def test_ok_w_description_wo_invitees():
    meeting = create_meeting(
        creator=get_user_by_name('creator'),
        start=1000,
        end=2000,
        description='DESC',
    )
    assert meeting == db.session.query(Meeting).first()
    assert meeting.description == 'DESC'
    assert len(meeting.invitations) == 0


def test_ok_w_repeat_type():
    meeting = create_meeting(
        creator=get_user_by_name('creator'),
        start=1000,
        end=2000,
        repeat_type=RepeatTypeEnum.daily,
    )
    assert meeting == db.session.query(Meeting).first()
    assert meeting.repeat_type == 'daily'


def test_ok_w_datetimes():
    meeting = create_meeting(
        creator=get_user_by_name('creator'),
        start=datetime.fromisoformat('2022-06-22T17:00+00:00'),
        end=datetime.fromisoformat('2022-06-22T18:00-04:00'),
    )
    assert meeting == db.session.query(Meeting).first()
    assert len(meeting.invitations) == 0
    assert meeting.start == 1655917200
    assert meeting.start_datetime.isoformat() == '2022-06-22T17:00:00+00:00'
    assert meeting.end == 1655935200
    assert meeting.end_datetime.isoformat() == '2022-06-22T22:00:00+00:00'


def test_fails_if_start_wo_tz_info():
    with pytest.raises(AssertionError):
        create_meeting(
            creator=get_user_by_name('creator'),
            start=datetime.fromisoformat('2022-06-22T17:00'),
            end=2000,
        )


def test_fails_if_end_wo_tz_info():
    with pytest.raises(AssertionError):
        create_meeting(
            creator=get_user_by_name('creator'),
            start=2000,
            end=datetime.fromisoformat('2022-06-22T17:00'),
        )
