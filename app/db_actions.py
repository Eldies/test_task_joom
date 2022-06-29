# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import (
    not_,
    or_,
)
from sqlalchemy.exc import IntegrityError

from .exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from .logic import RepeatTypeEnum
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


def create_user(name: str, password: str) -> User:
    try:
        user = User(name=name, password=password)
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError:
        raise AlreadyExistsException('user already exists')


def create_meeting(
        creator: User,
        start: int | datetime,
        end: int | datetime,
        description: str = None,
        invitees: list[User] = None,
        repeat_type: RepeatTypeEnum = RepeatTypeEnum.none,
) -> Meeting:
    if isinstance(start, datetime):
        assert start.tzinfo is not None
        start = int(start.astimezone(tz=timezone.utc).timestamp())
    if isinstance(end, datetime):
        assert end.tzinfo is not None
        end = int(end.astimezone(tz=timezone.utc).timestamp())
    if invitees is None:
        invitees = []
    meeting = Meeting(
        creator=creator,
        start=start,
        end=end,
        description=description,
        repeat_type=repeat_type,
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


def get_all_meetings_for_several_users(users: list[User], start: int | datetime) -> list[Meeting]:
    if isinstance(start, datetime):
        assert start.tzinfo is not None
        start = int(start.astimezone(tz=timezone.utc).timestamp())
    user_ids = [user.id for user in users]
    m1 = db.session.query(Meeting).join(Meeting.invitations).filter(
        Invitation.invitee_id.in_(user_ids),
        Invitation.answer.is_not(False),  # maybe there should be .is(True) instead
    )
    m2 = db.session.query(Meeting).filter(Meeting.creator_id.in_(user_ids))
    all_meetings = m2.union(m1)
    filtered_meetings = all_meetings.filter(
        or_(
            Meeting.end >= start,
            Meeting.repeat_type != RepeatTypeEnum.none,
        ),
    )
    return filtered_meetings.all()
