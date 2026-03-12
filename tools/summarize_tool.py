from typing import Literal
from pydantic import Field
from .base import ToolBase

class SummarizeTool(ToolBase):
    """Summarize Tool: Write a summary of the conversation and specify how many most recent turns to keep.
    The agent will replace older turns with the summary, preserving the specified number of recent turns."""
    
    summary: str = Field(description="The summary text to insert into the conversation history.")
    keep_recent_turns: int = Field(description="Number of most recent turns to keep (excluding the summary).", ge=0)

    def execute(self) -> str:
        # The actual pruning will be handled by the agent upon detection of this tool.
        # Return a confirmation message.
        return self._truncate_output(f"Summary tool called: will keep {self.keep_recent_turns} recent turns and insert summary.")