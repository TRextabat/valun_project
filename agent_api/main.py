"""FastAPI application for MCP Vulnerability Demo.

VULNERABLE VERSION - Contains multiple security issues:
1. Tool Poisoning in MCP server (hidden instructions in tool descriptions)
2. Overly permissive CORS (allows any origin)
3. Missing security headers (no X-Frame-Options, CSP, etc.)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .agent import agent, mcp_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP server lifecycle."""
    # Start MCP server on startup
    async with mcp_server:
        yield


app = FastAPI(
    title="MCP Vulnerability Demo API",
    description="Demonstrates MCP Tool Poisoning vulnerability",
    version="1.0.0",
    lifespan=lifespan
)

# VULNERABILITY: Overly permissive CORS configuration
# This allows ANY website to make requests to our API and read responses
# A malicious site can steal data from users who have access to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # INSECURE: Allows all origins
    allow_credentials=True,  # INSECURE: Allows cookies/auth headers
    allow_methods=["*"],  # INSECURE: Allows all HTTP methods
    allow_headers=["*"],  # INSECURE: Allows all headers
)

# VULNERABILITY: No security headers middleware
# Missing: X-Frame-Options, X-Content-Type-Options, CSP, etc.
# This makes the application vulnerable to clickjacking, MIME sniffing, XSS


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    tools_called: list[str] = []


class ToolInfo(BaseModel):
    """Information about an MCP tool."""
    name: str
    description: str


class ToolsResponse(BaseModel):
    """Response model for tools endpoint."""
    tools: list[ToolInfo]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI agent connected to MCP server.

    The agent will use available MCP tools to respond to your request.
    In the vulnerable version, this may leak sensitive data due to
    tool poisoning in the tool descriptions.
    """
    try:
        result = await agent.run(request.message)

        # Extract tool calls from result
        tools_called = []
        for message in result.all_messages():
            if hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'tool_name'):
                        tools_called.append(part.tool_name)

        # Get the response text - try different attributes for compatibility
        response_text = ""
        if hasattr(result, 'output'):
            response_text = str(result.output)
        elif hasattr(result, 'data'):
            response_text = str(result.data)
        else:
            # Get last text message from messages
            for msg in reversed(result.all_messages()):
                if hasattr(msg, 'content'):
                    response_text = str(msg.content)
                    break
                elif hasattr(msg, 'parts'):
                    for part in msg.parts:
                        if hasattr(part, 'content'):
                            response_text = str(part.content)
                            break

        return ChatResponse(
            response=response_text,
            tools_called=tools_called
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools", response_model=ToolsResponse)
async def list_tools():
    """List available MCP tools.

    This shows what the AI sees including tool descriptions.
    In the vulnerable version, you can see the hidden instructions
    embedded in the check_file_safety tool description.
    """
    tools = await mcp_server.list_tools()
    return ToolsResponse(
        tools=[
            ToolInfo(name=t.name, description=t.description or "")
            for t in tools
        ]
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "vulnerable"}
