# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask import (
    abort,
    jsonify,
    request,
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
    get_user_by_name,
)
from .models import (
    db,
    Invitation,
    Meeting,
)


def ping():
    return 'pong'


UsernameField = constr(min_length=2, max_length=20, regex='^[a-zA-Z_]\\w*$')


class UsersModel(BaseModel):
    username: UsernameField


class UsersView(MethodView):
    def post(self):
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
    def check_end_is_later_than_start(cls, values):
        if values.get('end') < values.get('start'):
            raise ValueError('end should not be earlier than start')
        return values

    @validator('start', 'end')
    def treat_tz_naive_dates_as_utc(cls, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    @validator('invitees', pre=True)
    def split_invitees(cls, value):
        return value.split(',')


class MeetingsView(MethodView):
    def post(self):
        form = MeetingsModel(**request.form)

        meeting = create_meeting(
            creator=get_user_by_name(form.creator_username),
            start=int(form.start.astimezone(tz=timezone.utc).timestamp()),
            end=int(form.end.astimezone(tz=timezone.utc).timestamp()),
            description=form.description,
            invitees=[get_user_by_name(name=name) for name in (form.invitees or [])]
        )

        return jsonify(dict(status='ok', meeting_id=meeting.id))

    def get(self, meeting_id: int):
        meeting = db.session.query(Meeting).filter_by(id=meeting_id).first()
        if meeting is None:
            abort(404, 'Meeting with that id does not exist')
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
    def post(self):
        form = AnswerInvitationModel(**request.form)

        user = get_user_by_name(form.username)
        invitation = db.session.query(Invitation).filter_by(invitee=user, meeting_id=form.meeting_id).first()
        if invitation is None:
            abort(404, 'User was not invited to this meeting')

        invitation.answer = form.answer
        db.session.commit()
        return jsonify(dict(status='ok'))
