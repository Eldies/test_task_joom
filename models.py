# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Column,
    ForeignKey,
)
from sqlalchemy.types import (
    Boolean,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

db = SQLAlchemy()
Base = db.Model


class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)


class Meeting(Base):
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("user.id"))
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    description = Column(String(200))

    creator = relationship("User")
    invitations = relationship("Invitation", back_populates="meeting")

    @property
    def start_datetime(self):
        return datetime.fromtimestamp(self.start, tz=timezone.utc)

    @property
    def end_datetime(self):
        return datetime.fromtimestamp(self.end, tz=timezone.utc)


class Invitation(Base):
    invitee_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id"), primary_key=True)
    answer = Column(Boolean)

    invitee = relationship("User")
    meeting = relationship("Meeting", back_populates="invitations")
