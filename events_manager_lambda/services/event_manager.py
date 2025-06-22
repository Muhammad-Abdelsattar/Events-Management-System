# services/event_manager.py
import boto3
from botocore.exceptions import ClientError
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional, List

from core.config import settings
from core.resources import get_boto3_client
from models.events import EventCreate, EventUpdate


# Custom Exceptions for clear error handling
class EventNotFound(Exception):
    pass


class NotEventOwner(Exception):
    pass


class InvalidUpdate(Exception):
    pass


class DeleteError(Exception):
    pass


# dynamodb = boto3.resource("dynamodb")
dynamodb = get_boto3_client("dynamodb")
table = dynamodb.Table(settings.EVENTS_TABLE_NAME)


def create_event(event_data: EventCreate, user_id: str) -> Dict[str, Any]:
    item = event_data.dict()
    item.update(
        {
            "eventId": str(uuid4()),
            "organizerId": user_id,
            "registeredAttendeesCount": 0,
            "status": "Active",
            "createdAt": datetime.utcnow().isoformat() + "Z",
        }
    )
    table.put_item(Item=item)
    return item


def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    response = table.get_item(Key={"eventId": event_id})
    return response.get("Item")


def get_all_events(
    limit: int = 25, exclusive_start_key: Optional[str] = None
) -> Dict[str, Any]:
    scan_kwargs = {"Limit": limit}
    if exclusive_start_key:
        scan_kwargs["ExclusiveStartKey"] = {"eventId": exclusive_start_key}

    response = table.scan(**scan_kwargs)
    return {
        "items": response.get("Items", []),
        "lastEvaluatedKey": response.get("LastEvaluatedKey", {}).get("eventId"),
    }


def get_events_by_organizer(organizer_id: str) -> List[Dict[str, Any]]:
    response = table.query(
        IndexName="OrganizerIdIndex",  # Assumes this GSI exists
        KeyConditionExpression="organizerId = :oid",
        ExpressionAttributeValues={":oid": organizer_id},
    )
    return response.get("Items", [])


def update_event(
    event_id: str, event_data: EventUpdate, user_id: str
) -> Dict[str, Any]:
    update_dict = event_data.dict(exclude_unset=True)
    if not update_dict:
        raise InvalidUpdate("No fields provided for update.")

    update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_dict)
    expression_attribute_names = {f"#{k}": k for k in update_dict}
    expression_attribute_values = {f":{k}": v for k, v in update_dict.items()}
    expression_attribute_values[":uid"] = user_id

    # Atomic condition check: ensures user is the owner
    condition_expression = "organizerId = :uid"

    try:
        response = table.update_item(
            Key={"eventId": event_id},
            UpdateExpression=update_expression,
            ConditionExpression=condition_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Could be not found or not the owner. The API layer will return 404/403.
            # To be more precise, we could do a get_item first, but this is more atomic.
            existing_event = get_event(event_id)
            if not existing_event:
                raise EventNotFound("Event not found.")
            raise NotEventOwner("User is not the owner of this event.")
        raise


def delete_event(event_id: str, user_id: str):
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
