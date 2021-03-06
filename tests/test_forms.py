# -*- coding: utf-8 -*-
from pydantic import ValidationError

import pytest

from app.forms import (
    AnswerInvitationModel,
    FindFreeWindowForUsersModel,
    MeetingsModel,
    UserMeetingsForRangeModel,
    UsersModel,
)


class TestAnswerInvitationModel:
    default_args = dict(
        username='aa',
        meeting_id=1,
        answer=True,
    )

    @pytest.mark.parametrize('form', [
        default_args,
        dict(username='a' * 30, meeting_id='1', answer='true'),
        dict(username='qwertQWERTY23456_', meeting_id=1, answer='false'),
    ])
    def test_ok(self, form):
        AnswerInvitationModel(**form)

    @pytest.mark.parametrize('form,loc,msg', [
        (dict(default_args, username=''), ('username',), 'ensure this value has at least 2 characters'),
        (dict(meeting_id=1, answer=True), ('username',), 'field required'),
        (dict(default_args, username='a' * 31), ('username',), 'ensure this value has at most 30 characters'),
        (dict(default_args, username='a b'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, username='1a'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, meeting_id='ddd'), ('meeting_id',), 'value is not a valid integer'),
        (dict(username='aa', answer='false'), ('meeting_id',), 'field required'),
        (dict(default_args, answer='scooters'), ('answer',), 'value could not be parsed to a boolean'),
        (dict(username='aa', meeting_id=1), ('answer',), 'field required'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            AnswerInvitationModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg


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
        dict(default_args, end='2022-06-23T19:00'),
        dict(default_args, desc='some description'),
        dict(default_args, invitees='inv1,inv2,inv3'),
        dict(default_args, repeat_type='none'),
        dict(default_args, repeat_type='daily'),
        dict(default_args, repeat_type='weekly'),
        dict(default_args, repeat_type='yearly'),
        dict(default_args, repeat_type='every_working_day'),
        dict(default_args, is_private='true'),
    ])
    def test_ok(self, form):
        MeetingsModel(**form)

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
        (dict(default_args, repeat_type='abyrvalg'), ('repeat_type', ), "value is not a valid enumeration member; permitted: 'none', 'daily', 'weekly', 'every_working_day', 'yearly', 'monthly'"),
        (dict(default_args, is_private='something'), ('is_private', ), 'value could not be parsed to a boolean'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            MeetingsModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg


class TestUserMeetingsForRangeModel:
    default_args = dict(
        username='aa',
        start='2022-06-22T19:00:00+01:00',
        end='2022-06-22T20:00:00-03:00',
    )

    @pytest.mark.parametrize('form', [
        default_args,
        dict(default_args, username='qwertQWERTY23456_'),
        dict(default_args, username='a'*30),
        dict(default_args, start='2022-06-22T19:00:00'),
        dict(default_args, end='2022-06-23T19:00'),
    ])
    def test_ok(self, form):
        UserMeetingsForRangeModel(**form)

    @pytest.mark.parametrize('form,loc,msg', [
        (dict(start='2022-06-22T19:00:00', end='2022-06-22T20:00:00'), ('username',), 'field required'),
        (dict(default_args, username=''), ('username',), 'ensure this value has at least 2 characters'),
        (dict(default_args, username='a'), ('username',), 'ensure this value has at least 2 characters'),
        (dict(default_args, username='a'*31), ('username',), 'ensure this value has at most 30 characters'),
        (dict(default_args, username='a b'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, username='1ab'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(username='aa', end='2022-06-22T19:00:00'), ('start',), 'field required'),
        (dict(default_args, start='ab'), ('start',), 'invalid datetime format'),
        (dict(username='aa', start='2022-06-22T19:00:00'), ('end',), 'field required'),
        (dict(default_args, end='ab'), ('end',), 'invalid datetime format'),
        (dict(default_args, start=default_args['end'], end=default_args['start']), ('__root__',), 'end should not be earlier than start'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            UserMeetingsForRangeModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg


class TestUsersModel:
    default_args = dict(
        username='username',
        password='password',
    )

    @pytest.mark.parametrize('form', [
        default_args,
        dict(default_args, username='aa'),
        dict(default_args, username='a' * 30),
        dict(default_args, username='qwertQWERTY23456_'),
        dict(default_args, password='qwertQWERTY23456_'),
    ])
    def test_ok(self, form):
        UsersModel(**form)

    @pytest.mark.parametrize('form,loc,msg', [
        (dict(password='password'), ('username',), 'field required'),
        (dict(username='username'), ('password',), 'field required'),
        (dict(default_args, username=None), ('username',), 'none is not an allowed value'),
        (dict(default_args, username=''), ('username',), 'ensure this value has at least 2 characters'),
        (dict(default_args, username='a'), ('username',), 'ensure this value has at least 2 characters'),
        (dict(default_args, username='a' * 31), ('username',), 'ensure this value has at most 30 characters'),
        (dict(default_args, username='a b'), ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, username='1ab'),  ('username',), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, password=None), ('password',), 'none is not an allowed value'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            UsersModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg


class TestFindFreeWindowForUsersModel:
    default_args = dict(
        usernames='inv1,inv2,inv3',
        start='2022-06-22T19:00:00+01:00',
        window_size=1000,
    )

    @pytest.mark.parametrize('form', [
        default_args,
        dict(default_args, start='2022-06-22T19:00'),
    ])
    def test_ok(self, form):
        FindFreeWindowForUsersModel(**form)

    @pytest.mark.parametrize('form,loc,msg', [
        (dict(start='2022-06-22T19:00:00', window_size=1000), ('usernames',), 'field required'),
        (dict(usernames='inv1,inv2,inv3', window_size=1000), ('start',), 'field required'),
        (dict(start='2022-06-22T19:00:00', usernames='inv1,inv2,inv3'), ('window_size',), 'field required'),
        (dict(default_args, start='ab'), ('start',), 'invalid datetime format'),
        (dict(default_args, usernames='aa aa'), ('usernames', 0), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, usernames='aa,1aa'), ('usernames', 1), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, usernames='1aa'), ('usernames', 0), 'string does not match regex "^[a-zA-Z_]\\w*$"'),
        (dict(default_args, usernames='a'*31), ('usernames', 0), 'ensure this value has at most 30 characters'),
    ])
    def test_not_ok(self, form, loc, msg):
        with pytest.raises(ValidationError) as excinfo:
            FindFreeWindowForUsersModel(**form)
        assert len(excinfo.value.errors()) == 1
        assert excinfo.value.errors()[0]['loc'] == loc
        assert excinfo.value.errors()[0]['msg'] == msg
