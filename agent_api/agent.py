"""PydanticAI agent with Gemini and MCP integration."""

import os
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

from .config import settings

# Set the Gemini API key in environment (pydantic-ai reads from env)
os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key

# Create MCP server connection via SSE
mcp_server = MCPServerHTTP(url=settings.mcp_server_url)

# Create agent with MCP tools
# Use string model name - pydantic-ai will use GOOGLE_API_KEY env var
agent = Agent(
    model="google-gla:gemini-2.0-flash",
    mcp_servers=[mcp_server],
    system_prompt="You are a helpful file assistant. Help users check and read files."
)
