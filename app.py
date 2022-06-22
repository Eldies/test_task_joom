# -*- coding: utf-8 -*-
from flask import Flask

from models import db
import settings
import views


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    db.init_app(app)

    app.add_url_rule('/ping', view_func=views.ping)
    app.add_url_rule('/user', view_func=views.UserView.as_view('user'))

    return app


app = create_app()
