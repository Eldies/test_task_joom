# -*- coding: utf-8 -*-
from .exceptions import NotFoundException
from .models import (
    db,
    User,
)


def get_user_by_name(name: str) -> User:
    user = db.session.query(User).filter_by(name=name).first()
    if user is None:
        raise NotFoundException('User "{}" does not exist'.format(name))
    return user