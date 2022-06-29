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


def make_headers(auth_user: User) -> dict[str, str]:
    return {
        'Authorization': make_auth_header(auth_user.name, auth_user.password)
    }
