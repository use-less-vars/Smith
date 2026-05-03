"""
Security configuration module for Docker tool.

Reads a JSON policy file from ~/.thoughtmachine/security_policy.json
that controls opt-in security relaxation per workspace path.
"""
import json
import os
from typing import Dict, Any


def load_policy(workspace_path: str) -> Dict[str, bool]:
    """Load security policy for a given workspace path.

    Reads ~/.thoughtmachine/security_policy.json and returns
    a policy dict with ``docker_network_allowed`` and ``writable_home`` flags.

    Matching logic:
        - Keys ending with ``*`` are treated as prefix globs
          (e.g. ``/home/jojo/CMEX/*`` matches any path under that directory).
        - Keys without ``*`` require an exact match.
        - An explicit match for the workspace path is preferred.
        - If no explicit match is found, the special ``"default"`` key is used.
        - If the file is missing, unreadable, or no matching key is found,
          both flags default to ``False`` (secure default).

    Args:
        workspace_path: Absolute path to the workspace being used.

    Returns:
        dict with keys ``docker_network_allowed`` (bool) and
        ``writable_home`` (bool).
    """
    config_path = os.path.expanduser("~/.thoughtmachine/security_policy.json")

    try:
        with open(config_path, "r") as f:
            config: Dict[str, Any] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        # File missing, corrupt, or unreadable → secure defaults
        return {"docker_network_allowed": False, "writable_home": False}

    if not isinstance(config, dict):
        return {"docker_network_allowed": False, "writable_home": False}

    workspace_abs = os.path.abspath(workspace_path)

    # First pass: try to find an explicit match
    for pattern, policy in config.items():
        if not isinstance(policy, dict):
            continue
        if _pattern_matches(pattern, workspace_abs):
            return _normalize_policy(policy)

    # Second pass: fallback to "default" key
    default_policy = config.get("default", {})
    if isinstance(default_policy, dict):
        return _normalize_policy(default_policy)

    # No match and no default → secure defaults
    return {"docker_network_allowed": False, "writable_home": False}


def _pattern_matches(pattern: str, workspace_path: str) -> bool:
    """Check if a workspace path matches a policy pattern.

    Supports trailing ``*`` glob patterns as well as exact matches.
    """
    pattern_stripped = pattern.strip()
    if pattern_stripped.endswith("*"):
        prefix = pattern_stripped.rstrip("*").rstrip("/")
        return workspace_path.startswith(prefix)
    else:
        return workspace_path == pattern_stripped


def _normalize_policy(policy: Dict[str, Any]) -> Dict[str, bool]:
    """Normalize a raw policy dict, coercing values to bool."""
    return {
        "docker_network_allowed": bool(policy.get("docker_network_allowed", False)),
        "writable_home": bool(policy.get("writable_home", False)),
    }


def ensure_default_config() -> str:
    """Create a default security policy file if it does not exist.

    Creates ``~/.thoughtmachine/`` directory and writes a template
    ``security_policy.json`` file with a commented example.

    Returns:
        The path to the config file (existing or newly created).
    """
    config_dir = os.path.expanduser("~/.thoughtmachine")
    config_path = os.path.join(config_dir, "security_policy.json")

    if os.path.exists(config_path):
        return config_path

    os.makedirs(config_dir, exist_ok=True)

    template = {
        "default": {
            "docker_network_allowed": False,
            "writable_home": False
        },
        "/home/you/your-workspace/*": {
            "docker_network_allowed": True,
            "writable_home": True
        }
    }

    with open(config_path, "w") as f:
        json.dump(template, f, indent=2)
        f.write("\n")

    return config_path
