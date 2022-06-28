# -*- coding: utf-8 -*-
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
