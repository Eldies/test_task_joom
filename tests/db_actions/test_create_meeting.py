# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import db
from app.db_actions import (
    create_user,
    create_meeting,
    get_user_by_name,
)
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
        description='DESC',
        invitees=invitees,
    )
    assert db.session.query(Meeting).count() == 1
    assert db.session.query(Invitation).count() == 2
    assert meeting == db.session.query(Meeting).first()
    assert meeting.creator.name == 'creator'
    assert meeting.start == 1000
    assert meeting.end == 2000
    assert meeting.description == 'DESC'
    for invitee in invitees:
        invitation = db.session.query(Invitation).filter_by(invitee=invitee, meeting=meeting).first()
        assert invitation is not None
        assert invitation.answer is None
