# -*- coding: utf-8 -*-
from flask import (
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
            return jsonify(dict(status='error', error='no username')), 400

        username = request.form['username']
        try:
            db.session.add(User(name=username))
            db.session.commit()
        except IntegrityError:
            return jsonify(dict(status='error', error='user already exists')), 400

        return jsonify(dict(status='ok'))
