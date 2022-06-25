# -*- coding: utf-8 -*-
from datetime import timezone
from flask import (
    abort,
    jsonify,
    request,
)
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from wtforms import (
    BooleanField,
    DateTimeField,
    Form,
    IntegerField,
    StringField,
    validators,
)

from models import (
    db,
    Invitation,
    Meeting,
    User,
)

def ping():
    return 'pong'


class UsernameField(StringField):
    validators = [
        validators.DataRequired(),
        validators.Length(min=2, max=20),
        validators.Regexp('^[a-zA-Z_]\\w*$'),
    ]


class UsersForm(Form):
    username = UsernameField('username')


class UsersView(MethodView):
    def post(self):
        form = UsersForm(request.form)
        if not form.validate():
            return abort(400, form.errors)

        username = form.data['username']
        try:
            db.session.add(User(name=username))
            db.session.commit()
        except IntegrityError:
            return abort(400, 'user already exists')

        return jsonify(dict(status='ok'))


class MeetingsForm(Form):
    creator_username = UsernameField('creator_username')
    start = DateTimeField('start', format='%Y-%m-%dT%H:%M:%S%z', validators=[validators.InputRequired()])
    end = DateTimeField('end', format='%Y-%m-%dT%H:%M:%S%z', validators=[validators.InputRequired()])
    description = StringField('description', validators=[validators.Optional()])
    invitees = StringField('invitees', validators=[
        validators.Optional(),
        validators.Regexp('^[a-zA-Z_]\\w*(,[a-zA-Z_]\\w*)*$'),
    ])

    def validate(self, *args, **kwargs):
        if not super(MeetingsForm, self).validate(*args, **kwargs):
            return False

        if self.end.data < self.start.data:
            self.end.errors.append('end should not be earlier than start')
            return False

        return True


class MeetingsView(MethodView):
    def post(self):
        form = MeetingsForm(request.form)
        if not form.validate():
            return abort(400, form.errors)

        creator = db.session.query(User).filter_by(
            name=form.data['creator_username'],
        ).first_or_404(
            description='User with that name does not exist',
        )

        meeting = Meeting(
            creator=creator,
            start=form.data['start'].astimezone(tz=timezone.utc).timestamp(),
            end=form.data['end'].astimezone(tz=timezone.utc).timestamp(),
            description=form.data.get('description'),
        )
        db.session.add(meeting)

        if form.data.get('invitees'):
            invitee_names = form.data.get('invitees').split(',')
            invitees = [
                db.session.query(User).filter_by(name=name).first_or_404('User "{}" does not exist'.format(name))
                for name in invitee_names
            ]
            for invitee in invitees:
                db.session.add(Invitation(invitee=invitee, meeting=meeting,))

        db.session.commit()
        return jsonify(dict(status='ok', meeting_id=meeting.id))

    def get(self, meeting_id: int):
        meeting = db.session.query(Meeting).filter_by(id=meeting_id).first_or_404(
            description='Meeting with that id does not exist',
        )
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


class AnswerInvitationForm(Form):
    username = UsernameField('username')
    meeting_id = IntegerField('meeting_id', validators=[validators.DataRequired()])
    answer = BooleanField('answer')


class AnswerInvitationView(MethodView):
    def post(self):
        form = AnswerInvitationForm(request.form)
        if not form.validate():
            return abort(400, form.errors)

        user = db.session.query(User).filter_by(
            name=form.data['username'],
        ).first_or_404(
            description='User with that name does not exist',
        )

        invitation = db.session.query(Invitation).filter_by(invitee=user, meeting_id=form.data['meeting_id']).first_or_404(
            description='User was not invited to this meeting',
        )

        invitation.answer = form.data['answer']
        db.session.commit()
        return jsonify(dict(status='ok'))
