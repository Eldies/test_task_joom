# -*- coding: utf-8 -*-
from flask import Flask, jsonify

from models import db
import settings
import views


def error_handler(error):
    return jsonify(dict(status='error', error=error.description)), error.code


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    db.init_app(app)

    # TODO proper migrations in case of actually using this app
    with app.app_context():
        db.create_all()

    app.add_url_rule('/ping', view_func=views.ping, methods=['GET'])
    app.add_url_rule('/users', view_func=views.UsersView.as_view('users'), methods=['POST'])
    app.add_url_rule('/meetings', view_func=views.MeetingsView.as_view('meetings'), methods=['POST'])
    app.add_url_rule('/meetings/<int:meeting_id>', view_func=views.MeetingsView.as_view('get_meeting'), methods=['GET'])
    app.add_url_rule('/invitations', view_func=views.AnswerInvitationView.as_view('answer_invitations'), methods=['POST'])

    app.register_error_handler(400, error_handler)
    app.register_error_handler(404, error_handler)

    return app


app = create_app()
