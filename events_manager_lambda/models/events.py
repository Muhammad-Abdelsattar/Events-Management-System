from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- User Models ---
class User(BaseModel):
    """Represents user info extracted from Cognito JWT."""

    user_id: str = Field(..., alias="sub")
    groups: List[str] = Field(default_factory=list, alias="cognito:groups")


# --- Event Models ---
class EventBase(BaseModel):
    """Base model with common event fields."""

    eventName: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    eventDate: datetime
    location: str = Field(..., max_length=150)
    capacity: int = Field(..., gt=0)  # Must be a positive integer


class EventCreate(EventBase):
    """Model for creating a new event (request body for POST)."""

    pass


class EventUpdate(BaseModel):
    """
    Model for updating an event (request body for PUT).
    All fields are optional for partial updates.
    """

    eventName: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    eventDate: Optional[datetime]
    location: Optional[str] = Field(None, max_length=150)
    capacity: Optional[int] = Field(None, gt=0)
    status: Optional[str]  # e.g., "Active", "Cancelled"


class EventInDB(EventBase):
    """Model representing a full event object as stored in DynamoDB."""

    eventId: str
    organizerId: str
    registeredAttendeesCount: int
    status: str
    createdAt: datetime


class EventListResponse(BaseModel):
    """Model for paginated list responses."""

    items: List[EventInDB]
    lastEvaluatedKey: Optional[str] = None
