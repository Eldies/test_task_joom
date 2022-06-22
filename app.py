# -*- coding: utf-8 -*-
from flask import Flask

import settings
import views


def create_app():
    app = Flask(__name__)

    app.add_url_rule('/ping', view_func=views.ping)

    return app


app = create_app()
