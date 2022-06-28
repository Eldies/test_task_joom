# -*- coding: utf-8 -*-
from sqlalchemy import (
    not_,
    or_,
)
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


def create_meeting(creator: User, start: int, end: int, description: str = None, invitees: list[User] = None) -> Meeting:
    if invitees is None:
        invitees = []
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


def get_invitation(invitee: User, meeting: Meeting) -> Invitation:
    invitation = db.session.query(Invitation).filter_by(invitee=invitee, meeting=meeting).first()
    if invitation is None:
        raise NotFoundException('User was not invited to this meeting')
    return invitation


def set_answer_for_invitation(invitee: User, meeting: Meeting, answer: bool) -> None:
    get_invitation(invitee=invitee, meeting=meeting).answer = answer
    db.session.commit()


def get_user_meetings_for_range(user: User, start: int, end: int) -> list[Meeting]:
    m1 = db.session.query(Meeting).join(Meeting.invitations).filter(Invitation.invitee == user)
    m2 = db.session.query(Meeting).filter_by(creator=user)
    all_meetings_of_user = m2.union(m1)

    filtered_meetings = all_meetings_of_user.filter(not_(or_(
        Meeting.start > end,
        Meeting.end < start,
    )))

    return filtered_meetings.all()
