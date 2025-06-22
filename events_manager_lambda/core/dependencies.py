from fastapi import Request, HTTPException, status, Depends
from typing import Optional

from models.event import User
from core.config import settings


def get_user_from_request(request: Request) -> Optional[User]:
    """
    Dependency to extract user info from the API Gateway event context.
    Mangum makes the raw event available in the request scope.
    """
    authorizer_claims = (
        request.scope.get("aws.event", {})
        .get("requestContext", {})
        .get("authorizer", {})
        .get("claims")
    )
    if not authorizer_claims:
        return None
    return User.parse_obj(authorizer_claims)


def get_current_organizer(
    user: Optional[User] = Depends(get_user_from_request),
) -> User:
    """
    Dependency that ensures the current user is authenticated and is an organizer.
    Raises a 403 Forbidden error if not.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )
    if settings.ORGANIZER_GROUP not in user.groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: User is not an organizer.",
        )
    return user


#----- For local testing (mocking cognito) ------------
def fake_get_current_organizer() -> User:
    """
    A mock dependency that bypasses Cognito and returns a hard-coded
    test user with the 'Organizers' group.
    """
    print("--- MOCK AUTH: Providing a fake 'Organizer' user. ---")
    return User(
        sub="test-organizer-001",  # This is the user_id
        cognito_groups=["Organizers", "Attendees"], # Belongs to both groups
        email="organizer.test@example.com",
        name="Test Organizer",
        cognito_username="testorganizer"
    )

def fake_get_user_from_request() -> User:
    """
    A mock dependency that returns a generic test user without any specific
    group, useful for testing public or non-role-specific endpoints.
    """
    print("--- MOCK AUTH: Providing a fake generic user. ---")
    return User(
        sub="test-user-generic-002",
        cognito_groups=["Attendees"],
        email="generic.test@example.com",
        name="Generic User",
        cognito_username="genericuser"
    )
