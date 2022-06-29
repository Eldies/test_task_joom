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


class TestAnswerInvitationView:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        db.session.commit()
        db.session.expire_on_commit = False
        self.creator = create_user(name='creator', password='')
        self.invited_user = create_user(name='user1', password='')
        self.not_invited_user = create_user(name='user2', password='')
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

    @pytest.mark.parametrize('answer', [
        True,
        False,
    ])
    def test_ok(self, answer):
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None
        response = self.client.post('/invitations', data=dict(self.default_args, answer='true' if answer else 'false'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer == answer

    def test_validates_input(self):
        with patch('app.forms.AnswerInvitationModel', Mock(wraps=AnswerInvitationModel)) as mock:
            response = self.client.post('/invitations', data=dict(foo='bar'))
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
        response = self.client.post('/invitations', data=dict(self.default_args, meeting_id=9999))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'Meeting with id "9999" does not exist'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None

    def test_not_invited_user(self):
        response = self.client.post('/invitations', data=dict(self.default_args, username=self.not_invited_user.name))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User was not invited to this meeting'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None

    def test_nonexistent_username(self):
        response = self.client.post('/invitations', data=dict(self.default_args, username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "FOO" does not exist'}
        assert get_invitation(invitee=self.invited_user, meeting=self.meeting).answer is None
