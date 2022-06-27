# -*- coding: utf-8 -*-
from pydantic import ValidationError

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


class TestAnswerInvitationModel:
    @pytest.mark.parametrize('form', [
        dict(username='aa', meeting_id=1, answer=True),
        dict(username='a' * 30, meeting_id='1', answer='true'),
        dict(username='qwertQWERTY23456_', meeting_id=1, answer='false'),
    ])
    def test_ok(self, form):
        form = AnswerInvitationModel(**form)
        assert form.dict() == form

    @pytest.mark.parametrize('form,loc,msg', [
        (dict(username='', meeting_id=1, answer=True), ('username',), 'ensure this value has at least 2 characters'),
        (dict(meeting_id=1, answer=True), ('username',), 'field required'),
        (dict(username='a' * 31, meeting_id=1, answer='true'), ('username',), 'ensure this value has at most 30 characters'),
        (dict(username='a b', meeting_id=1, answer='true'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(username='1a', meeting_id=1, answer='true'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(username='aa', meeting_id='ddd', answer='false'), ('meeting_id',), 'value is not a valid integer'),
        (dict(username='aa', answer='false'), ('meeting_id',), 'field required'),
        (dict(username='aa', meeting_id=1, answer='scooters'), ('answer',), 'value could not be parsed to a boolean'),
        (dict(username='aa', meeting_id=1), ('answer',), 'field required'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            AnswerInvitationModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg


class TestAnswerInvitationView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        db.session.commit()
        db.session.expire_on_commit = False
        self.creator = create_user(name='creator')
        self.invited_user = create_user(name='user1')
        self.not_invited_user = create_user(name='user2')
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

        self.client = app.test_client()

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
            form = dict(foo='bar')
            self.client.post('/invitations', data=form)
            assert mock.call_count == 1
            assert mock.call_args.kwargs == form

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
