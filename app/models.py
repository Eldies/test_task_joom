# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Column,
    ForeignKey,
    MetaData,
)
from sqlalchemy.types import (
    Boolean,
    Integer,
    String,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

metadata = MetaData()
Base = declarative_base(metadata=metadata)
db = SQLAlchemy(metadata=metadata)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(120), nullable=False)

    @classmethod
    def generate_password_hash(cls, password: str) -> str:
        return generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Meeting(Base):
    __tablename__ = 'meetings'

    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    repeat_type = Column(String(20))
    description = Column(String(200))
    is_private = Column(Boolean, nullable=False, default=False)

    creator = relationship("User")
    invitations = relationship("Invitation", back_populates="meeting")

    @property
    def start_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.start, tz=timezone.utc)

    @property
    def end_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.end, tz=timezone.utc)


class Invitation(Base):
    __tablename__ = 'invitations'

    invitee_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), primary_key=True)
    answer = Column(Boolean)

    invitee = relationship("User")
    meeting = relationship("Meeting", back_populates="invitations")
