# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import db
from app.db_actions import get_user_by_name
from app.exceptions import NotFoundException
from app.models import User


@pytest.fixture(autouse=True)
def init_db(app: Flask) -> None:
    db.create_all()
    db.session.add(User(name='existing_username'))
    db.session.commit()


def test_ok():
    user = get_user_by_name('existing_username')
    assert user is not None
    assert user.name == 'existing_username'


def test_not_existing_user():
    with pytest.raises(NotFoundException) as excinfo:
        get_user_by_name('not_existing_username')
    assert excinfo.value.code == 404
    assert excinfo.value.args == ('User "not_existing_username" does not exist',)
