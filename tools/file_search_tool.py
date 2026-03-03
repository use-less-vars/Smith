from .base import ToolBase
import os
import fnmatch
from pathlib import Path
from pydantic import Field
from typing import List, Optional

class FileSearchTool(ToolBase):
    """Search for patterns across multiple files or directories."""
    
    pattern: str = Field(description="String pattern to search for (case-insensitive by default)")
    filenames: Optional[List[str]] = Field(default=None, description="List of file paths to search in. If not provided, use directory parameter.")
    directory: Optional[str] = Field(default=None, description="Directory to search recursively (if filenames not provided)")
    case_sensitive: bool = Field(default=False, description="If True, perform case-sensitive search")
    max_results: int = Field(default=50, description="Maximum number of matches to return")
    
    def execute(self) -> str:
        try:
            # Determine which files to search
            files_to_search = []
            if self.filenames:
                for f in self.filenames:
                    if os.path.isdir(f):
                        # treat as directory, expand recursively
                        for root, dirs, files in os.walk(f):
                            for file in files:
                                files_to_search.append(os.path.join(root, file))
                    else:
                        files_to_search.append(f)
            elif self.directory:
                if not os.path.isdir(self.directory):
                    return f"Error: '{self.directory}' is not a valid directory."
                for root, dirs, files in os.walk(self.directory):
                    for file in files:
                        files_to_search.append(os.path.join(root, file))
            else:
                return "Error: Either 'filenames' or 'directory' must be provided."
            
            # Limit number of files to prevent excessive scanning (optional)
            if len(files_to_search) > 1000:
                return f"Error: Too many files to search ({len(files_to_search)}). Please narrow your search."
            
            matches = []
            pattern = self.pattern if self.case_sensitive else self.pattern.lower()
            
            for file_path in files_to_search:
                if not os.path.isfile(file_path):
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, start=1):
                            search_line = line if self.case_sensitive else line.lower()
                            if pattern in search_line:
                                matches.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'content': line.rstrip('\n')
                                })
                                if len(matches) >= self.max_results:
                                    break
                except (IOError, PermissionError, UnicodeDecodeError):
                    continue
                if len(matches) >= self.max_results:
                    break
            
            if not matches:
                return "No matches found."
            
            # Group matches by file for readability
            matches_by_file = {}
            for match in matches:
                file = match['file']
                matches_by_file.setdefault(file, []).append(match)
            
            # Build output
            lines = []
            for file, file_matches in matches_by_file.items():
                # Make path relative to current directory for brevity
                try:
                    rel_path = os.path.relpath(file)
                except ValueError:
                    rel_path = file
                lines.append(f"{rel_path}:")
                for match in file_matches[:10]:  # limit per file for readability
                    lines.append(f"  Line {match['line']}: {match['content']}")
                if len(file_matches) > 10:
                    lines.append(f"  ... and {len(file_matches) - 10} more matches in this file")
                lines.append("")
            
            header = f"Found {len(matches)} matches for pattern '{self.pattern}'"
            if self.directory:
                header += f" in directory '{self.directory}'"
            header += f" (case_sensitive={self.case_sensitive}, max_results={self.max_results}):"
            return header + "\n" + "\n".join(lines)
            
        except Exception as e:
            return f"Error searching files: {e}"