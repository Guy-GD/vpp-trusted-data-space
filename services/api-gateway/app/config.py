# services/api-gateway/app/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "VPP Gateway"
    DEBUG: bool = True
    DOWNSTREAM_SERVICE_URL: str = "http://localhost:8001" 

    class Config:
        env_file = ".env"

settings = Settings()