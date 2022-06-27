# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError

from .exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from .models import (
    db,
    User,
)


def get_user_by_name(name: str) -> User:
    user = db.session.query(User).filter_by(name=name).first()
    if user is None:
        raise NotFoundException('User "{}" does not exist'.format(name))
    return user


def create_user(name: str) -> None:
    try:
        db.session.add(User(name=name))
        db.session.commit()
    except IntegrityError:
        raise AlreadyExistsException('user already exists')
