# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask import (
    abort,
    jsonify,
    request,
    Response,
)
from flask.views import MethodView

from . import forms
from .db_actions import (
    create_meeting,
    create_user,
    get_all_meetings_for_several_users,
    get_meeting_by_id,
    get_user_by_name,
    get_user_meetings_for_range,
    set_answer_for_invitation,
)
from .logic import (
    find_first_free_window_among_meetings,
    make_meeting_description,
)
from .models import User


def ping():
    return 'pong'


class AuthenticationMixin:
    def get_authenticated_user(self) -> User | None:
        auth_info = request.authorization
        if auth_info is None:
            return None
        user = get_user_by_name(auth_info.username)
        if auth_info['password'] != user.password:
            abort(403, 'Wrong password')
        return user

    def assert_user_is_authenticated(self, user: User) -> None:
        auth_user = self.get_authenticated_user()
        if auth_user is None:
            abort(401, 'Not authenticated')
        if user != auth_user:
            abort(403, 'Wrong user')


class UsersView(MethodView):
    def post(self) -> Response:
        form = forms.UsersModel(**request.form)
        create_user(name=form.username, password=form.password)
        return jsonify(dict(status='ok'))


class MeetingsView(MethodView, AuthenticationMixin):
    def post(self) -> Response:
        form = forms.MeetingsModel(**request.form)

        creator = get_user_by_name(form.creator_username)
        self.assert_user_is_authenticated(creator)
        meeting = create_meeting(
            creator=creator,
            start=int(form.start.astimezone(tz=timezone.utc).timestamp()),
            end=int(form.end.astimezone(tz=timezone.utc).timestamp()),
            description=form.description,
            invitees=[get_user_by_name(name=name) for name in (form.invitees or [])],
            repeat_type=form.repeat_type,
        )

        return jsonify(dict(status='ok', meeting_id=meeting.id))

    def get(self, meeting_id: int) -> Response:
        meeting = get_meeting_by_id(id=meeting_id)
        desc = make_meeting_description(meeting)
        return jsonify(dict(status='ok', meeting_description=desc))


class AnswerInvitationView(MethodView, AuthenticationMixin):
    def post(self) -> Response:
        form = forms.AnswerInvitationModel(**request.form)
        user = get_user_by_name(form.username)
        self.assert_user_is_authenticated(user)
        set_answer_for_invitation(
            invitee=user,
            meeting=get_meeting_by_id(form.meeting_id),
            answer=form.answer,
        )
        return jsonify(dict(status='ok'))


class UserMeetingsForRangeView(MethodView):
    def get(self, username: str) -> Response:
        form = forms.UserMeetingsForRangeModel(username=username, **request.args)
        meetings = get_user_meetings_for_range(
            user=get_user_by_name(form.username),
            start=int(form.start.astimezone(tz=timezone.utc).timestamp()),
            end=int(form.end.astimezone(tz=timezone.utc).timestamp()),
        )
        return jsonify(dict(status='ok', meetings=[make_meeting_description(m) for m in meetings]))


class FindFreeWindowForUsersView(MethodView):
    def get(self) -> Response:
        form = forms.FindFreeWindowForUsersModel(**request.args)
        start_timestamp = int(form.start.astimezone(tz=timezone.utc).timestamp())
        meetings = get_all_meetings_for_several_users(
            users=[get_user_by_name(name) for name in form.usernames],
            start=start_timestamp,
        )
        window_start_timestamp = find_first_free_window_among_meetings(
            meetings=meetings,
            window_size=form.window_size,
            start=start_timestamp,
        )
        if window_start_timestamp is None:
            abort(404, 'Impossible to find window for meeting')

        return jsonify(dict(status='ok', window={
            'start': datetime.fromtimestamp(window_start_timestamp, tz=timezone.utc).isoformat(),
            'end': datetime.fromtimestamp(window_start_timestamp + form.window_size, tz=timezone.utc).isoformat(),
        }))
