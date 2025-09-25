"""
Base Tool Class - Common interface for all market analysis tools
"""
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.utils.logging import setup_logging

logger = setup_logging("market_tools")


class BaseTool(ABC):
    """Base class for all market analysis tools"""

    def __init__(self, tool_id: str, name: str, description: str):
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.logger = setup_logging(f"tool_{tool_id}")

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments"""
        pass

    @abstractmethod
    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        pass

    def validate_arguments(self, arguments: Dict[str, Any], required_args: list) -> None:
        """Validate that required arguments are present"""
        missing_args = [arg for arg in required_args if arg not in arguments]
        if missing_args:
            raise ValueError(f"Missing required arguments: {', '.join(missing_args)}")

    async def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Handle errors and return standardized error response"""
        error_message = str(error)
        self.logger.error(f"Tool {self.tool_id} error{f' in {context}' if context else ''}: {error_message}")

        return {
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": error_message,
                "tool": self.tool_id,
                "context": context
            },
            "data": None
        }

    def create_success_response(self, data: Any, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized success response"""
        response = {
            "success": True,
            "error": None,
            "data": data,
            "tool": self.tool_id
        }

        if metadata:
            response["metadata"] = metadata

        return response