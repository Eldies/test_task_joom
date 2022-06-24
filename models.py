# -*- coding: utf-8 -*-
from datetime import (
    datetime,
    timezone,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, ForeignKey("user.id"))
    start = db.Column(db.Integer, nullable=False)
    end = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))

    creator = db.relationship("User")
    invitations = db.relationship("Invitation", back_populates="meeting")

    @property
    def start_datetime(self):
        return datetime.fromtimestamp(self.start, tz=timezone.utc)

    @property
    def end_datetime(self):
        return datetime.fromtimestamp(self.end, tz=timezone.utc)


class Invitation(db.Model):
    invitee_id = db.Column(db.Integer, ForeignKey("user.id"), primary_key=True)
    meeting_id = db.Column(db.Integer, ForeignKey("meeting.id"), primary_key=True)
    answer = db.Column(db.Boolean)

    invitee = db.relationship("User")
    meeting = db.relationship("Meeting", back_populates="invitations")
