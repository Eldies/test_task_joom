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

        creator_id = User.query.filter_by(
            name=request.form['creator_username'],
        ).first_or_404(
            description='User with that name does not exist',
        ).id
        try:
            start_datetime = datetime.fromisoformat(request.form.get('start')).astimezone(tz=None)
            end_datetime = datetime.fromisoformat(request.form.get('end')).astimezone(tz=None)
        except ValueError:
            return abort(400, 'incorrect time')

        meeting = Meeting(
            creator_id=creator_id,
            start=start_datetime,
            end=end_datetime,
            description=request.form.get('description'),
        )
        db.session.add(meeting)
        db.session.commit()
        return jsonify(dict(status='ok', meeting_id=meeting.id))
