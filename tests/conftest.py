# -*- coding: utf-8 -*-
from flask import Flask
from flask.testing import FlaskClient
import pytest

from app import create_app


@pytest.fixture()
def app() -> Flask:
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
    })
    with app.app_context():
        yield app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
