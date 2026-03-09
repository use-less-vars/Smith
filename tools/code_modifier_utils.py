"""
Helper utilities for CodeModifier operations, enabling non-destructive modifications
and batch operations across multiple files.
"""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import difflib
import libcst as cst
import textwrap
import os

from .code_modifier import CodeModifier


def apply_code_modifier(
    file_path: Path,
    operation: str,
    **kwargs
) -> Tuple[bool, str, str]:
    """
    Apply a CodeModifier operation to a file in memory.
    
    Returns:
        (success, new_content, error_message)
        - success: bool indicating if modification succeeded
        - new_content: if success is True, the modified source code as string;
          if success is False, empty string
        - error_message: if success is False, error description; else empty string
    
    Raises:
        ValueError if operation is invalid or required parameters missing.
    """
    # Read source
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception as e:
        return False, "", f"Error reading file: {e}"
    
    # Parse module
    try:
        module = cst.parse_module(source)
    except Exception as e:
        return False, "", f"Error parsing file: {e}"
    
    # Create a CodeModifier instance with the given parameters.
    # The file_path argument is required but not used for writing.
    # We'll pass it as a string.
    try:
        modifier = CodeModifier(file_path=str(file_path), operation=operation, **kwargs)
    except Exception as e:
        return False, "", f"Invalid parameters: {e}"
    
    # Map operation to internal method
    method_map = {
        'add_function': modifier._add_function,
        'add_method': modifier._add_method,
        'add_import': modifier._add_import,
        'add_class': modifier._add_class,
        'replace_function_body': modifier._replace_function_body,
        'modify_function': modifier._modify_function,
    }
    
    if operation not in method_map:
        return False, "", f"Unsupported operation: {operation}"
    
    # Call the internal method
    try:
        new_module, msg = method_map[operation](module)
    except Exception as e:
        return False, "", f"Error during operation: {e}"
    
    if new_module is None:
        return False, "", msg  # error message from internal method
    
    new_source = new_module.code
    return True, new_source, ""


def compute_diff(original: str, modified: str, file_path: Path) -> str:
    """
    Compute unified diff between original and modified content.
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines, modified_lines,
        fromfile=str(file_path),
        tofile=str(file_path),
        lineterm=""
    )
    return "".join(diff)