# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from queue import PriorityQueue

from .models import Meeting


def make_meeting_description(meeting: Meeting) -> dict:
    return dict(
        id=meeting.id,
        description=meeting.description,
        start_datetime=meeting.start_datetime.isoformat(),
        end_datetime=meeting.end_datetime.isoformat(),
        creator=meeting.creator.name,
        invitees=[
            dict(username=invitation.invitee.name, accepted_invitation=invitation.answer)
            for invitation in meeting.invitations
        ],
    )


def find_first_free_range_among_meetings(meetings: list[Meeting], range_size: int, start: int) -> int:
    @dataclass(order=True)
    class PrioritizedItem:
        start: int
        end: int
        meeting: Meeting = field(compare=False)

    if len(meetings) == 0:
        return start

    queue = PriorityQueue()
    for meeting in meetings:
        queue.put(PrioritizedItem(meeting.start, meeting.end, meeting))

    first_item = queue.get()
    if first_item.start >= start + range_size:
        return start
    busy_until = first_item.end

    while not queue.empty():
        item = queue.get()
        if item.start - busy_until >= range_size:
            return busy_until
        busy_until = max(busy_until, item.end)

    return busy_until
