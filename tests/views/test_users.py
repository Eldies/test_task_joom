# -*- coding: utf-8 -*-
import pytest

from app import db
from app.db_actions import (
    create_user,
    get_user_by_name,
)
from app.exceptions import NotFoundException


class TestUsersPostView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        db.create_all()
        self.client = app.test_client()

    def test_ok(self):
        with pytest.raises(NotFoundException):
            get_user_by_name('bar')
        response = self.client.post('/users', data=dict(username='bar'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        assert get_user_by_name('bar') is not None

    @pytest.mark.parametrize('username,error', [
        (None, 'field required'),
        ('', 'ensure this value has at least 2 characters'),
        ('a', 'ensure this value has at least 2 characters'),
        ('a' * 21, 'ensure this value has at most 20 characters'),
        ('a b', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        ('1ab', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
    ])
    def test_wrong_username(self, username, error):
        response = self.client.post('/users', data=dict(username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'username': [error]}}

    def test_username_already_exists(self):
        create_user(name='foo')
        response = self.client.post('/users', data=dict(username='foo'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'user already exists'}
