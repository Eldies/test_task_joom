# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from parameterized import parameterized
import unittest

from app import app, db
from models import (
    Invitation,
    Meeting,
    User,
)


class TestImageView(unittest.TestCase):
    def setUp(self):
        app.logger.setLevel(logging.DEBUG)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        with app.app_context():
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

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test_post_ok(self, answer):
        with app.app_context():
            assert Invitation.query.filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None
        response = self.client.post('/invitations', data=dict(self.default_args, answer='true' if answer else 'false'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok'}
        with app.app_context():
            assert Invitation.query.filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer == answer

    @parameterized.expand([
        (None, 'This field is required.'),
        ('', 'This field is required.'),
        ('a', 'Field must be between 2 and 20 characters long.'),
        ('a' * 21, 'Field must be between 2 and 20 characters long.'),
        ('a b', 'Invalid input.'),
        ('1ab', 'Invalid input.'),
    ])
    def test_post_wrong_username(self, username, error):
        response = self.client.post('/invitations', data=dict(self.default_args, username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'username': [error]}}
        with app.app_context():
            assert Invitation.query.filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_post_nonexistent_meeting(self):
        response = self.client.post('/invitations', data=dict(self.default_args, meeting_id=9999))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User was not invited to this meeting'}
        with app.app_context():
            assert Invitation.query.filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_post_not_invited_user(self):
        response = self.client.post('/invitations', data=dict(self.default_args, username=self.not_invited_user.name))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User was not invited to this meeting'}
        with app.app_context():
            assert Invitation.query.filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None

    def test_post_nonexistent_username(self):
        response = self.client.post('/invitations', data=dict(self.default_args, username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User with that name does not exist'}
        with app.app_context():
            assert Invitation.query.filter_by(invitee=self.invited_user, meeting=self.meeting).first().answer is None
