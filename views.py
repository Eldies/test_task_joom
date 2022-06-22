# -*- coding: utf-8 -*-
from flask import (
    jsonify,
    request,
)
from flask.views import MethodView

from models import (
    db,
    User,
)


def ping():
    return 'pong'


class UserView(MethodView):
    def post(self):
        username = request.form['username']
        db.session.add(User(username=username))
        db.session.commit()

        return jsonify(dict(
            status='ok',
        ))
