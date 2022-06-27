# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
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
    get_meeting_by_id,
    set_answer_for_invitation,
)
from app.exceptions import NotFoundException
from app.forms import MeetingsModel


class TestMeetingsModel:
    default_args = dict(
        creator_username='aa',
        start='2022-06-22T19:00:00+01:00',
        end='2022-06-22T20:00:00-03:00',
    )

    @pytest.mark.parametrize('form', [
        default_args,
        dict(default_args, creator_username='qwertQWERTY23456_'),
        dict(default_args, creator_username='a'*30),
        dict(default_args, start='2022-06-22T19:00:00'),
        dict(default_args, desc='some description'),
        dict(default_args, invitees='inv1,inv2,inv3'),
    ])
    def test_ok(self, form):
        form = MeetingsModel(**form)
        assert form.dict() == form

    @pytest.mark.parametrize('form,loc,msg', [
        (dict(start='2022-06-22T19:00:00', end='2022-06-22T20:00:00'), ('creator_username',), 'field required'),
        (dict(default_args, creator_username=''), ('creator_username',), 'ensure this value has at least 2 characters'),
        (dict(default_args, creator_username='a'), ('creator_username',), 'ensure this value has at least 2 characters'),
        (dict(default_args, creator_username='a'*31), ('creator_username',), 'ensure this value has at most 30 characters'),
        (dict(default_args, creator_username='a b'), ('creator_username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, creator_username='1ab'), ('creator_username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(creator_username='aa', end='2022-06-22T19:00:00'), ('start',), 'field required'),
        (dict(default_args, start='ab'), ('start',), 'invalid datetime format'),
        (dict(creator_username='aa', start='2022-06-22T19:00:00'), ('end',), 'field required'),
        (dict(default_args, end='ab'), ('end',), 'invalid datetime format'),
        (dict(default_args, start=default_args['end'], end=default_args['start']), ('__root__',), 'end should not be earlier than start'),
        (dict(default_args, invitees='aa aa'), ('invitees', 0), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, invitees='aa,1aa'), ('invitees', 1), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, invitees='1aa'), ('invitees', 0), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, invitees='a'*31), ('invitees', 0), 'ensure this value has at most 30 characters'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            MeetingsModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg


class TestMeetingsPostView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        create_user(name='creator')
        create_user(name='invitee1')
        create_user(name='invitee2')

        self.client = app.test_client()

        self.default_args = dict(
            creator_username='creator',
            start='2022-06-22T19:00:00+01:00',
            end='2022-06-22T20:00:00-03:00',
        )

    def test_ok(self):
        with pytest.raises(NotFoundException):
            get_meeting_by_id(1)

        response = self.client.post('/meetings', data=self.default_args)

        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        meeting = get_meeting_by_id(1)
        assert meeting.id == 1
        assert meeting.creator.name == 'creator'
        assert meeting.start == datetime(2022, 6, 22, 18, 0, tzinfo=timezone.utc).timestamp()
        assert meeting.end == datetime(2022, 6, 22, 23, 0, tzinfo=timezone.utc).timestamp()
        assert meeting.description is None
        assert meeting.invitations == []

    def test_validates_input(self):
        with patch('app.forms.MeetingsModel', Mock(wraps=MeetingsModel)) as mock:
            form = dict(foo='bar')
            self.client.post('/meetings', data=form)
            assert mock.call_count == 1
            assert mock.call_args.kwargs == form

    def test_ok_tz_naive_dates_treated_as_utc_dates(self):
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
        assert get_meeting_by_id(1).start == int(datetime(2022, 6, 22, 19, 0, tzinfo=timezone.utc).timestamp())
        assert get_meeting_by_id(1).end == int(datetime(2022, 6, 22, 20, 0, tzinfo=timezone.utc).timestamp())

    def test_ok_with_description(self):
        response = self.client.post('/meetings', data=dict(self.default_args, description='desc'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        assert get_meeting_by_id(1).description == 'desc'

    def test_nonexistent_username(self):
        response = self.client.post('/meetings', data=dict(self.default_args, creator_username='FOO'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "FOO" does not exist'}

    def test_ok_with_invitees(self):
        response = self.client.post('/meetings', data=dict(self.default_args, invitees='invitee1,invitee2'))
        assert response.status_code == 200
        assert response.json == {'status': 'ok', 'meeting_id': 1}
        meeting = get_meeting_by_id(1)
        assert len(meeting.invitations) == 2
        for invitation in meeting.invitations:
            assert invitation.meeting_id == meeting.id
            assert invitation.invitee.name in ('invitee1', 'invitee2')
            assert invitation.answer is None

    def test_with_nonexistent_invitee(self):
        response = self.client.post('/meetings', data=dict(self.default_args, invitees='invitee1,nonexistent_invitee'))
        assert response.status_code == 404
        assert response.json == {'status': 'error', 'error': 'User "nonexistent_invitee" does not exist'}


class TestMeetingsGetView:
    @pytest.fixture(autouse=True)
    def _setup(self, app):
        self.start = datetime.fromisoformat('2022-06-22T19:00:00+00:00')
        self.end = datetime.fromisoformat('2022-06-22T20:00:00+00:00')
        db.create_all()

        user1 = create_user(name='inv1')
        user2 = create_user(name='inv2')
        user3 = create_user(name='inv3')
        meeting = create_meeting(
            creator=create_user(name='creator'),
            start=int(self.start.timestamp()),
            end=int(self.end.timestamp()),
            description='DESCRIPTION',
            invitees=[user1, user2, user3],
        )
        set_answer_for_invitation(user2, meeting, True)
        set_answer_for_invitation(user3, meeting, False)

        self.meeting_id = meeting.id

        self.client = app.test_client()

    def test_ok(self):
        response = self.client.get('/meetings/{}'.format(self.meeting_id))

        assert response.status_code == 200
        assert response.json == {
            'status': 'ok',
            'meeting_description': {
                'id': 1,
                'creator': 'creator',
                'description': 'DESCRIPTION',
                'start_datetime': self.start.isoformat(),
                'end_datetime': self.end.isoformat(),
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
