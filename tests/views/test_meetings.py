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


class TestMeetingsView(unittest.TestCase):
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
            assert db.session.query(Meeting).count() == 0
        response = self.client.post('/meetings', data=self.default_args)
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            assert db.session.query(Meeting).count() == 1
            meeting = db.session.query(Meeting).first()
            assert meeting.id == 1
            assert meeting.creator.name == 'creator'
            assert meeting.start == datetime(2022, 6, 22, 18, 0, tzinfo=timezone.utc).timestamp()
            assert meeting.end == datetime(2022, 6, 22, 23, 0, tzinfo=timezone.utc).timestamp()
            assert meeting.description is None
            assert meeting.invitations == []

    def test_post_ok_tz_naive_dates_treated_as_utc_dates(self):
        response = self.client.post(
            '/meetings',
            data=dict(
                self.default_args,
                start='2022-06-22T19:00:00',
                end='2022-06-22T20:00:00',
            ),
        )
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            meeting = db.session.query(Meeting).first()
            assert meeting.start == int(datetime(2022, 6, 22, 19, 0, tzinfo=timezone.utc).timestamp())
            assert meeting.end == int(datetime(2022, 6, 22, 20, 0, tzinfo=timezone.utc).timestamp())

    def test_post_ok_with_description(self):
        response = self.client.post('/meetings', data=dict(self.default_args, description='desc'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            meeting = db.session.query(Meeting).first()
            assert meeting.description == 'desc'

    @parameterized.expand([
        ('start', None, 'field required'),
        ('start', '', 'invalid datetime format'),
        ('start', 'a', 'invalid datetime format'),
        ('end', None, 'field required'),
        ('end', '', 'invalid datetime format'),
        ('end', 'a', 'invalid datetime format'),
    ])
    def test_post_incorrect_date(self, field_name, value, error):
        response = self.client.post('/meetings', data=dict(self.default_args, **{field_name: value}))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {field_name: [error]}}
        with app.app_context():
            assert db.session.query(Meeting).count() == 0

    @parameterized.expand([
        (None, 'field required'),
        ('', 'ensure this value has at least 2 characters'),
        ('a', 'ensure this value has at least 2 characters'),
        ('a' * 21, 'ensure this value has at most 20 characters'),
        ('a b', 'string does not match regex "^[a-zA-Z_]\\w*$"'),
    ])
    def test_post_wrong_username(self, username, error):
        response = self.client.post('/meetings', data=dict(self.default_args, creator_username=username))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'creator_username': [error]}}
        with app.app_context():
            assert db.session.query(Meeting).count() == 0

    def test_post_nonexistent_username(self):
        response = self.client.post('/meetings', data=dict(self.default_args, creator_username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "FOO" does not exist'}
        with app.app_context():
            assert db.session.query(Meeting).count() == 0

    def test_post_end_before_start(self):
        response = self.client.post('/meetings', data=dict(self.default_args, end='2022-06-22T18:00:00+01:00'))
        assert response.status_code == 400
        assert response.json == {'status': 'error', 'error': {'__root__': ['end should not be earlier than start']}}
        with app.app_context():
            assert db.session.query(Meeting).count() == 0

    def test_post_ok_with_invitees(self):
        with app.app_context():
            db.session.add(User(name='inv1'))
            db.session.add(User(name='inv2'))
            db.session.commit()
        response = self.client.post('/meetings', data=dict(self.default_args, invitees='inv1,inv2'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        with app.app_context():
            assert db.session.query(Meeting).count() == 1
            meeting = db.session.query(Meeting).first()
            invitations = meeting.invitations
            assert len(invitations) == 2
            for invitation in invitations:
                assert invitation.meeting_id == meeting.id
                assert invitation.invitee.name in ('inv1', 'inv2')
                assert invitation.answer is None

    def test_post_with_nonexistent_invitee(self):
        with app.app_context():
            db.session.add(User(name='inv1'))
            db.session.commit()
        response = self.client.post('/meetings', data=dict(self.default_args, invitees='inv1,inv2'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "inv2" does not exist'}
        with app.app_context():
            assert db.session.query(Meeting).count() == 0
            assert db.session.query(Invitation).count() == 0

    @parameterized.expand([
        ('aa bb',),
        ('aa, bb',),
        ('1aa',),
        (' aa',),
    ])
    def test_post_with_wrong_invitees(self, invitees):
        response = self.client.post('/meetings', data=dict(self.default_args, invitees=invitees))
        assert response.status_code == 400
        assert response.json == {
            'status': 'error',
            'error': {'invitees': ['string does not match regex "^[a-zA-Z_]\\w*$"']},
        }
        with app.app_context():
            assert db.session.query(Meeting).count() == 0
            assert db.session.query(Invitation).count() == 0

    def test_get_ok(self):
        start = datetime.fromisoformat('2022-06-22T19:00:00+00:00')
        end = datetime.fromisoformat('2022-06-22T20:00:00+00:00')
        with app.app_context():
            user1 = User(name='inv1')
            user2 = User(name='inv2')
            user3 = User(name='inv3')
            meeting = Meeting(creator_id=1, start=start.timestamp(), end=end.timestamp())
            inv1 = Invitation(invitee=user1, meeting=meeting, answer=None)
            inv2 = Invitation(invitee=user2, meeting=meeting, answer=True)
            inv3 = Invitation(invitee=user3, meeting=meeting, answer=False)
            db.session.add_all([user1, user2, user3, meeting, inv1, inv2, inv3])
            db.session.commit()

            response = self.client.get('/meetings/{}'.format(meeting.id))

        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meeting_description': {
                'id': 1,
                'creator': 'creator',
                'description': None,
                'start_datetime': start.isoformat(),
                'end_datetime': end.isoformat(),
                'invitees': [
                    {'accepted_invitation': None, 'username': 'inv1'},
                    {'accepted_invitation': True, 'username': 'inv2'},
                    {'accepted_invitation': False,'username': 'inv3'},
                ],
            },
        }

    def test_get_string_meeting_id(self):
        response = self.client.get('/meetings/aaaaaa')
        assert response.status_code == 404
        assert response.json == {
            'status': 'error',
            'error':
                'The requested URL was not found on the server.'
                ' If you entered the URL manually please check your spelling and try again.',
        }

    def test_get_nonexistent_meeting(self):
        response = self.client.get('/meetings/9999')
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'Meeting with that id does not exist'}
