# agent/config/__init__.py
"""
Configuration module for ThoughtMachine agent.
"""

from .models import AgentConfig
from .loader import (
    load_default_config,
    load_config,
    save_config,
    validate_config,
    update_config,
    get_config_paths,
)
from .preset import Preset, PresetLoader, get_preset_loader

__all__ = [
    'AgentConfig',
    'load_default_config',
    'load_config',
    'save_config',
    'validate_config',
    'update_config',
    'get_config_paths',
    'Preset',
    'PresetLoader',
    'get_preset_loader',
]