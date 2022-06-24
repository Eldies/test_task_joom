# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
import logging
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
            db.session.add(User(name='creator'))
            db.session.commit()

        self.client = app.test_client()

        self.default_args = dict(
            creator_username='creator',
            start='2022-06-22T19:00:00+01:00',
            end='2022-06-22T20:00:00-03:00',
        )

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_post_ok(self):
        with app.app_context():
            assert Meeting.query.count() == 0
        response = self.client.post('/meeting', data=self.default_args)
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            assert Meeting.query.count() == 1
            meeting = Meeting.query.first()
            assert meeting.id == 1
            assert meeting.creator.name == 'creator'
            assert meeting.start.astimezone(tz=timezone.utc) == datetime(2022, 6, 22, 18, 0, tzinfo=timezone.utc)
            assert meeting.end.astimezone(tz=timezone.utc) == datetime(2022, 6, 22, 23, 0, tzinfo=timezone.utc)
            assert meeting.description is None
            assert meeting.invitations == []

    def test_post_ok_with_description(self):
        response = self.client.post('/meeting', data=dict(self.default_args, description='desc'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            meeting = Meeting.query.first()
            assert meeting.description == 'desc'

    @parameterized.expand([
        ('start', None, 'This field is required.'),
        ('start', '', 'This field is required.'),
        ('start', 'a', 'Not a valid datetime value.'),
        ('end', None, 'This field is required.'),
        ('end', '', 'This field is required.'),
        ('end', 'a', 'Not a valid datetime value.'),
    ])
    def test_post_incorrect_date(self, field_name, value, error):
        response = self.client.post('/meeting', data=dict(self.default_args, **{field_name: value}))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {field_name: [error]}}
        with app.app_context():
            assert Meeting.query.count() == 0

    @parameterized.expand([
        (None, 'This field is required.'),
        ('', 'This field is required.'),
        ('a', 'Field must be between 2 and 20 characters long.'),
        ('a' * 21, 'Field must be between 2 and 20 characters long.'),
        ('a b', 'Invalid input.'),
    ])
    def test_post_wrong_username(self, username, error):
        response = self.client.post('/meeting', data=dict(self.default_args, creator_username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'creator_username': [error]}}
        with app.app_context():
            assert Meeting.query.count() == 0

    def test_post_nonexistent_username(self):
        response = self.client.post('/meeting', data=dict(self.default_args, creator_username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User with that name does not exist'}
        with app.app_context():
            assert Meeting.query.count() == 0

    def test_post_end_before_start(self):
        response = self.client.post('/meeting', data=dict(self.default_args, end='2022-06-22T18:00:00+01:00'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'end': ['end should not be earlier than start']}}
        with app.app_context():
            assert Meeting.query.count() == 0

    def test_post_ok_with_invitees(self):
        with app.app_context():
            db.session.add(User(name='inv1'))
            db.session.add(User(name='inv2'))
            db.session.commit()
        response = self.client.post('/meeting', data=dict(self.default_args, invitees='inv1,inv2'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            assert Meeting.query.count() == 1
            meeting = Meeting.query.first()
            invitations = meeting.invitations
            assert len(invitations) == 2
            for invitation in invitations:
                assert invitation.meeting_id == meeting.id
                assert invitation.invitee.name in ('inv1', 'inv2')
                assert invitation.answer is None

    def test_post_with_wrong_invitees(self):
        with app.app_context():
            db.session.add(User(name='inv1'))
            db.session.commit()
        response = self.client.post('/meeting', data=dict(self.default_args, invitees='inv1,inv2'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "inv2" does not exist'}
        with app.app_context():
            assert Meeting.query.count() == 0
            assert Invitation.query.count() == 0
