from botocore.exceptions import ClientError
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from core.resources import get_boto3_resource
from core.config import settings
from models.events import EventCreate, EventUpdate, EventStatus


# --- Custom Exceptions for this Service ---
class EventNotFound(Exception):
    """Raised when an event with a given ID cannot be found."""

    pass


class NotEventOwner(Exception):
    """Raised when a user attempts to modify an event they do not own."""

    pass


class InvalidUpdate(Exception):
    """Raised when an update operation is attempted with no data."""

    pass


class DeleteError(Exception):
    """Raised when an event cannot be deleted due to business rules."""

    pass


dynamodb_resource = get_boto3_resource("dynamodb")
table = dynamodb_resource.Table(settings.EVENTS_TABLE_NAME)


def create_event(event_data: EventCreate, user_id: str) -> Dict[str, Any]:
    """
    Creates a new event record in the DynamoDB table.

    Args:
        event_data: A Pydantic model with the new event's data.
        user_id: The ID of the user creating the event (organizer).

    Returns:
        A dictionary representing the newly created event item.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    item = event_data.model_dump()
    item.update(
        {
            "eventId": str(uuid4()),
            "organizerId": user_id,
            "registeredAttendeesCount": 0,
            "status": EventStatus.ACTIVE.value,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }
    )
    table.put_item(Item=item)
    return item


def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single event by its ID.

    Args:
        event_id: The unique ID of the event.

    Returns:
        A dictionary of the event item, or None if not found.
    """
    response = table.get_item(Key={"eventId": event_id})
    return response.get("Item")


def get_all_events(
    limit: int = 25, exclusive_start_key: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Retrieves a paginated list of all events using a Scan operation.

    Args:
        limit: The maximum number of items to return per page.
        exclusive_start_key: The pagination key from a previous response to fetch the next page.

    Returns:
        A dictionary containing the list of items and the next pagination key.
    """
    scan_kwargs = {"Limit": limit}
    if exclusive_start_key:
        scan_kwargs["ExclusiveStartKey"] = exclusive_start_key

    response = table.scan(**scan_kwargs)
    return {
        "items": response.get("Items", []),
        "lastEvaluatedKey": response.get("LastEvaluatedKey"),
    }


def get_events_by_organizer(organizer_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all events created by a specific organizer using the GSI.

    Args:
        organizer_id: The ID of the organizer.

    Returns:
        A list of event items.
    """
    response = table.query(
        IndexName="OrganizerIdIndex",
        KeyConditionExpression="organizerId = :oid",
        ExpressionAttributeValues={":oid": organizer_id},
    )
    return response.get("Items", [])


def update_event(
    event_id: str, event_data: EventUpdate, user_id: str
) -> Dict[str, Any]:
    """
    Atomically updates an event's attributes.
    Ensures that the user performing the update is the original organizer.

    Args:
        event_id: The ID of the event to update.
        event_data: A Pydantic model with the fields to update.
        user_id: The ID of the user requesting the update.

    Raises:
        InvalidUpdate: If no update data is provided.
        NotEventOwner: If the update fails the conditional check (wrong owner or event not found).

    Returns:
        A dictionary of the event item with its new attributes.
    """
    update_dict = event_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise InvalidUpdate("No fields provided for update.")

    update_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()

    update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_dict)
    expression_attribute_names = {f"#{k}": k for k in update_dict}
    expression_attribute_values = {f":{k}": v for k, v in update_dict.items()}
    expression_attribute_values[":uid"] = user_id

    try:
        response = table.update_item(
            Key={"eventId": event_id},
            UpdateExpression=update_expression,
            ConditionExpression="organizerId = :uid",
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotEventOwner(
                "Update failed: Event not found or user is not the owner."
            )
        raise


def delete_event(event_id: str, user_id: str):
    """
    Atomically deletes an event.
    Ensures the user is the owner AND there are no registered attendees.

    Args:
        event_id: The ID of the event to delete.
        user_id: The ID of the user requesting the deletion.

    Raises:
        DeleteError: If the conditional check fails for any reason.
    """
    try:
        table.delete_item(
            Key={"eventId": event_id},
            ConditionExpression="organizerId = :uid AND registeredAttendeesCount = :zero",
            ExpressionAttributeValues={":uid": user_id, ":zero": 0},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise DeleteError(
                "Deletion failed: Event not found, you are not the owner, or it has registered attendees."
            )
        raise
