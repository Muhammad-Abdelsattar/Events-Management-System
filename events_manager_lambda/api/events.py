from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional

from services import event_manager
from models.events import EventCreate, EventUpdate, EventInDB, User, EventListResponse
from core.dependencies import get_current_organizer, get_user_from_request

router = APIRouter()


@router.post(
    "/",
    response_model=EventInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
)
def create_new_event(event: EventCreate, user: User = Depends(get_current_organizer)):
    """
    Creates a new event. Only users in the 'Organizers' group can perform this action.
    """
    created_event = event_manager.create_event(event_data=event, user_id=user.user_id)
    return created_event


@router.get(
    "/{event_id}", response_model=EventInDB, summary="Get a single event by its ID"
)
def get_single_event(event_id: str):
    """Retrieves the details of a specific event."""
    event = event_manager.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.get(
    "/", response_model=EventListResponse, summary="List all events with pagination"
)
def list_events(
    organizer_id: Optional[str] = Query(
        None, description="Filter events by organizer ID"
    ),
    exclusive_start_key: Optional[str] = Query(
        None, description="Pagination key from the previous response"
    ),
):
    """
    Lists all events. Supports pagination and filtering by organizer.
    """
    if organizer_id:
        items = event_manager.get_events_by_organizer(organizer_id)
        return {"items": items, "lastEvaluatedKey": None}

    result = event_manager.get_all_events(exclusive_start_key=exclusive_start_key)
    return result


@router.put("/{event_id}", response_model=EventInDB, summary="Update an event")
def update_existing_event(
    event_id: str,
    event_update: EventUpdate,
    user: User = Depends(get_current_organizer),
):
    """Updates an event's details. Only the event's organizer can perform this action."""
    try:
        updated_event = event_manager.update_event(
            event_id=event_id, event_data=event_update, user_id=user.user_id
        )
        return updated_event
    except event_manager.EventNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except event_manager.NotEventOwner as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except event_manager.InvalidUpdate as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{event_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an event"
)
def delete_existing_event(event_id: str, user: User = Depends(get_current_organizer)):
    """
    Deletes an event. Only the organizer can do this, and only if there are no registered attendees.
    """
    try:
        event_manager.delete_event(event_id=event_id, user_id=user.user_id)
    except event_manager.DeleteError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return
