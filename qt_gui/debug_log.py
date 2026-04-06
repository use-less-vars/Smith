"""Debug logging utilities for the GUI."""
import os
import datetime
from pathlib import Path

DEBUG_ENABLED = os.environ.get('THOUGHTMACHINE_DEBUG') == '1'
DEBUG_TRUNCATION_LIMIT = int(os.environ.get('THOUGHTMACHINE_DEBUG_TRUNCATION', 100))
DEBUG_LOG_PATH = Path("debug_close.log")


def debug_log(msg: str, level: str = "DEBUG", component: str = "") -> None:
    """Log message to file (and optionally to console based on level and DEBUG_ENABLED).
    
    Levels: DEBUG, INFO, WARNING, ERROR
    When DEBUG_ENABLED is True: all levels go to console
    When DEBUG_ENABLED is False: only WARNING and ERROR go to console
    """
    """Log message to file (and optionally to console based on level and DEBUG_ENABLED).

    Levels: DEBUG, INFO, WARNING, ERROR
    When DEBUG_ENABLED is True: all levels go to console
    When DEBUG_ENABLED is False: only WARNING and ERROR go to console
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    level_prefix = f"[{level}]"
    component_prefix = f"[{component}]" if component else ""

    # Convert message to string for processing
    msg_str = str(msg)

    # Truncate for console output if limit is set (>0)
    console_msg = msg_str
    if DEBUG_TRUNCATION_LIMIT > 0 and len(msg_str) > DEBUG_TRUNCATION_LIMIT:
        console_msg = msg_str[:DEBUG_TRUNCATION_LIMIT] + "..."

    # Always write to file (full message)
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}]{component_prefix}{level_prefix} {msg_str}\n")

    # Console output based on level and DEBUG_ENABLED
    if DEBUG_ENABLED:
        # In debug mode, print everything (truncated)
        print(f"{component_prefix}{level_prefix} {console_msg}")
    elif level in ("WARNING", "ERROR"):
        # Always print warnings and errors even without debug mode (truncated)
        print(f"{component_prefix}{level_prefix} {console_msg}")