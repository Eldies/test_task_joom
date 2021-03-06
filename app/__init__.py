# -*- coding: utf-8 -*-
from flask import (
    Flask,
    jsonify,
    Response,
)
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from .models import db
from .exceptions import BaseLocalException
from . import (
    settings,
    views,
)


def pydantic_validation_error_handler(error: ValidationError) -> (Response, int):
    return jsonify(dict(status='error', error={err['loc'][0]: [err['msg']] for err in error.errors()})), 400


def error_handler(error: HTTPException) -> (Response, int):
    return jsonify(dict(status='error', error=error.description)), error.code


def local_exception_handler(error: BaseLocalException) -> (Response, int):
    return jsonify(dict(status='error', error=error.args[0])), error.code


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if test_config is not None:
        app.config.update(test_config)
    db.init_app(app)

    # TODO proper migrations in case of actually using this app
    with app.app_context():
        db.create_all()

    app.add_url_rule('/ping', view_func=views.ping, methods=['GET'])
    app.add_url_rule('/users', view_func=views.UsersView.as_view('users'), methods=['POST'])
    app.add_url_rule('/users/<username>/meetings', view_func=views.UserMeetingsForRangeView.as_view('user_meetings'), methods=['GET'])
    app.add_url_rule('/meetings', view_func=views.MeetingsView.as_view('meetings'), methods=['POST'])
    app.add_url_rule('/meetings/<int:meeting_id>', view_func=views.MeetingsView.as_view('get_meeting'), methods=['GET'])
    app.add_url_rule('/invitations', view_func=views.AnswerInvitationView.as_view('answer_invitations'), methods=['POST'])
    app.add_url_rule('/find_free_window_for_users', view_func=views.FindFreeWindowForUsersView.as_view('find_free_window'), methods=['GET'])

    app.register_error_handler(400, error_handler)
    app.register_error_handler(401, error_handler)
    app.register_error_handler(403, error_handler)
    app.register_error_handler(404, error_handler)
    app.register_error_handler(BaseLocalException, local_exception_handler)
    app.register_error_handler(ValidationError, pydantic_validation_error_handler)

    return app
