# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)

import pytest
from unittest.mock import (
    Mock,
    patch,
)

from app import db
from app.db_actions import (
    create_meeting,
    create_user,
    get_meeting_by_id,
    set_answer_for_invitation,
)
from app.exceptions import NotFoundException
from app.forms import MeetingsModel

from tests.utils import (
    make_auth_header,
    make_headers,
)


class TestMeetingsPostView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        creator = create_user(name='creator', password='foo')
        create_user(name='invitee1', password='')
        create_user(name='invitee2', password='')

        self.client = client

        self.default_args = dict(
            creator_username='creator',
            start='2022-06-22T19:00:00+01:00',
            end='2022-06-22T20:00:00-03:00',
        )
        self.headers = make_headers(creator)

    def test_ok(self):
        with pytest.raises(NotFoundException):
            get_meeting_by_id(1)

        response = self.client.post('/meetings', data=self.default_args, headers=self.headers)

        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        meeting = get_meeting_by_id(1)
        assert meeting.id == 1
        assert meeting.creator.name == 'creator'
        assert meeting.start == datetime(2022, 6, 22, 18, 0, tzinfo=timezone.utc).timestamp()
        assert meeting.end == datetime(2022, 6, 22, 23, 0, tzinfo=timezone.utc).timestamp()
        assert meeting.description is None
        assert meeting.invitations == []
        assert meeting.repeat_type == 'none'
        assert meeting.is_private is False

    def test_not_authenticated(self):
        response = self.client.post('/meetings', data=self.default_args)
        assert response.status_code == 401
        assert response.json == {'status': 'error', 'error': 'Not authenticated'}

    def test_authenticated_as_wrong_user(self):
        wrong_user = create_user('wrong_user', 'bar')
        response = self.client.post('/meetings', data=self.default_args, headers=make_headers(wrong_user))
        assert response.status_code == 403
        assert response.json == {'status': 'error', 'error': 'Wrong user'}

    def test_authenticated_with_wrong_password(self):
        response = self.client.post('/meetings', data=self.default_args, headers={
            'Authorization': make_auth_header('creator', 'some_random_string')
        })
        assert response.status_code == 403
        assert response.json == {'status': 'error', 'error': 'Wrong password'}

    def test_validates_input(self):
        with patch('app.forms.MeetingsModel', Mock(wraps=MeetingsModel)) as mock:
            response = self.client.post('/meetings', data=dict(foo='bar'))
        assert mock.call_count == 1
        assert mock.call_args.kwargs == dict(foo='bar')
        assert response.json == {
            'status': 'error',
            'error': {
                'creator_username': ['field required'],
                'end': ['field required'],
                'start': ['field required'],
            },
        }

    def test_ok_tz_naive_dates_treated_as_utc_dates(self):
        response = self.client.post(
            '/meetings',
            data=dict(
                self.default_args,
                start='2022-06-22T19:00:00',
                end='2022-06-22T20:00:00',
            ),
            headers=self.headers,
        )
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        assert get_meeting_by_id(1).start == int(datetime(2022, 6, 22, 19, 0, tzinfo=timezone.utc).timestamp())
        assert get_meeting_by_id(1).end == int(datetime(2022, 6, 22, 20, 0, tzinfo=timezone.utc).timestamp())

    def test_ok_with_description(self):
        response = self.client.post('/meetings', data=dict(self.default_args, description='desc'), headers=self.headers)
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        assert get_meeting_by_id(1).description == 'desc'

    def test_ok_with_repeat_type(self):
        response = self.client.post('/meetings', data=dict(self.default_args, repeat_type='daily'), headers=self.headers)
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        assert get_meeting_by_id(1).repeat_type == 'daily'

    def test_nonexistent_username(self):
        response = self.client.post('/meetings', data=dict(self.default_args, creator_username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "FOO" does not exist'}

    def test_ok_with_invitees(self):
        response = self.client.post('/meetings', data=dict(self.default_args, invitees='invitee1,invitee2'), headers=self.headers)
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        meeting = get_meeting_by_id(1)
        assert len(meeting.invitations) == 2
        for invitation in meeting.invitations:
            assert invitation.meeting_id == meeting.id
            assert invitation.invitee.name in ('invitee1', 'invitee2')
            assert invitation.answer is None

    def test_with_nonexistent_invitee(self):
        response = self.client.post('/meetings', data=dict(self.default_args, invitees='invitee1,nonexistent_invitee'), headers=self.headers)
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "nonexistent_invitee" does not exist'}

    def test_ok_with_is_private(self):
        response = self.client.post('/meetings', data=dict(self.default_args, is_private='true'), headers=self.headers)
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        meeting = get_meeting_by_id(1)
        assert meeting.is_private is True


class TestMeetingsGetView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        self.start = datetime.fromisoformat('2022-06-22T19:00:00+00:00')
        self.end = datetime.fromisoformat('2022-06-22T20:00:00+00:00')
        db.create_all()

        self.creator = create_user(name='creator', password='foo')
        user1 = create_user(name='inv1', password='')
        user2 = create_user(name='inv2', password='')
        user3 = create_user(name='inv3', password='')
        meeting = create_meeting(
            creator=self.creator,
            start=int(self.start.timestamp()),
            end=int(self.end.timestamp()),
            description='DESCRIPTION',
            invitees=[user1, user2, user3],
            is_private=True,
        )
        set_answer_for_invitation(user2, meeting, True)
        set_answer_for_invitation(user3, meeting, False)

        self.meeting_id = meeting.id

        self.client = app.test_client()

    def test_ok(self):
        response = self.client.get('/meetings/{}'.format(self.meeting_id), headers=make_headers(self.creator))

        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meeting_description': {
                'id': 1,
                'creator': 'creator',
                'description': 'DESCRIPTION',
                'start_datetime': self.start.isoformat(),
                'end_datetime': self.end.isoformat(),
                'repeat_type': 'none',
                'is_private': True,
                'invitees': [
                    {'accepted_invitation': None, 'username': 'inv1'},
                    {'accepted_invitation': True, 'username': 'inv2'},
                    {'accepted_invitation': False, 'username': 'inv3'},
                ],
            },
        }

    def test_string_meeting_id(self):
        response = self.client.get('/meetings/aaaaaa')
        assert response.status_code == 404
        assert response.json == {
            'status': 'error',
            'error':
                'The requested URL was not found on the server.'
                ' If you entered the URL manually please check your spelling and try again.',
        }

    def test_nonexistent_meeting(self):
        response = self.client.get('/meetings/9999')
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'Meeting with id "9999" does not exist'}

    def test_ok_private_meeting_wo_auth(self):
        response = self.client.get('/meetings/{}'.format(self.meeting_id))

        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meeting_description': {
                'id': 1,
                'start_datetime': self.start.isoformat(),
                'end_datetime': self.end.isoformat(),
            },
        }
