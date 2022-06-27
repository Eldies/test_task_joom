# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import (
    create_app,
    db,
)
from app.db_actions import create_user
from app.exceptions import AlreadyExistsException
from app.models import User


@pytest.fixture()
def app() -> Flask:
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    context = app.app_context()
    context.__enter__()
    yield app
    context.__exit__(None, None, None)


@pytest.fixture(autouse=True)
def init_db(app: Flask) -> None:
    db.create_all()
    db.session.add(User(name='existing_username'))
    db.session.commit()


def test_ok():
    assert db.session.query(User).filter_by(name='not_existing_username').first() is None
    create_user('not_existing_username')
    assert db.session.query(User).filter_by(name='not_existing_username').first() is not None


def test_existing_user():
    with pytest.raises(AlreadyExistsException) as excinfo:
        create_user('existing_username')
    assert excinfo.value.code == 400
    assert excinfo.value.args == ('user already exists',)
