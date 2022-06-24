# -*- coding: utf-8 -*-
from datetime import datetime
from flask import (
    abort,
    jsonify,
    request,
)
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from wtforms import (
    DateTimeField,
    Form,
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

        creator = User.query.filter_by(
            name=form.data['creator_username'],
        ).first_or_404(
            description='User with that name does not exist',
        )

        meeting = Meeting(
            creator=creator,
            start=form.data['start'].astimezone(tz=None),
            end=form.data['end'].astimezone(tz=None),
            description=form.data.get('description'),
        )
        db.session.add(meeting)

        if form.data.get('invitees'):
            invitee_names = form.data.get('invitees').split(',')
            invitees = [
                User.query.filter_by(name=name).first_or_404('User "{}" does not exist'.format(name))
                for name in invitee_names
            ]
            for invitee in invitees:
                db.session.add(Invitation(invitee=invitee, meeting=meeting,))

        db.session.commit()
        return jsonify(dict(status='ok', meeting_id=meeting.id))
