# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError

from .exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from .models import (
    db,
    Invitation,
    Meeting,
    User,
)


def get_user_by_name(name: str) -> User:
    user = db.session.query(User).filter_by(name=name).first()
    if user is None:
        raise NotFoundException('User "{}" does not exist'.format(name))
    return user


def create_user(name: str) -> User:
    try:
        user = User(name=name)
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError:
        raise AlreadyExistsException('user already exists')


def create_meeting(creator: User, start: int, end: int, description: str, invitees: list[User]) -> Meeting:
    meeting = Meeting(
        creator=creator,
        start=start,
        end=end,
        description=description,
    )
    db.session.add(meeting)

    for invitee in invitees:
        db.session.add(Invitation(invitee=invitee, meeting=meeting))

    db.session.add(meeting)
    db.session.commit()
    return meeting


def get_meeting_by_id(id: int) -> Meeting:
    meeting = db.session.query(Meeting).filter_by(id=id).first()
    if meeting is None:
        raise NotFoundException('Meeting with id "{}" does not exist'.format(id))
    return meeting
