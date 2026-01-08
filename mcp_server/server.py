"""
MCP Security Demo - SECURE VERSION

This MCP server demonstrates security best practices:
1. NO hidden instructions in tool descriptions (prevents tool poisoning)
2. Path allowlisting (prevents unauthorized file access)
3. Audit logging (tracks all file operations)
4. Input sanitization (prevents path traversal)
"""

import os
import logging
from datetime import datetime
from fastmcp import FastMCP

# Configure audit logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SecureMCPServer")

mcp = FastMCP("SecureFileServer")

# SECURITY FIX 1: Allowlist of readable directories
# Only files in these directories can be accessed
ALLOWED_DIRECTORIES = [
    "/app/demo/user_files/",
    "/app/demo/public/",
]


def sanitize_path(filepath: str) -> str:
    """SECURITY FIX 2: Sanitize file paths to prevent traversal attacks."""
    # Remove path traversal attempts
    filepath = filepath.replace('..', '')
    filepath = filepath.replace('//', '/')
    # Normalize the path
    filepath = os.path.normpath(filepath)
    return filepath


def is_path_allowed(filepath: str) -> bool:
    """Check if the file path is within allowed directories."""
    normalized = os.path.normpath(filepath)
    return any(normalized.startswith(d) for d in ALLOWED_DIRECTORIES)


def audit_log(action: str, filepath: str, result: str, user_ip: str = "local"):
    """SECURITY FIX 3: Log all file access attempts for audit trail."""
    logger.info(f"AUDIT | Action: {action} | Path: {filepath} | Result: {result} | IP: {user_ip}")


@mcp.tool()
def read_file(filepath: str) -> str:
    """Read contents of a file from allowed directories.

    This tool only allows reading files from designated safe directories.
    All access attempts are logged for security auditing.

    Args:
        filepath: Path to the file to read (must be in allowed directories)
    """
    # Sanitize the path
    filepath = sanitize_path(filepath)

    # Check if path is allowed
    if not is_path_allowed(filepath):
        audit_log("READ", filepath, "BLOCKED - outside allowed directories")
        return f"ERROR: Access denied. Files can only be read from: {ALLOWED_DIRECTORIES}"

    # Attempt to read the file
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        audit_log("READ", filepath, "SUCCESS")
        return content
    except FileNotFoundError:
        audit_log("READ", filepath, "NOT_FOUND")
        return f"ERROR: File not found: {filepath}"
    except PermissionError:
        audit_log("READ", filepath, "PERMISSION_DENIED")
        return f"ERROR: Permission denied: {filepath}"
    except Exception as e:
        audit_log("READ", filepath, f"ERROR - {str(e)}")
        return f"ERROR: {str(e)}"


@mcp.tool()
def check_file_safety(filepath: str) -> str:
    """Check if a file path is safe to access.

    Validates that a file path is within allowed directories and
    doesn't contain dangerous patterns.

    Args:
        filepath: The file path to validate
    """
    # SECURITY FIX 4: Clean implementation - NO hidden instructions!
    # The vulnerable version had malicious instructions here

    # Sanitize the path first
    filepath = sanitize_path(filepath)

    # Check for dangerous patterns
    dangerous_patterns = ['../', '/etc/', '/root/', '/home/', '~', '/proc/', '/sys/']
    for pattern in dangerous_patterns:
        if pattern in filepath:
            audit_log("CHECK_SAFETY", filepath, f"DANGEROUS - contains '{pattern}'")
            return f"WARNING: {filepath} contains dangerous pattern '{pattern}'"

    # Check if in allowed directories
    if is_path_allowed(filepath):
        audit_log("CHECK_SAFETY", filepath, "SAFE - in allowed directory")
        return f"OK: {filepath} is in an allowed directory and appears safe to access"

    audit_log("CHECK_SAFETY", filepath, "OUTSIDE_ALLOWED")
    return f"WARNING: {filepath} is outside allowed directories ({ALLOWED_DIRECTORIES})"


@mcp.tool()
def list_files(directory: str) -> str:
    """List files in an allowed directory.

    Only directories within the allowlist can be listed.

    Args:
        directory: Path to the directory to list
    """
    # Sanitize the path
    directory = sanitize_path(directory)

    # Check if directory is allowed
    if not is_path_allowed(directory + "/"):
        audit_log("LIST", directory, "BLOCKED - outside allowed directories")
        return f"ERROR: Access denied. Can only list: {ALLOWED_DIRECTORIES}"

    try:
        files = os.listdir(directory)
        audit_log("LIST", directory, f"SUCCESS - {len(files)} files")
        return "\n".join(files) if files else "Directory is empty"
    except FileNotFoundError:
        audit_log("LIST", directory, "NOT_FOUND")
        return f"ERROR: Directory not found: {directory}"
    except PermissionError:
        audit_log("LIST", directory, "PERMISSION_DENIED")
        return f"ERROR: Permission denied: {directory}"
    except Exception as e:
        audit_log("LIST", directory, f"ERROR - {str(e)}")
        return f"ERROR: {str(e)}"


if __name__ == "__main__":
    # Run as HTTP server for Docker networking
    # Uses SSE transport for inter-container communication
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8001"))
    logger.info(f"Starting SecureFileServer on {host}:{port}")
    logger.info(f"Allowed directories: {ALLOWED_DIRECTORIES}")
    mcp.run(transport="sse", host=host, port=port)
