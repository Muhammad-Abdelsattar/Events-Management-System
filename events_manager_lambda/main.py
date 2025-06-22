import os
import logging
from fastapi import FastAPI
from mangum import Mangum

from api.events import router as events_router
from core.config import settings
from core.dependencies import fake_get_current_organizer, fake_get_user_from_request
from core.dependencies import get_current_organizer, get_user_from_request

IS_OFFLINE = os.environ.get("IS_OFFLINE")

# Configure logging
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL.upper())

# Create FastAPI app
app = FastAPI(
    title="Events Manager API",
    description="API for creating and managing events.",
    version="1.0.0",
)

# --- THE MAGIC: Dependency Override ---
if IS_OFFLINE:
    print("--- RUNNING IN OFFLINE MODE: AUTHENTICATION IS MOCKED ---")
    # Tell FastAPI to use our fake function whenever the real one is requested
    app.dependency_overrides[get_current_organizer] = fake_get_current_organizer
    app.dependency_overrides[get_user_from_request] = fake_get_user_from_request
else:
    print("--- RUNNING IN ONLINE MODE: USING REAL COGNITO AUTH ---")


# Include the events router
app.include_router(events_router, prefix="/events", tags=["Events"])


# Health check endpoint
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Events Manager API"}


# Create the Mangum handler for AWS Lambda
handler = Mangum(app, lifespan="off")
