"""SQLAlchemy ORM models for the Mergington High School Activities system."""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Activity(Base):
    """An extracurricular activity offered by the school."""

    __tablename__ = "activities"

    name = Column(String(255), primary_key=True, index=True)
    description = Column(String(1000), nullable=False)
    schedule = Column(String(255), nullable=False)
    max_participants = Column(Integer, nullable=False)

    participants = relationship(
        "Participant",
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class Participant(Base):
    """A student enrolled in an activity."""

    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_name = Column(
        String(255),
        ForeignKey("activities.name", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False)

    activity = relationship("Activity", back_populates="participants")


class User(Base):
    """A system user (admin, faculty, coordinator, or student)."""

    __tablename__ = "users"

    username = Column(String(150), primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")
