# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from pydantic import (
    BaseModel,
    constr,
    root_validator,
    validator,
)
from typing import (
    Optional,
)

from .logic import RepeatTypeEnum


UsernameField = constr(min_length=2, max_length=30, regex='^[a-zA-Z_]\\w*$')


class UsersModel(BaseModel):
    username: UsernameField
    password: constr(min_length=2, max_length=30, regex='^\\w*$')


class RangeModel(BaseModel):
    start: datetime
    end: datetime

    @root_validator(skip_on_failure=True)
    def check_end_is_later_than_start(cls, values: dict) -> dict:
        if values.get('end') < values.get('start'):
            raise ValueError('end should not be earlier than start')
        return values

    @validator('start', 'end')
    def treat_tz_naive_dates_as_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class MeetingsModel(RangeModel):
    creator_username: UsernameField
    description: Optional[str]
    invitees: Optional[list[UsernameField]]
    repeat_type: RepeatTypeEnum = RepeatTypeEnum.none
    is_private: bool = False

    @validator('invitees', pre=True)
    def split_invitees(cls, value: str) -> list[str]:
        return value.split(',')


class AnswerInvitationModel(BaseModel):
    username: UsernameField
    meeting_id: int
    answer: bool


class UserMeetingsForRangeModel(RangeModel):
    username: UsernameField


class FindFreeWindowForUsersModel(BaseModel):
    usernames: list[UsernameField]
    window_size: int
    start: datetime

    @validator('start')
    def treat_tz_naive_dates_as_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    @validator('usernames', pre=True)
    def split_usernames(cls, value: str) -> list[str]:
        return value.split(',')
