# -*- coding: utf-8 -*-
from pydantic import ValidationError
import pytest

from app.db_actions import (
    create_user,
    get_user_by_name,
)
from app.exceptions import NotFoundException
from app.forms import UsersModel

from unittest.mock import (
    Mock,
    patch,
)


class TestUsersModel:
    @pytest.mark.parametrize('username', [
        'aa',
        'a' * 30,
        'qwertQWERTY23456_',
    ])
    def test_ok(self, username):
        form = UsersModel(username=username)
        assert form.username == username

    @pytest.mark.parametrize('username,msg', [
        (None, 'none is not an allowed value'),
        ('', 'ensure this value has at least 2 characters'),
        ('a', 'ensure this value has at least 2 characters'),
        ('a' * 31, 'ensure this value has at most 30 characters'),
        ('a b', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        ('1ab', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
    ])
    def test_not_ok(self, username, msg):
        with pytest.raises(ValidationError) as excinfo:
            UsersModel(username=username)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == ('username',)
        assert excinfo.value.errors()[0]['msg'] == msg


class TestUsersPostView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        self.client = app.test_client()

    def test_ok(self):
        with pytest.raises(NotFoundException):
            get_user_by_name('bar')
        response = self.client.post('/users', data=dict(username='bar'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        assert get_user_by_name('bar') is not None

    def test_validates_input(self):
        with patch('app.forms.UsersModel', Mock(wraps=UsersModel)) as mock:
            form = dict(username='bar')
            self.client.post('/users', data=form)
            assert mock.call_count == 1
            assert mock.call_args.kwargs == form

    def test_username_already_exists(self):
        create_user(name='foo')
        response = self.client.post('/users', data=dict(username='foo'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'user already exists'}
