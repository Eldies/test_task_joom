# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app.db_actions import (
    create_user,
    create_meeting,
    get_invitation,
    set_answer_for_invitation,
)
from app.exceptions import NotFoundException
from app.models import (
    Meeting,
    User,
)


@pytest.fixture()
def invited_user(app: Flask) -> User:
    return create_user('invited_user', password='')


@pytest.fixture()
def not_invited_user(app:Flask) -> User:
    return create_user('not_invited_user', password='')


@pytest.fixture()
def meeting(app: Flask, invited_user) -> Meeting:
    return create_meeting(
        creator=create_user('creator', password=''),
        start=1000,
        end=2000,
        description='DESC',
        invitees=[invited_user],
    )


@pytest.mark.parametrize('answer', [True, False])
def test_ok(meeting: Meeting, invited_user: User, answer: bool):
    assert get_invitation(invitee=invited_user, meeting=meeting).answer is None
    set_answer_for_invitation(invitee=invited_user, meeting=meeting, answer=answer)
    assert get_invitation(invitee=invited_user, meeting=meeting).answer is answer


def test_not_invited_user(meeting: Meeting, not_invited_user: User):
    with pytest.raises(NotFoundException) as excinfo:
        set_answer_for_invitation(invitee=not_invited_user, meeting=meeting, answer=True)
    assert excinfo.value.code == 404
    assert excinfo.value.args == ('User was not invited to this meeting',)
