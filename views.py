# -*- coding: utf-8 -*-
from flask import (
    abort,
    jsonify,
    request,
)
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from models import (
    db,
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
