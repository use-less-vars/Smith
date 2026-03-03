from .base import ToolBase
import os
import pathlib
import stat
from pydantic import Field
from typing import Optional, List, Dict, Any
import time

class DirectoryTreeTool(ToolBase):
    """Show recursive directory structure with file counts and sizes."""
    
    directory: str = Field(description="Root directory to show tree structure")
    max_depth: int = Field(default=3, description="Maximum depth to recurse (0 for unlimited)")
    show_hidden: bool = Field(default=False, description="Show hidden files and directories (starting with .)")
    include_sizes: bool = Field(default=True, description="Include file sizes and line counts")
    pattern: str = Field(default="*", description="Glob pattern to filter files (e.g., '*.py', '*.txt')")
    
    def execute(self) -> str:
        try:
            # Resolve directory path
            dir_path = pathlib.Path(self.directory)
            if not dir_path.exists():
                return f"Error: Directory '{self.directory}' does not exist."
            if not dir_path.is_dir():
                return f"Error: '{self.directory}' is not a directory."
            
            # Build tree structure
            tree_data = self._build_tree(dir_path, current_depth=0)
            
            # Generate tree visualization
            output_lines = self._format_tree(tree_data, dir_path)
            
            # Add summary statistics
            summary = self._generate_summary(tree_data)
            output_lines.extend(summary)
            
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"Error generating directory tree: {e}"
    
    def _build_tree(self, dir_path: pathlib.Path, current_depth: int) -> Dict[str, Any]:
        """Recursively build tree structure."""
        if self.max_depth > 0 and current_depth >= self.max_depth:
            return {'type': 'directory', 'path': dir_path, 'children': [], 'file_count': 0, 'total_size': 0}
        
        tree_node = {
            'type': 'directory',
            'path': dir_path,
            'name': dir_path.name,
            'children': [],
            'file_count': 0,
            'total_size': 0,
            'line_count': 0
        }
        
        try:
            entries = list(dir_path.iterdir())
            
            # Filter hidden files if needed
            if not self.show_hidden:
                entries = [e for e in entries if not e.name.startswith('.')]
            
            # Sort: directories first, then files, alphabetically
            entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for entry in entries:
                if entry.is_dir():
                    # Recursively process subdirectory
                    child_node = self._build_tree(entry, current_depth + 1)
                    tree_node['children'].append(child_node)
                    tree_node['file_count'] += child_node['file_count']
                    tree_node['total_size'] += child_node['total_size']
                    tree_node['line_count'] += child_node['line_count']
                elif entry.is_file():
                    # Check pattern filter
                    if not self._matches_pattern(entry.name):
                        continue
                    
                    file_info = self._get_file_info(entry)
                    tree_node['children'].append(file_info)
                    tree_node['file_count'] += 1
                    tree_node['total_size'] += file_info['size']
                    tree_node['line_count'] += file_info.get('line_count', 0)
            
        except (PermissionError, OSError) as e:
            tree_node['error'] = str(e)
        
        return tree_node
    
    def _matches_pattern(self, filename: str) -> bool:
        """Check if filename matches the glob pattern."""
        import fnmatch
        return fnmatch.fnmatch(filename, self.pattern)
    
    def _get_file_info(self, file_path: pathlib.Path) -> Dict[str, Any]:
        """Get detailed information about a file."""
        file_info = {
            'type': 'file',
            'path': file_path,
            'name': file_path.name,
            'size': 0,
            'mtime': None,
            'line_count': 0
        }
        
        try:
            # File size
            stat_info = file_path.stat()
            file_info['size'] = stat_info.st_size
            file_info['mtime'] = stat_info.st_mtime
            
            # Line count (for text files)
            if self.include_sizes:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = 0
                        for line in f:
                            line_count += 1
                            if line_count > 10000:  # Limit for performance
                                break
                        file_info['line_count'] = line_count
                except (UnicodeDecodeError, IOError):
                    # Binary file or unreadable
                    file_info['line_count'] = 0
                    
        except (OSError, PermissionError):
            pass
        
        return file_info
    
    def _format_tree(self, tree_node: Dict[str, Any], root_path: pathlib.Path) -> List[str]:
        """Format tree structure as ASCII tree."""
        output_lines = []
        
        # Root directory
        rel_path = str(tree_node['path'].relative_to(root_path)) if tree_node['path'] != root_path else "."
        if rel_path == ".":
            output_lines.append(f"{tree_node['path'].resolve()}")
        else:
            output_lines.append(f"{rel_path}")
        
        # Recursively format children
        self._format_tree_recursive(tree_node['children'], "", True, output_lines, root_path)
        
        return output_lines
    
    def _format_tree_recursive(self, children: List[Dict[str, Any]], prefix: str, is_last: bool, 
                              output_lines: List[str], root_path: pathlib.Path):
        """Recursive helper for formatting tree."""
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            
            # Determine connector symbols
            if is_last:
                connector = "└── "
                new_prefix = prefix + "    "
            else:
                connector = "├── "
                new_prefix = prefix + "│   "
            
            # Format the entry
            if child['type'] == 'directory':
                line = f"{prefix}{connector}{child['name']}/"
                if self.include_sizes:
                    size_str = self._format_size(child['total_size'])
                    line += f" ({child['file_count']} files, {size_str})"
                output_lines.append(line)
                
                # Recursively process directory children
                self._format_tree_recursive(child['children'], new_prefix, is_last_child, 
                                           output_lines, root_path)
                
            else:  # file
                line = f"{prefix}{connector}{child['name']}"
                if self.include_sizes:
                    size_str = self._format_size(child['size'])
                    line_count = child.get('line_count', 0)
                    if line_count > 0:
                        line += f" ({size_str}, {line_count} lines)"
                    else:
                        line += f" ({size_str})"
                
                # Add modification time if available
                if child.get('mtime'):
                    mtime_str = time.strftime("%Y-%m-%d", time.localtime(child['mtime']))
                    line += f" [modified: {mtime_str}]"
                
                output_lines.append(line)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 bytes"
        
        units = ['bytes', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{size_bytes} bytes"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    def _generate_summary(self, tree_node: Dict[str, Any]) -> List[str]:
        """Generate summary statistics."""
        summary = []
        summary.append("")
        summary.append("SUMMARY:")
        summary.append(f"  Directories: {self._count_directories(tree_node)}")
        summary.append(f"  Files: {tree_node['file_count']}")
        
        if self.include_sizes:
            summary.append(f"  Total size: {self._format_size(tree_node['total_size'])}")
            if tree_node['line_count'] > 0:
                summary.append(f"  Total lines: {tree_node['line_count']:,}")
        
        return summary
    
    def _count_directories(self, tree_node: Dict[str, Any]) -> int:
        """Count total directories in tree."""
        count = 0
        stack = [tree_node]
        
        while stack:
            node = stack.pop()
            if node['type'] == 'directory':
                count += 1
                stack.extend(node['children'])
        
        return count - 1  # Exclude root directory