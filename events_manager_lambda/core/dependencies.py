import json
from fastapi import Request, HTTPException, status, Depends
from typing import Optional

from models.events import User
from core.config import settings


def get_cognito_claims(request: Request) -> dict:
    """Extracts Cognito claims from API Gateway event"""
    event = request.scope["aws.event"]

    if "requestContext" in event and "authorizer" in event["requestContext"]:
        authorizer = event["requestContext"]["authorizer"]

        # HTTP API Gateway format
        if "jwt" in authorizer and "claims" in authorizer["jwt"]:
            return authorizer["jwt"]["claims"]

        # REST API Gateway format
        if "claims" in authorizer:
            return authorizer["claims"]

    # Fallback to test event format
    return event.get("test_claims", {})


def get_user_groups(claims: dict) -> list[str]:
    """Extract and parse Cognito groups from claims, handling stringified lists"""
    # Get raw groups string
    groups_str = claims.get("cognito:groups", "")

    # Case 1: Empty string
    if not groups_str:
        return []

    # Case 2: Proper JSON array ('["Organizers","Admins"]')
    try:
        groups = json.loads(groups_str)
        if isinstance(groups, list):
            return groups
    except json.JSONDecodeError:
        pass

    # Case 3: Stringified list without quotes ('[Organizers, Admins]')
    if groups_str.startswith("[") and groups_str.endswith("]"):
        # Remove brackets and split
        inner = groups_str[1:-1].strip()
        return [g.strip() for g in inner.split(",")] if inner else []

    # Case 4: Comma-separated string ('Organizers, Admins')
    return [g.strip() for g in groups_str.split(",")]


def requires_auth(claims: dict = Depends(get_cognito_claims)):
    """Dependency for authenticated routes"""
    if "sub" not in claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return claims


def requires_group(group: str):
    """Dependency factory for group-based access"""

    def group_dependency(claims: dict = Depends(requires_auth)):
        groups = get_user_groups(claims)
        if group not in groups:
            raise HTTPException(status_code=403, detail=f"Requires {group} privileges")
        return claims

    return group_dependency


def get_current_user(claims: dict = Depends(requires_auth)):
    return User.parse_obj(claims)


def get_current_organizer(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )
    print(user)
    if settings.ORGANIZER_GROUP not in user.groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: User is not an organizer.",
        )
    return user
