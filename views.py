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


class UserForm(Form):
    username = UsernameField('username')


class UserView(MethodView):
    def post(self):
        form = UserForm(request.form)
        if not form.validate():
            return abort(400, form.errors)

        username = request.form['username']
        try:
            db.session.add(User(name=username))
            db.session.commit()
        except IntegrityError:
            return abort(400, 'user already exists')

        return jsonify(dict(status='ok'))


class MeetingForm(Form):
    creator_username = UsernameField('creator_username')
    start = DateTimeField('start', format='%Y-%m-%dT%H:%M:%S%z', validators=[validators.InputRequired()])
    end = DateTimeField('end', format='%Y-%m-%dT%H:%M:%S%z', validators=[validators.InputRequired()])
    description = StringField('description')

    def validate(self):
        if not super(MeetingForm, self).validate():
            return False

        if self.end.data < self.start.data:
            self.end.errors.append('end should not be earlier than start')
            return False

        return True


class MeetingView(MethodView):
    def post(self):
        form = MeetingForm(request.form)
        if not form.validate():
            return abort(400, form.errors)

        creator = User.query.filter_by(
            name=request.form['creator_username'],
        ).first_or_404(
            description='User with that name does not exist',
        )

        meeting = Meeting(
            creator=creator,
            start=form.data['start'].astimezone(tz=None),
            end=form.data['end'].astimezone(tz=None),
            description=request.form.get('description'),
        )
        db.session.add(meeting)

        if 'invitees' in request.form:
            invitee_names = request.form['invitees'].split(',')
            invitees = [
                User.query.filter_by(name=name).first_or_404('User "{}" does not exist'.format(name))
                for name in invitee_names
            ]
            for invitee in invitees:
                db.session.add(Invitation(invitee=invitee, meeting=meeting,))

        db.session.commit()
        return jsonify(dict(status='ok', meeting_id=meeting.id))
