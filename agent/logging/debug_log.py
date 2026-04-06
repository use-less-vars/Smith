"""Debug logging utilities for the agent."""
import os
import datetime
from pathlib import Path

# DEBUG_ENABLED determined at runtime from environment variable
DEBUG_LOG_PATH = Path("debug_agent.log")
DEBUG_TRUNCATION_LIMIT = int(os.environ.get('THOUGHTMACHINE_DEBUG_TRUNCATION', 100))


def is_debug_enabled(component: str = "") -> bool:
    """Check if debug output is enabled for a component.
    
    Returns True if THOUGHTMACHINE_DEBUG=1 or DEBUG_{component} is truthy.
    """
    if os.environ.get('THOUGHTMACHINE_DEBUG') == '1':
        return True
    if component:
        # Check component-specific flag (any non-empty value)
        flag_value = os.environ.get(f'DEBUG_{component.upper()}')
        if flag_value is not None and flag_value != '':
            return True
    return False


def debug_log(msg: str, level: str = "DEBUG", component: str = "") -> None:
    """Log message to file (and optionally to console based on level and THOUGHTMACHINE_DEBUG).

    Levels: DEBUG, INFO, WARNING, ERROR
    When THOUGHTMACHINE_DEBUG=1: all levels go to console
    When THOUGHTMACHINE_DEBUG=0: only WARNING and ERROR go to console
    Component-specific debug flags (DEBUG_{component}) also enable console output.
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
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}]{component_prefix}{level_prefix} {msg_str}\n")
    except Exception as e:
        # If file writing fails, just print to console
        print(f"[DEBUG_LOG ERROR] Failed to write to log file: {e}")

    # Console output based on level and debug flags (THOUGHTMACHINE_DEBUG or DEBUG_{component})
    debug_enabled = is_debug_enabled(component)
    if debug_enabled:
        # In debug mode, print everything (truncated)
        print(f"{component_prefix}{level_prefix} {console_msg}")
    elif level in ("WARNING", "ERROR"):
        # Always print warnings and errors even without debug mode (truncated)
        print(f"{component_prefix}{level_prefix} {console_msg}")