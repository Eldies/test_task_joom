# -*- coding: utf-8 -*-
import pytest
from unittest.mock import (
    Mock,
    patch,
)

from app import db
from app.db_actions import (
    create_meeting,
    create_user,
    get_invitation,
)
from app.forms import AnswerInvitationModel

from tests.utils import (
    make_auth_header,
    make_headers,
)

class TestAnswerInvitationView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        db.session.commit()
        db.session.expire_on_commit = False
        self.creator = create_user(name='creator', password='')
        self.invited_user = create_user(name='invited_user', password='')
        self.not_invited_user = create_user(name='not_invited_user', password='')
        self.meeting = create_meeting(
            creator=self.creator,
            start=1000,
            end=2000,
            description='desc',
            invitees=[self.invited_user],
        )

        self.default_args = dict(
            username=self.invited_user.name,
            meeting_id=self.meeting.id,
            answer='true',
        )

        self.client = client

    def test_not_authenticated(self):
        response = self.client.post(
            '/invitations',
            json=self.default_args,
        )
        assert response.status_code == 401
        assert response.json == {'status': 'error', 'error': 'Not authenticated'}

    def test_authenticated_as_wrong_user(self):
        create_user('wrong_user', 'bar')
        response = self.client.post(
            '/invitations',
            json=self.default_args,
            headers=make_headers(name='wrong_user', password='bar'),
        )
        assert response.status_code == 403
        assert response.json == {'status': 'error', 'error': 'Wrong user'}

    def test_authenticated_with_wrong_password(self):
        response = self.client.post(
            '/invitations',
            json=self.default_args,
            headers={
                'Authorization': make_auth_header('invited_user', 'some_random_string'),
            },
        )
        assert response.status_code == 403
        assert response.json == {'status': 'error', 'error': 'Wrong password'}

    @pytest.mark.parametrize('answer', [
        True,
        False,
    ])
    def test_ok(self, answer):
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None
        response = self.client.post(
            '/invitations',
            json=dict(self.default_args, answer='true' if answer else 'false'),
            headers=make_headers(name='invited_user', password=''),
        )
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer == answer

    def test_validates_input(self):
        with patch('app.forms.AnswerInvitationModel', Mock(wraps=AnswerInvitationModel)) as mock:
            response = self.client.post('/invitations', json=dict(foo='bar'))
        assert mock.call_count == 1
        assert mock.call_args.kwargs == dict(foo='bar')
        assert response.json == {
            'status': 'error',
            'error': {
                'answer': ['field required'],
                'meeting_id': ['field required'],
                'username': ['field required'],
            },
        }

    def test_nonexistent_meeting(self):
        response = self.client.post(
            '/invitations',
            json=dict(self.default_args, meeting_id=9999),
            headers=make_headers(name='invited_user', password=''),
        )
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'Meeting with id "9999" does not exist'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None

    def test_not_invited_user(self):
        response = self.client.post(
            '/invitations',
            json=dict(self.default_args, username=self.not_invited_user.name),
            headers=make_headers(name='not_invited_user', password=''),
        )
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User was not invited to this meeting'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None

    def test_nonexistent_username(self):
        response = self.client.post('/invitations', json=dict(self.default_args, username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "FOO" does not exist'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None
