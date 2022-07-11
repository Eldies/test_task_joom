# -*- coding: utf-8 -*-
import base64

from app.models import User


def make_auth_header(username: str, password: str) -> str:
    return 'Basic {}'.format(
        base64.encodebytes('{}:{}'.format(
            username,
            password,
        ).encode()).decode().strip()
    )


def make_headers(name: str, password: str) -> dict[str, str]:
    return {
        'Authorization': make_auth_header(name, password)
    }
