# -*- coding: utf-8 -*-
from app import create_app


def test_create_app():
    assert create_app().testing is False
    assert create_app({'TESTING': True}).testing is True
