import os
import logging
from fastapi import FastAPI
from mangum import Mangum

from api.events import router as events_router


app = FastAPI(
    title="Events Manager API",
    description="API for creating and managing events.",
    version="1.0.0",
)


app.include_router(events_router, prefix="/events", tags=["Events"])


@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Events Manager API"}


BASE_PATH = os.environ.get("BASE_PATH", "/")

handler = Mangum(app, lifespan="off", api_gateway_base_path=BASE_PATH)

