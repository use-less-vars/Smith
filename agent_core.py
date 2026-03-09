# agent_core.py
import json
import logging
import os
from typing import Optional, Callable, List, Any, Dict
from openai import OpenAI
from pydantic import BaseModel, ValidationError, Field

from tools import TOOL_CLASSES, SIMPLIFIED_TOOL_CLASSES
from tools.base import ToolBase
from tools.final import Final
from tools.request_user_interaction import RequestUserInteraction
from tools.utils import model_to_openai_tool
from fast_json_repair import loads as repair_loads


# Import logging module
try:
    from agent_logging import create_logger, AgentLogger, LogEventType, LogLevel
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    create_logger = None
    AgentLogger = None
    LogEventType = None
    LogLevel = None 

class AgentConfig(BaseModel):
    api_key: str
    model: str = "deepseek-reasoner"
    temperature: float = 0.2
    max_turns: int = 30
    extra_system: Optional[str] = None
    stop_check: Optional[Callable[[], bool]] = None
    tool_classes: Optional[List[type]] = None   #
    initial_conversation: Optional[List[Dict[str, Any]]] = None
    max_history_turns: Optional[int] = None
    max_tokens: Optional[int] = None
    keep_initial_query: bool = True
    keep_system_messages: bool = True
    initial_input_tokens: int = 0
    initial_output_tokens: int = 0
    
    # Logging configuration
    enable_logging: bool = Field(default=True, description="Enable agent logging")
    log_dir: str = Field(default="./logs", description="Directory for log files")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    enable_file_logging: bool = Field(default=True, description="Write logs to files")
    enable_console_logging: bool = Field(default=False, description="Print logs to console")
    jsonl_format: bool = Field(default=True, description="Use JSONL format for log files")
    max_file_size_mb: int = Field(default=10, description="Maximum log file size in MB before rotation")
    max_backup_files: int = Field(default=5, description="Maximum number of backup log files to keep")
    session_id: Optional[str] = Field(default=None, description="Unique session ID for logging (auto-generated if None)")
    
    class Config:
        extra = "ignore"  # Allow backward compatibility with older configs
def prune_conversation_history(conversation: List[Dict[str, Any]], config: AgentConfig) -> List[Dict[str, Any]]:
    """Prune conversation history based on config settings."""
    if config.max_history_turns is None and config.max_tokens is None:
        return conversation
    
    # Separate system messages and other messages
    system_messages = []
    other_messages = []
    for msg in conversation:
        if msg.get("role") == "system":
            system_messages.append(msg)
        else:
            other_messages.append(msg)
    
    # If no pruning needed for other messages, just return
    if not other_messages:
        return conversation
    
    # Apply turn-based pruning if configured
    if config.max_history_turns is not None:
        # Group messages by turns starting from user messages
        turns = []
        current_turn = []
        for msg in other_messages:
            if msg.get("role") == "user":
                if current_turn:
                    turns.append(current_turn)
                current_turn = [msg]
            else:
                current_turn.append(msg)
        if current_turn:
            turns.append(current_turn)
        
        # Determine how many turns to keep
        turns_to_keep = config.max_history_turns
        if turns_to_keep <= 0:
            kept_turns = []
        elif config.keep_initial_query and turns:
            # Always keep the first turn (initial query)
            if turns_to_keep == 1:
                # Keep only first turn
                kept_turns = [turns[0]]
            else:
                # Keep first turn plus recent turns
                if len(turns) <= turns_to_keep:
                    kept_turns = turns
                else:
                    # Keep first turn + (turns_to_keep-1) most recent turns
                    recent_turns = turns[-(turns_to_keep-1):]
                    kept_turns = [turns[0]] + recent_turns
        else:
            # Just keep most recent turns
            kept_turns = turns[-turns_to_keep:] if turns_to_keep > 0 else []
        
        # Flatten kept turns
        pruned_other = []
        for turn in kept_turns:
            pruned_other.extend(turn)
        
        # Combine with system messages
        result = system_messages + pruned_other if config.keep_system_messages else pruned_other
        return result
    
    # TODO: Implement token-based pruning
    return conversation
def run_agent_stream(query: str, config: AgentConfig):
    """
    Backward compatibility wrapper that creates an Agent instance and processes the query.
    """
    from agent import Agent
    agent = Agent(config, initial_conversation=config.initial_conversation)
    yield from agent.process_query(query)
    
