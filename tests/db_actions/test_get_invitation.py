# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import db
from app.db_actions import (
    create_user,
    create_meeting,
    get_invitation,
)
from app.exceptions import NotFoundException
from app.models import (
    Invitation,
    Meeting,
    User,
)


@pytest.fixture()
def invited_user(app: Flask) -> User:
    return create_user('invited_user')


@pytest.fixture()
def not_invited_user(app:Flask) -> User:
    return create_user('not_invited_user')


@pytest.fixture()
def meeting(app: Flask, invited_user) -> Meeting:
    return create_meeting(
        creator=create_user('creator'),
        start=1000,
        end=2000,
        description='DESC',
        invitees=[invited_user],
    )


def test_ok(meeting: Meeting, invited_user: User):
    invitation = get_invitation(invited_user, meeting)
    assert invitation == db.session.query(Invitation).filter_by(invitee=invited_user, meeting=meeting).first()


def test_not_invited_user(meeting: Meeting, not_invited_user: User):
    with pytest.raises(NotFoundException) as excinfo:
        get_invitation(not_invited_user, meeting)
    assert excinfo.value.code == 404
    assert excinfo.value.args == ('User was not invited to this meeting',)
