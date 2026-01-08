"""Configuration settings for the Agent API."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str
    mcp_server_command: str = "python"
    mcp_server_args: str = "/app/mcp_server/server.py"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
