from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    EVENTS_TABLE_NAME: str
    ORGANIZER_GROUP: str = "Organizers"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"  # For local development, loads a .env file
        case_sensitive = True


settings = Settings()
