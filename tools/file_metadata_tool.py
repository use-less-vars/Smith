from .base import ToolBase
import os
import pathlib
import time
import hashlib
import mimetypes
from pydantic import Field
from typing import Optional, Dict, Any
import stat

class FileMetadataTool(ToolBase):
    """Get comprehensive file metadata including size, timestamps, and content analysis."""
    
    filename: str = Field(description="Path to the file to analyze")
    compute_hash: bool = Field(default=True, description="Compute MD5 and SHA1 hashes of file content")
    detect_language: bool = Field(default=True, description="Attempt to detect programming language")
    analyze_content: bool = Field(default=True, description="Analyze file content (line count, encoding)")
    
    def execute(self) -> str:
        try:
            # Resolve file path
            file_path = pathlib.Path(self.filename)
            if not file_path.exists():
                return f"Error: File '{self.filename}' does not exist."
            
            # Collect basic metadata
            metadata = self._collect_basic_metadata(file_path)
            
            # Collect extended metadata based on parameters
            if self.compute_hash and file_path.is_file():
                metadata.update(self._compute_file_hashes(file_path))
            
            if self.detect_language and file_path.is_file():
                metadata.update(self._detect_language(file_path))
            
            if self.analyze_content and file_path.is_file():
                metadata.update(self._analyze_content(file_path))
            
            # Format output
            return self._format_metadata(metadata, file_path)
            
        except Exception as e:
            return f"Error analyzing file '{self.filename}': {e}"
    
    def _collect_basic_metadata(self, file_path: pathlib.Path) -> Dict[str, Any]:
        """Collect basic file system metadata."""
        metadata = {
            'path': str(file_path.resolve()),
            'name': file_path.name,
            'exists': file_path.exists(),
            'type': 'unknown'
        }
        
        if not file_path.exists():
            return metadata
        
        try:
            stat_info = file_path.stat()
            
            # File type
            if file_path.is_dir():
                metadata['type'] = 'directory'
            elif file_path.is_file():
                metadata['type'] = 'file'
            elif file_path.is_symlink():
                metadata['type'] = 'symlink'
            
            # Basic stats
            metadata['size'] = stat_info.st_size if file_path.is_file() else 0
            metadata['created'] = stat_info.st_ctime
            metadata['modified'] = stat_info.st_mtime
            metadata['accessed'] = stat_info.st_atime
            
            # Permissions
            metadata['permissions'] = stat.filemode(stat_info.st_mode)
            metadata['permissions_octal'] = oct(stat_info.st_mode)[-3:]
            
            # Owner/group (if available)
            try:
                import pwd
                import grp
                metadata['owner'] = pwd.getpwuid(stat_info.st_uid).pw_name
                metadata['group'] = grp.getgrgid(stat_info.st_gid).gr_name
            except (ImportError, KeyError):
                metadata['owner'] = stat_info.st_uid
                metadata['group'] = stat_info.st_gid
            
        except OSError as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def _compute_file_hashes(self, file_path: pathlib.Path) -> Dict[str, Any]:
        """Compute MD5 and SHA1 hashes of file content."""
        hashes = {}
        
        try:
            md5_hash = hashlib.md5()
            sha1_hash = hashlib.sha1()
            
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
                    sha1_hash.update(chunk)
            
            hashes['md5'] = md5_hash.hexdigest()
            hashes['sha1'] = sha1_hash.hexdigest()
            
        except (IOError, OSError) as e:
            hashes['hash_error'] = str(e)
        
        return hashes
    
    def _detect_language(self, file_path: pathlib.Path) -> Dict[str, Any]:
        """Attempt to detect programming language from file extension and content."""
        detection = {}
        
        # MIME type detection
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            detection['mime_type'] = mime_type
        
        # Extension-based language detection
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.toml': 'TOML',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.csv': 'CSV',
            '.sql': 'SQL',
            '.sh': 'Shell Script',
            '.bash': 'Bash Script',
            '.ps1': 'PowerShell',
            '.r': 'R',
            '.jl': 'Julia',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
        }
        
        ext = file_path.suffix.lower()
        if ext in extension_map:
            detection['language'] = extension_map[ext]
            detection['detection_method'] = 'extension'
        
        # Content-based detection (simple heuristics)
        if file_path.is_file() and file_path.suffix.lower() == '':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline(100)
                    
                    # Shebang detection
                    if first_line.startswith('#!'):
                        detection['shebang'] = first_line.strip()
                        if 'python' in first_line.lower():
                            detection['language'] = 'Python'
                            detection['detection_method'] = 'shebang'
                        elif 'bash' in first_line.lower() or 'sh' in first_line.lower():
                            detection['language'] = 'Shell Script'
                            detection['detection_method'] = 'shebang'
            except:
                pass
        
        return detection
    
    def _analyze_content(self, file_path: pathlib.Path) -> Dict[str, Any]:
        """Analyze file content (line count, encoding, etc.)."""
        analysis = {}
        
        if not file_path.is_file():
            return analysis
        
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                analysis['encoding'] = 'UTF-8'
                analysis['line_count'] = len(lines)
                analysis['character_count'] = sum(len(line) for line in lines)
                
                # Count non-empty lines
                non_empty = sum(1 for line in lines if line.strip())
                analysis['non_empty_lines'] = non_empty
                
                # Estimate indentation style (for code files)
                if file_path.suffix.lower() in ['.py', '.js', '.java', '.cpp', '.c']:
                    tabs = sum(line.startswith('\t') for line in lines[:100])
                    spaces_2 = sum(line.startswith('  ') and not line.startswith('   ') for line in lines[:100])
                    spaces_4 = sum(line.startswith('    ') for line in lines[:100])
                    
                    if tabs > spaces_4 and tabs > spaces_2:
                        analysis['indentation'] = 'tabs'
                    elif spaces_4 > spaces_2:
                        analysis['indentation'] = '4 spaces'
                    elif spaces_2 > 0:
                        analysis['indentation'] = '2 spaces'
                
        except UnicodeDecodeError:
            # Try Latin-1 as fallback
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                    analysis['encoding'] = 'Latin-1'
                    analysis['line_count'] = len(lines)
                    analysis['character_count'] = sum(len(line) for line in lines)
                    analysis['non_empty_lines'] = sum(1 for line in lines if line.strip())
            except:
                analysis['encoding'] = 'binary or unknown'
                analysis['line_count'] = 0
        
        except (IOError, OSError) as e:
            analysis['content_error'] = str(e)
        
        return analysis
    
    def _format_metadata(self, metadata: Dict[str, Any], file_path: pathlib.Path) -> str:
        """Format metadata for display."""
        output_lines = []
        
        # Header
        output_lines.append(f"METADATA: {file_path.name}")
        output_lines.append("=" * 60)
        
        # Basic info
        output_lines.append("BASIC INFORMATION:")
        output_lines.append(f"  Path: {metadata.get('path', 'unknown')}")
        output_lines.append(f"  Type: {metadata.get('type', 'unknown').upper()}")
        output_lines.append(f"  Exists: {metadata.get('exists', False)}")
        
        if metadata.get('type') == 'file':
            size = metadata.get('size', 0)
            size_str = self._format_size(size)
            output_lines.append(f"  Size: {size:,} bytes ({size_str})")
        
        # Timestamps
        if 'created' in metadata:
            output_lines.append("")
            output_lines.append("TIMESTAMPS:")
            output_lines.append(f"  Created:  {self._format_timestamp(metadata['created'])}")
            output_lines.append(f"  Modified: {self._format_timestamp(metadata['modified'])}")
            output_lines.append(f"  Accessed: {self._format_timestamp(metadata['accessed'])}")
        
        # Permissions
        if 'permissions' in metadata:
            output_lines.append("")
            output_lines.append("PERMISSIONS:")
            output_lines.append(f"  Mode: {metadata['permissions']} ({metadata.get('permissions_octal', '???')})")
            output_lines.append(f"  Owner: {metadata.get('owner', '?')}")
            output_lines.append(f"  Group: {metadata.get('group', '?')}")
        
        # Language detection
        if self.detect_language:
            output_lines.append("")
            output_lines.append("CONTENT TYPE:")
            if 'language' in metadata:
                output_lines.append(f"  Language: {metadata['language']} ({metadata.get('detection_method', 'unknown')})")
            if 'mime_type' in metadata:
                output_lines.append(f"  MIME Type: {metadata['mime_type']}")
            if 'shebang' in metadata:
                output_lines.append(f"  Shebang: {metadata['shebang']}")
        
        # Content analysis
        if self.analyze_content and metadata.get('type') == 'file':
            output_lines.append("")
            output_lines.append("CONTENT ANALYSIS:")
            if 'encoding' in metadata:
                output_lines.append(f"  Encoding: {metadata['encoding']}")
            if 'line_count' in metadata:
                output_lines.append(f"  Lines: {metadata['line_count']:,}")
                if 'non_empty_lines' in metadata:
                    output_lines.append(f"  Non-empty lines: {metadata['non_empty_lines']:,}")
                if 'character_count' in metadata:
                    output_lines.append(f"  Characters: {metadata['character_count']:,}")
            if 'indentation' in metadata:
                output_lines.append(f"  Indentation: {metadata['indentation']}")
        
        # Hashes
        if self.compute_hash and metadata.get('type') == 'file':
            output_lines.append("")
            output_lines.append("FILE HASHES:")
            if 'md5' in metadata:
                output_lines.append(f"  MD5:    {metadata['md5']}")
            if 'sha1' in metadata:
                output_lines.append(f"  SHA1:   {metadata['sha1']}")
            if 'hash_error' in metadata:
                output_lines.append(f"  Hash Error: {metadata['hash_error']}")
        
        # Errors
        if 'error' in metadata:
            output_lines.append("")
            output_lines.append("ERRORS:")
            output_lines.append(f"  {metadata['error']}")
        
        return "\n".join(output_lines)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 bytes"
        
        units = ['bytes', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{size_bytes} bytes"
        else:
            return f"{size:.2f} {units[unit_index]}"
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as readable string."""
        if timestamp <= 0:
            return "unknown"
        
        try:
            local_time = time.localtime(timestamp)
            formatted = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
            return formatted
        except:
            return "invalid timestamp"