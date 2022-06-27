# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import db
from app.db_actions import create_user
from app.exceptions import AlreadyExistsException
from app.models import User


@pytest.fixture(autouse=True)
def init_db(app: Flask) -> None:
    db.create_all()
    db.session.add(User(name='existing_username'))
    db.session.commit()


def test_ok():
    assert db.session.query(User).filter_by(name='not_existing_username').first() is None
    created_user = create_user('not_existing_username')
    found_user = db.session.query(User).filter_by(name='not_existing_username').first()
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.name == created_user.name
    assert found_user.name == 'not_existing_username'


def test_existing_user():
    with pytest.raises(AlreadyExistsException) as excinfo:
        create_user('existing_username')
    assert excinfo.value.code == 400
    assert excinfo.value.args == ('user already exists',)
