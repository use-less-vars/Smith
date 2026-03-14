from pydantic import Field
from .base import ToolBase

class Final(ToolBase):
    """Final answer tool. Use this when you answer a user question and want to output the final answer."""
    content: str = Field(description="The final answer text")

    def execute(self) -> str:
        return self._truncate_output(self.content)