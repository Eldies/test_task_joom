# -*- coding: utf-8 -*-
from flask import Flask
import pytest

from app import (
    create_app,
    db,
)


@pytest.fixture()
def app() -> Flask:
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    context = app.app_context()
    context.__enter__()
    db.create_all()
    yield app
    context.__exit__(None, None, None)
