from .base import ToolBase
import os
import fnmatch
import time
from pathlib import Path
from pydantic import Field
from typing import Optional

class FileLister(ToolBase):
    """Lists files in a directory with optional recursion, pattern filtering, and sorting."""
    
    directory: str = Field(description="Directory to list files from")
    recursive: bool = Field(default=False, description="If True, list files recursively in subdirectories")
    pattern: str = Field(default="*", description="Glob pattern to filter files (e.g., '*.py', 'data_*.txt')")
    sort_by: str = Field(default="name", description="Sort order: 'name', 'size', or 'modified'")
    
    def execute(self) -> str:
        try:
            # Normalize directory path
            directory = os.path.normpath(self.directory)
            if not os.path.exists(directory):
                return f"Error: Directory '{directory}' does not exist."
            if not os.path.isdir(directory):
                return f"Error: '{directory}' is not a directory."
            
            file_entries = []  # each entry: (relative_path, full_path, size, mtime)
            
            if self.recursive:
                for root, dirs, files in os.walk(directory):
                    rel_root = os.path.relpath(root, directory)
                    if rel_root == ".":
                        rel_root = ""
                    for file in files:
                        if fnmatch.fnmatch(file, self.pattern):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.join(rel_root, file) if rel_root else file
                            try:
                                size = os.path.getsize(full_path)
                                mtime = os.path.getmtime(full_path)
                            except (OSError, PermissionError):
                                size = -1
                                mtime = -1
                            file_entries.append((rel_path, full_path, size, mtime))
            else:
                # List only immediate files in directory
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if entry.is_file() and fnmatch.fnmatch(entry.name, self.pattern):
                            full_path = entry.path
                            rel_path = entry.name
                            try:
                                size = entry.stat().st_size
                                mtime = entry.stat().st_mtime
                            except (OSError, PermissionError):
                                size = -1
                                mtime = -1
                            file_entries.append((rel_path, full_path, size, mtime))
            
            # Sort entries
            if self.sort_by == "name":
                file_entries.sort(key=lambda x: x[0].lower())
            elif self.sort_by == "size":
                file_entries.sort(key=lambda x: x[2])
            elif self.sort_by == "modified":
                file_entries.sort(key=lambda x: x[3], reverse=True)  # newest first
            else:
                return f"Error: Invalid sort_by value '{self.sort_by}'. Must be 'name', 'size', or 'modified'."
            
            # Build output string
            if not file_entries:
                return f"No files matching pattern '{self.pattern}' in directory '{directory}' (recursive={self.recursive})."
            
            lines = []
            for rel_path, full_path, size, mtime in file_entries:
                # Format size
                if size >= 0:
                    size_str = f"{size:,} bytes"
                else:
                    size_str = "?"
                # Format modification time
                if mtime >= 0:
                    time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
                else:
                    time_str = "?"
                # Indent subdirectory files when recursive
                indent = ""
                if self.recursive and os.path.dirname(rel_path):
                    indent = "    "
                lines.append(f"{indent}{rel_path} ({size_str}, modified {time_str})")
            
            header = f"Files in {directory} (pattern='{self.pattern}', recursive={self.recursive}, sorted by {self.sort_by}):"
            return header + "\n" + "\n".join(lines)
            
        except Exception as e:
            return f"Error listing files: {e}"