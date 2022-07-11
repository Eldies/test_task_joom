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
    get_user_by_name,
)
from app.forms import UserMeetingsForRangeModel

from tests.utils import make_headers


@pytest.fixture(autouse=True)
def prepare(app: Flask):
    user1 = create_user('user1', password='')
    user2 = create_user('user2', password='')
    user3 = create_user('user3', password='')

    create_meeting(
        creator=user1,
        start=int(datetime.fromisoformat('2022-06-22T15:00+00:00').timestamp()),
        end=int(datetime.fromisoformat('2022-06-22T16:00+00:00').timestamp()),
        invitees=[user2, user3],
    )
    create_meeting(
        creator=user2,
        start=int(datetime.fromisoformat('2022-06-22T17:00+00:00').timestamp()),
        end=int(datetime.fromisoformat('2022-06-22T18:00+00:00').timestamp()),
        invitees=[user1],
        is_private=True,
    )
    create_meeting(
        creator=user3,
        start=int(datetime.fromisoformat('2022-06-22T19:00+00:00').timestamp()),
        end=int(datetime.fromisoformat('2022-06-22T20:00+00:00').timestamp()),
        invitees=[user2],
    )


class TestUserMeetingsForRangeView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.client = client

    def test_ok_all(self):
        response = self.client.get(
            '/users/user1/meetings',
            query_string={
                'start': '2022-06-22T14:00+00:00',
                'end': '2022-06-22T22:00+00:00',
            },
            headers=make_headers(name='user1', password=''),
        )
        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meetings': [
                {
                    'creator': 'user1',
                    'description': None,
                    'start_datetime': '2022-06-22T15:00:00+00:00',
                    'end_datetime': '2022-06-22T16:00:00+00:00',
                    'id': 1,
                    'repeat_type': 'none',
                    'is_private': False,
                    'invitees': [
                        {'accepted_invitation': None, 'username': 'user2'},
                        {'accepted_invitation': None, 'username': 'user3'},
                    ],
                },
                {
                    'creator': 'user2',
                    'description': None,
                    'start_datetime': '2022-06-22T17:00:00+00:00',
                    'end_datetime': '2022-06-22T18:00:00+00:00',
                    'id': 2,
                    'repeat_type': 'none',
                    'is_private': True,
                    'invitees': [
                        {'accepted_invitation': None, 'username': 'user1'},
                    ],
                },
            ],
        }

    def test_ok_no_meetings_in_range(self):
        response = self.client.get(
            '/users/user1/meetings',
            query_string={
                'start': '2022-06-23T14:00+00:00',
                'end': '2022-06-23T22:00+00:00',
            })
        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meetings': [],
        }

    def test_validates_input(self):
        with patch('app.forms.UserMeetingsForRangeModel', Mock(wraps=UserMeetingsForRangeModel)) as mock:
            response = self.client.get('/users/111/meetings', query_string=dict(foo='bar'))
        assert mock.call_count == 1
        assert mock.call_args.kwargs == dict(foo='bar', username='111')
        assert response.json == {
            'status': 'error',
            'error': {
                'start': ['field required'],
                'end': ['field required'],
                'username': ['string does not match regex "^[a-zA-Z_]\\w*$"'],
            },
        }

    def test_ok_wo_auth(self):
        response = self.client.get(
            '/users/user1/meetings',
            query_string={
                'start': '2022-06-22T14:00+00:00',
                'end': '2022-06-22T22:00+00:00',
            },
        )
        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meetings': [
                {
                    'creator': 'user1',
                    'description': None,
                    'start_datetime': '2022-06-22T15:00:00+00:00',
                    'end_datetime': '2022-06-22T16:00:00+00:00',
                    'id': 1,
                    'repeat_type': 'none',
                    'is_private': False,
                    'invitees': [
                        {'accepted_invitation': None, 'username': 'user2'},
                        {'accepted_invitation': None, 'username': 'user3'},
                    ],
                },
                {
                    'start_datetime': '2022-06-22T17:00:00+00:00',
                    'end_datetime': '2022-06-22T18:00:00+00:00',
                    'id': 2,
                },
            ],
        }

