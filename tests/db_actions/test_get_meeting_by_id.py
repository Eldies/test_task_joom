# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import db
from app.db_actions import (
    create_user,
    create_meeting,
    get_meeting_by_id,
)
from app.exceptions import NotFoundException
from app.models import Meeting


@pytest.fixture()
def meeting_id(app: Flask) -> int:
    meeting = create_meeting(
        creator=create_user('creator', password=''),
        start=1000,
        end=2000,
        description='DESC',
        invitees=[],
    )
    return meeting.id


def test_ok(meeting_id: int):
    meeting = get_meeting_by_id(meeting_id)
    assert meeting == db.session.query(Meeting).first()


@pytest.mark.usefixtures('app')
def test_not_existing_meeting():
    with pytest.raises(NotFoundException) as excinfo:
        get_meeting_by_id(9999)
    assert excinfo.value.code == 404
    assert excinfo.value.args == ('Meeting with id "9999" does not exist',)
