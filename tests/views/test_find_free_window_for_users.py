# -*- coding: utf-8 -*-
from datetime import datetime
from flask import Flask

import pytest
from unittest.mock import (
    Mock,
    patch,
)

from app.db_actions import (
    create_meeting,
    create_user,
)
from app.forms import FindFreeWindowForUsersModel
from app.types import RepeatTypeEnum


@pytest.fixture(autouse=True)
def many_meetings(app: Flask):
    creator1 = create_user('creator1', password='')
    creator2 = create_user('creator2', password='')
    creator3 = create_user('creator3', password='')
    return [
        create_meeting(
            creator=creator1,
            start=datetime.fromisoformat('2022-06-22T12:00+00:00'),
            end=datetime.fromisoformat('2022-06-22T13:00+00:00'),
        ),
        create_meeting(
            creator=creator1,
            start=datetime.fromisoformat('2022-06-22T12:00+00:00'),
            end=datetime.fromisoformat('2022-06-22T15:00+00:00'),
        ),
        create_meeting(
            creator=creator2,
            start=datetime.fromisoformat('2022-06-22T15:30+00:00'),
            end=datetime.fromisoformat('2022-06-22T17:00+00:00'),
        ),
        create_meeting(
            creator=creator2,
            start=datetime.fromisoformat('2022-06-22T18:00+00:00'),
            end=datetime.fromisoformat('2022-06-22T19:00+00:00'),
        ),
        create_meeting(
            creator=creator3,
            start=datetime.fromisoformat('2022-06-22T00:00+00:00'),
            end=datetime.fromisoformat('2022-06-22T23:30+00:00'),
            repeat_type=RepeatTypeEnum.daily,
        ),
    ]


class TestFindFreeWindowForUsersView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.client = client

    def test_ok_before_all_meetings(self):
        response = self.client.get(
            'find_free_window_for_users',
            query_string={
                'usernames': 'creator2',
                'window_size': 60*60,
                'start': '2022-06-22T11:00+00:00'
            })
        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'window': {
                'start': '2022-06-22T11:00:00+00:00',
                'end': '2022-06-22T12:00:00+00:00',
            }
        }

    def test_ok_after_all_meetings(self):
        response = self.client.get(
            'find_free_window_for_users',
            query_string={
                'usernames': 'creator1',
                'window_size': 2*60*60,
                'start': '2022-06-22T11:00+00:00'
            })
        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'window': {
                'start': '2022-06-22T15:00:00+00:00',
                'end': '2022-06-22T17:00:00+00:00',
            }
        }

    def test_ok_between_meetings(self):
        response = self.client.get(
            'find_free_window_for_users',
            query_string={
                'usernames': 'creator1,creator2',
                'window_size': 60*60,
                'start': '2022-06-22T11:30+00:00'
            })
        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'window': {
                'start': '2022-06-22T17:00:00+00:00',
                'end': '2022-06-22T18:00:00+00:00',
            }
        }

    def test_validates_input(self):
        with patch('app.forms.FindFreeWindowForUsersModel', Mock(wraps=FindFreeWindowForUsersModel)) as mock:
            response = self.client.get('find_free_window_for_users', query_string=dict(foo='bar'))
        assert mock.call_count == 1
        assert mock.call_args.kwargs == dict(foo='bar')
        assert response.json == {
            'status': 'error',
            'error': {
                'start': ['field required'],
                'usernames': ['field required'],
                'window_size': ['field required'],
            },
        }

    def test_no_window(self):
        response = self.client.get(
            'find_free_window_for_users',
            query_string={
                'usernames': 'creator3',
                'window_size': 60*60,
                'start': '2022-06-22T11:30+00:00'
            })
        assert response.status_code == 404
        assert response.json == {'error': 'Impossible to find window for meeting', 'status': 'error'}
