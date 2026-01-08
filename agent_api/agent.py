"""PydanticAI agent with Gemini and MCP integration."""

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.mcp import MCPServerStdio

from .config import settings


# Create Gemini model
model = GeminiModel("gemini-2.0-flash", api_key=settings.gemini_api_key)

# Create MCP server connection
mcp_server = MCPServerStdio(
    command=settings.mcp_server_command,
    args=[settings.mcp_server_args]
)

# Create agent with MCP tools
agent = Agent(
    model=model,
    mcp_servers=[mcp_server],
    system_prompt="You are a helpful file assistant. Help users check and read files."
)
