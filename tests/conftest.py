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


@pytest.fixture(autouse=True)
def mock_password_hashing(monkeypatch, request):
    if 'no_mock_password_hashing' in request.keywords:
        return
    monkeypatch.setattr('app.models.User.generate_password_hash', lambda p: p)
    monkeypatch.setattr('app.models.User.check_password', lambda self, p: self.password_hash == p)
