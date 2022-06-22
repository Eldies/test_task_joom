# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
import logging
import unittest

from app import app, db
from models import (
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
            assert meeting.creator_id == User.query.filter_by(name='creator').first().id
            assert meeting.start.astimezone(tz=timezone.utc) == datetime(2022, 6, 22, 18, 0, tzinfo=timezone.utc)
            assert meeting.end.astimezone(tz=timezone.utc) == datetime(2022, 6, 22, 23, 0, tzinfo=timezone.utc)
            assert meeting.description is None

    def test_post_ok_with_description(self):
        response = self.client.post('/meeting', data=dict(self.default_args, description='desc'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            meeting = Meeting.query.first()
            assert meeting.description == 'desc'

    def test_post_incorrect_start(self):
        response = self.client.post('/meeting', data=dict(self.default_args, start='FOO'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'incorrect time'}

    def test_post_incorrect_end(self):
        response = self.client.post('/meeting', data=dict(self.default_args, end='FOO'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'incorrect time'}

    def test_post_no_username(self):
        response = self.client.post('/meeting', data=dict())
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'no username'}

    def test_post_nonexistent_username(self):
        response = self.client.post('/meeting', data=dict(self.default_args, creator_username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User with that name does not exist'}

    def test_post_end_before_start(self):
        response = self.client.post('/meeting', data=dict(self.default_args, end='2022-06-22T18:00:00+01:00'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': 'end should not be earlier than start'}
