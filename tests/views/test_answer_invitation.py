# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytest

from app import db
from app.models import (
    Invitation,
    Meeting,
    User,
)


class TestAnswerInvitationView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        db.create_all()
        db.session.commit()
        db.session.expire_on_commit = False
        start = datetime.fromisoformat('2022-06-22T19:00:00+00:00')
        end = datetime.fromisoformat('2022-06-22T20:00:00+00:00')
        self.creator = User(name='creator')
        self.invited_user = User(name='user1')
        self.not_invited_user = User(name='user2')
        self.meeting = Meeting(creator=self.creator, start=start.timestamp(), end=end.timestamp())
        invitation = Invitation(invitee=self.invited_user, meeting=self.meeting, answer=None)
        db.session.add_all([self.creator, self.invited_user, self.not_invited_user, self.meeting, invitation])
        db.session.commit()

        db.session.refresh(self.not_invited_user)
        db.session.refresh(self.invited_user)
        db.session.refresh(self.meeting)

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
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None
        response = self.client.post('/invitations', data=dict(self.default_args, answer='true' if answer else 'false'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer == answer

    @pytest.mark.parametrize('username,error', [
        (None, 'field required'),
        ('', 'ensure this value has at least 2 characters'),
        ('a', 'ensure this value has at least 2 characters'),
        ('a' * 21, 'ensure this value has at most 20 characters'),
        ('a b', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        ('1ab', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
    ])
    def test_wrong_username(self, username, error):
        response = self.client.post('/invitations', data=dict(self.default_args, username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'username': [error]}}
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_string_meeting_id(self):
        response = self.client.post('/invitations', data=dict(self.default_args, meeting_id='DD'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'meeting_id': ['value is not a valid integer']}}
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_nonexistent_meeting(self):
        response = self.client.post('/invitations', data=dict(self.default_args, meeting_id=9999))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User was not invited to this meeting'}
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_not_invited_user(self):
        response = self.client.post('/invitations', data=dict(self.default_args, username=self.not_invited_user.name))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User was not invited to this meeting'}
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_nonexistent_username(self):
        response = self.client.post('/invitations', data=dict(self.default_args, username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "FOO" does not exist'}
        assert db.session.query(Invitation).filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None
