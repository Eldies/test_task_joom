# -*- coding: utf-8 -*-
from datetime import datetime
from flask import (
    abort,
    jsonify,
    request,
)
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from models import (
    db,
    Invitation,
    Meeting,
    User,
)


def ping():
    return 'pong'


class UserView(MethodView):
    def post(self):
        if 'username' not in request.form:
            return abort(400, 'no username')

        username = request.form['username']
        try:
            db.session.add(User(name=username))
            db.session.commit()
        except IntegrityError:
            return abort(400, 'user already exists')

        return jsonify(dict(status='ok'))


class MeetingView(MethodView):
    def post(self):
        if 'creator_username' not in request.form:
            return abort(400, 'no username')

        creator = User.query.filter_by(
            name=request.form['creator_username'],
        ).first_or_404(
            description='User with that name does not exist',
        )
        try:
            start_datetime = datetime.fromisoformat(request.form.get('start')).astimezone(tz=None)
            end_datetime = datetime.fromisoformat(request.form.get('end')).astimezone(tz=None)
        except ValueError:
            return abort(400, 'incorrect time')
        if start_datetime > end_datetime:
            return abort(400, 'end should not be earlier than start')

        meeting = Meeting(
            creator=creator,
            start=start_datetime,
            end=end_datetime,
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
