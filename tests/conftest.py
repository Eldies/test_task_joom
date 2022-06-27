# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import (
    create_app,
    db,
)


@pytest.fixture()
def app() -> Flask:
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
    })
    with app.app_context():
        yield app
