# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import db
from app.db_actions import create_user
from app.exceptions import AlreadyExistsException
from app.models import User


@pytest.fixture(autouse=True)
def init_db(app: Flask) -> None:
    db.session.add(User(name='existing_username', password=''))
    db.session.commit()


def test_ok():
    assert db.session.query(User).filter_by(name='not_existing_username').first() is None
    user = create_user('not_existing_username', password='foo')
    assert user == db.session.query(User).filter_by(name='not_existing_username').first()
    assert user is not None
    assert user.name == 'not_existing_username'
    assert user.password == 'foo'


def test_existing_user():
    with pytest.raises(AlreadyExistsException) as excinfo:
        create_user('existing_username', password='')
    assert excinfo.value.code == 400
    assert excinfo.value.args == ('user already exists',)
