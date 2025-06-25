from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EventStatus(str, Enum):
    """Defines the possible statuses for an event."""
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
    DRAFT = "Draft"

class User(BaseModel):
    user_id: str = Field(..., alias="sub", description="The unique identifier for the user from Cognito.")
    groups: List[str] = Field(default_factory=list, alias="cognito:groups")
    username: str = Field(..., alias="username")


class EventBase(BaseModel):
    """Base schema with common event fields."""
    eventName: str = Field(..., min_length=3, max_length=100, description="The public name of the event.")
    description: Optional[str] = Field(None, max_length=1000, description="A detailed description of the event.")
    eventDate: datetime = Field(..., description="The scheduled date and time for the event (UTC).")
    location: str = Field(..., max_length=200, description="The physical or virtual location of the event.")
    capacity: int = Field(..., gt=0, description="The maximum number of attendees allowed.")

    class Config:
        # Allows creating models from ORM/database objects
        orm_mode = True
        # Provides example data for API documentation
        schema_extra = {
            "example": {
                "eventName": "Tech Conference 2024",
                "description": "Annual conference for technology enthusiasts.",
                "eventDate": "2024-10-26T10:00:00Z",
                "location": "Virtual",
                "capacity": 500,
            }
        }

class EventCreate(EventBase):
    """Schema used for creating a new event. Inherits all fields from EventBase."""
    pass

class EventUpdate(BaseModel):
    """
    Schema for updating an event. All fields are optional to allow for partial updates.
    """
    eventName: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    eventDate: Optional[datetime]
    location: Optional[str] = Field(None, max_length=200)
    capacity: Optional[int] = Field(None, gt=0)
    status: Optional[EventStatus] = Field(None, description="Update the status of the event.")

class EventInDB(EventBase):
    """
    Full schema for an event as it is stored and returned from the database.
    This is the primary response model for GET requests.
    """
    eventId: str = Field(..., description="The unique identifier for the event.")
    organizerId: str = Field(..., description="The user ID of the event organizer.")
    registeredAttendeesCount: int = Field(..., ge=0, description="The current number of registered attendees.")
    status: EventStatus = Field(..., description="The current status of the event.")
    createdAt: datetime = Field(..., description="The timestamp when the event was created.")
    updatedAt: Optional[datetime] = Field(None, description="The timestamp of the last update.")

class EventListResponse(BaseModel):
    """Schema for paginated list responses of events."""
    items: List[EventInDB]
    lastEvaluatedKey: Optional[str] = Field(None, description="The key for fetching the next page of results. Null if no more pages.")
