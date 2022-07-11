# -*- coding: utf-8 -*-
import pytest
from unittest.mock import (
    Mock,
    patch,
)

from app.db_actions import (
    create_user,
    get_user_by_name,
)
from app.exceptions import NotFoundException
from app.forms import UsersModel


class TestUsersPostView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.client = client

    def test_ok(self):
        with pytest.raises(NotFoundException):
            get_user_by_name('bar')
        response = self.client.post('/users', json=dict(username='bar', password='foo'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        user = get_user_by_name('bar')
        assert user.name == 'bar'
        assert user.password == 'foo'

    def test_validates_input(self):
        with patch('app.forms.UsersModel', Mock(wraps=UsersModel)) as mock:
            response = self.client.post('/users', json=dict(foo='bar'))
        assert mock.call_count == 1
        assert mock.call_args.kwargs == dict(foo='bar')
        assert response.json == {
            'status': 'error',
            'error': {
                'username': ['field required'],
                'password': ['field required'],
            },
        }

    def test_username_already_exists(self):
        create_user(name='foo', password='')
        response = self.client.post('/users', json=dict(username='foo', password='bar'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'user already exists'}
