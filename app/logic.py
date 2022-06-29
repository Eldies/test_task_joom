# -*- coding: utf-8 -*-
from dataclasses import (
    dataclass,
    field,
)
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from queue import PriorityQueue
from typing import Generator

from .db_actions import get_all_meetings_for_several_users
from .models import (
    Meeting,
    User,
)
from .types import RepeatTypeEnum


def get_repeated_timestamp(timestamp: int, repeat_type: RepeatTypeEnum):
    if repeat_type == RepeatTypeEnum.daily:
        return timestamp + 60 * 60 * 24
    if repeat_type == RepeatTypeEnum.weekly:
        return timestamp + 60 * 60 * 24 * 7
    if repeat_type == RepeatTypeEnum.monthly:
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        new_date = date.replace(month=date.month + 1)
        return int(new_date.timestamp())
    if repeat_type == RepeatTypeEnum.yearly:
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        new_date = date.replace(year=date.year + 1)
        return int(new_date.timestamp())
    if repeat_type == RepeatTypeEnum.every_working_day:
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        new_date = date + timedelta(days=1)
        while new_date.weekday() in [5, 6]:  # increase while it is sunday or saturday
            new_date += timedelta(days=1)
        return int(new_date.timestamp())
    assert False


def make_meeting_description(meeting: Meeting, requester: User = None) -> dict:
    if meeting.is_private:
        if requester is not None:
            people_who_has_rights = [
                invitation.invitee for invitation in meeting.invitations
            ] + [meeting.creator]
            show_full = requester in people_who_has_rights
        else:
            show_full = False
    else:
        show_full = True

    details = dict(
        id=meeting.id,
        start_datetime=meeting.start_datetime.isoformat(),
        end_datetime=meeting.end_datetime.isoformat(),
    )
    if show_full:
        details = dict(
            details,
            description=meeting.description,
            creator=meeting.creator.name,
            repeat_type=meeting.repeat_type,
            invitees=[
                dict(username=invitation.invitee.name, accepted_invitation=invitation.answer)
                for invitation in meeting.invitations
            ],
            is_private=meeting.is_private,
        )
    return details


class MeetingRangeWrapper:
    def __init__(self, meeting: Meeting, start: int, end: int):
        self.meeting = meeting
        self.start = start
        self.end = end

    @property
    def start_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.start, tz=timezone.utc)

    @property
    def end_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.end, tz=timezone.utc)

    def __getattr__(self, attr):
        return getattr(self.meeting, attr)


def iterate_meetings(meetings: list[Meeting]) -> Generator[MeetingRangeWrapper, None, None]:
    @dataclass(order=True)
    class PrioritizedItem:
        start: int
        end: int
        meeting: Meeting = field(compare=False)

    queue = PriorityQueue()
    for meeting in meetings:
        queue.put(PrioritizedItem(meeting.start, meeting.end, meeting))

    while not queue.empty():
        item = queue.get()

        yield MeetingRangeWrapper(item.meeting, item.start, item.end)

        if item.meeting.repeat_type != RepeatTypeEnum.none:
            new_start = get_repeated_timestamp(item.start, item.meeting.repeat_type)
            new_end = item.end + (new_start - item.start)
            queue.put(PrioritizedItem(new_start, new_end, item.meeting))


def find_first_free_window_among_meetings(
        meetings: list[Meeting],
        window_size: int,
        start: int | datetime,
) -> int | None:
    if isinstance(start, datetime):
        assert start.tzinfo is not None
        start = int(start.astimezone(tz=timezone.utc).timestamp())

    busy_until = start

    for meeting in iterate_meetings(meetings):
        if meeting.start - busy_until >= window_size:
            return busy_until
        busy_until = max(busy_until, meeting.end)

        if busy_until - start >= 60*60*24*365*10:  # people probably dont want to organize meeting ten years later
            return None

    return busy_until


def get_user_meetings_for_range(
        user: User,
        start: int | datetime,
        end: int | datetime,
) -> list[Meeting | MeetingRangeWrapper]:
    if isinstance(start, datetime):
        assert start.tzinfo is not None
        start = int(start.astimezone(tz=timezone.utc).timestamp())
    if isinstance(end, datetime):
        assert end.tzinfo is not None
        end = int(end.astimezone(tz=timezone.utc).timestamp())

    meetings = get_all_meetings_for_several_users([user], start)

    result = []
    for meeting in iterate_meetings(meetings):
        if meeting.start >= end:
            break
        if meeting.start < end and meeting.end > start:
            result.append(meeting)

    return result
