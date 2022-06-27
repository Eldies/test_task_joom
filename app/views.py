# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask import (
    jsonify,
    request, Response,
)
from flask.views import MethodView
from pydantic import (
    BaseModel,
    constr,
    root_validator,
    validator,
)
from typing import (
    Optional,
)

from .db_actions import (
    create_meeting,
    create_user,
    get_meeting_by_id,
    get_user_by_name,
    set_answer_for_invitation,
)


def ping():
    return 'pong'


UsernameField = constr(min_length=2, max_length=20, regex='^[a-zA-Z_]\\w*$')


class UsersModel(BaseModel):
    username: UsernameField


class UsersView(MethodView):
    def post(self) -> Response:
        form = UsersModel(**request.form)
        create_user(name=form.username)
        return jsonify(dict(status='ok'))


class MeetingsModel(BaseModel):
    creator_username: UsernameField
    start: datetime
    end: datetime
    description: Optional[str]
    invitees: Optional[list[UsernameField]]

    @root_validator(skip_on_failure=True)
    def check_end_is_later_than_start(cls, values: dict) -> dict:
        if values.get('end') < values.get('start'):
            raise ValueError('end should not be earlier than start')
        return values

    @validator('start', 'end')
    def treat_tz_naive_dates_as_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    @validator('invitees', pre=True)
    def split_invitees(cls, value: str) -> list[str]:
        return value.split(',')


class MeetingsView(MethodView):
    def post(self) -> Response:
        form = MeetingsModel(**request.form)

        meeting = create_meeting(
            creator=get_user_by_name(form.creator_username),
            start=int(form.start.astimezone(tz=timezone.utc).timestamp()),
            end=int(form.end.astimezone(tz=timezone.utc).timestamp()),
            description=form.description,
            invitees=[get_user_by_name(name=name) for name in (form.invitees or [])]
        )

        return jsonify(dict(status='ok', meeting_id=meeting.id))

    def get(self, meeting_id: int) -> Response:
        meeting = get_meeting_by_id(id=meeting_id)
        desc = dict(
            id=meeting.id,
            description=meeting.description,
            start_datetime=meeting.start_datetime.isoformat(),
            end_datetime=meeting.end_datetime.isoformat(),
            creator=meeting.creator.name,
            invitees=[
                dict(username=invitation.invitee.name, accepted_invitation=invitation.answer)
                for invitation in meeting.invitations
            ],
        )
        return jsonify(dict(status='ok', meeting_description=desc))


class AnswerInvitationModel(BaseModel):
    username: UsernameField
    meeting_id: int
    answer: bool


class AnswerInvitationView(MethodView):
    def post(self) -> Response:
        form = AnswerInvitationModel(**request.form)
        set_answer_for_invitation(
            invitee=get_user_by_name(form.username),
            meeting=get_meeting_by_id(form.meeting_id),
            answer=form.answer,
        )
        return jsonify(dict(status='ok'))
