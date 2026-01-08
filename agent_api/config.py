"""Configuration settings for the Agent API."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str
    # MCP server connection (SSE transport)
    mcp_server_url: str = "http://mcp-server:8001/sse"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
