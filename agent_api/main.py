"""FastAPI application for MCP Security Demo.

SECURE VERSION - Contains multiple security fixes:
1. Strict CORS (only allows specific origins)
2. Security headers middleware (X-Frame-Options, CSP, etc.)
3. No tool poisoning in MCP server
"""

from fastapi import FastAPI, HTTPException, Request
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
    title="MCP Security Demo API",
    description="Demonstrates secure MCP implementation with security fixes",
    version="2.0.0",
    lifespan=lifespan
)

# SECURITY FIX 1: Strict CORS configuration
# Only allow requests from the same origin (localhost:8000)
# This prevents cross-origin attacks from malicious websites
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],  # SECURE: Only allow same origin
    allow_credentials=False,  # SECURE: Don't allow credentials in CORS
    allow_methods=["GET", "POST"],  # SECURE: Only allow necessary methods
    allow_headers=["Content-Type"],  # SECURE: Only allow necessary headers
)


# SECURITY FIX 2: Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable browser XSS filter
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy - restrict resource loading
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"

    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Prevent caching of sensitive data
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    return response


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
    In the secure version, tool descriptions are clean and file access
    is restricted to allowed directories.
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
    In the secure version, descriptions are clean without hidden instructions.
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
    return {
        "status": "healthy",
        "version": "secure",
        "security_features": [
            "strict_cors",
            "security_headers",
            "path_allowlisting",
            "audit_logging",
            "no_tool_poisoning"
        ]
    }
