# Development Guides

Coding conventions, setup instructions, and development workflows.

## Current Status
- No guides recorded yet.

## Setup
(To be populated)

## Conventions
(To be populated)

## Workflows
(To be populated)

## Logging API Reference
## Logging API Reference

*(Migrated from docs/logging_manual.md — Last validated: 2026-05-05)*

### Adding a Log Statement
```python
from agent.logging import log

log(level: str, tag: str, message: str, data: dict = None)
```

| Parameter | Description | Example |
|-----------|-------------|---------|
| `level` | "DEBUG", "INFO", "WARNING", "ERROR" | `"DEBUG"` |
| `tag` | Hierarchical component name (area.component) | `"tools.file_editor"` |
| `message` | Human-readable description | `"Writing file"` |
| `data` | Optional dict (auto-truncated) | `{"path": p, "size": n}` |

Example:
```python
log("DEBUG", "core.pruning", "Pruning context", {"kept": 5, "removed": 2})
```

### Tag Naming Convention
Use `area.component` format:
- **core** — agent core, session, pruning, config
- **tools** — file_editor, docker, search
- **llm** — anthropic, openai, stepfun
- **ui** — presenter, output_panel, events
- **session** — history_provider, context_builder

### Console Output Control
| Variable | Effect | Default |
|----------|--------|---------|
| `TM_LOG_LEVEL` | Minimum console level | WARNING |
| `TM_LOG_TAGS` | Comma-separated tags to show at DEBUG/INFO | (empty) |
| `DEBUG_<COMP>` | Legacy flag for a single component | – |
| `THOUGHTMACHINE_DEBUG=1` | Firehose (all debug) | – |

Examples:
```bash
# Debug only pruning and all tools
export TM_LOG_LEVEL=DEBUG
export TM_LOG_TAGS=core.pruning,tools.*

# Quick single-component debug
export DEBUG_EVENTBUS=1

# Back to quiet (default)
unset TM_LOG_LEVEL TM_LOG_TAGS DEBUG_EVENTBUS
```

### File Logging (JSONL)
`TM_LOG_FILE_LEVEL` controls minimum level written to JSONL file (default: DEBUG). All logs go to `logs/agent_<session_id>.jsonl`. Rotation: 10 MB, 5 backups.

### Truncation (Prevents Bloat)
| Variable | Default | Applies To |
|----------|---------|------------|
| `TM_DEBUG_TRUNCATE_LENGTH` | 100 | Generic debug messages, dump_messages preview |
| `TM_TOOL_ARGUMENTS_TRUNCATE` | 100 | Tool call arguments |
| `TM_TOOL_RESULT_TRUNCATE` | 100 | Tool call results |
| `TM_RAW_RESPONSE_TRUNCATE` | 100 | Raw LLM responses |
| `TM_CONSOLE_DATA_TRUNCATE` | 200 | Structured data printed to console |
| `TM_CONVERSATION_CONTENT_TRUNCATE` | 10000 | Conversation messages in JSONL |
| `TM_DOCKER_OUTPUT_TRUNCATE` | 10000 | Docker sandbox output |

### Best Practices
- Use **DEBUG** for temporary instrumentation (won't spam unless explicitly enabled)
- Use **INFO** for normal noteworthy events
- Choose a **specific tag** (e.g., `"tools.my_new_tool"`)
- Provide a **data dict** even for minimal context

## DockerCodeRunner Usage
## DockerCodeRunner Usage

*(Migrated from docs/docker_usage.md — Last validated: 2026-05-05)*

### Overview
`DockerCodeRunner` executes shell commands inside a secure, isolated Docker container. Designed for speed and agent-friendliness — especially for runtime `pip install` without rebuilding the image.

### Key Capabilities
- Run any shell command (bash, python, pip, etc.)
- Runtime `pip install --user` — install packages on the fly (seconds, not minutes)
- Persistent container — reused across sequential calls (up to idle timeout, default 600s)
- Network on demand — controlled by JSON policy file (default: no network)
- Writable home directory — `/home/agent` is a tmpfs mount (when `writable_home: true`)
- Read-only root filesystem — system directories cannot be modified

### Security Model
| Feature | Default | Policy-controlled |
|---------|---------|-------------------|
| Network | none | bridge if `docker_network_allowed: true` |
| Home directory | read-only | writable tmpfs if `writable_home: true` |
| Root access | none (user agent) | root not available |
| Capabilities | all dropped (`cap_drop=["ALL"]`) | – |
| Workspace mount | `/workspace` (read-write) | always mounted |

### Security Policy File
Read from `~/.thoughtmachine/security_policy.json` (NOT inside workspace — user-controlled):
```json
{
  "/home/jojo/PycharmProjects/*": {
    "docker_network_allowed": true,
    "writable_home": true
  },
  "default": {
    "docker_network_allowed": false,
    "writable_home": false
  }
}
```
Path patterns support `*` globs. First matching pattern applies; fallback to "default".

### Container Lifecycle
- Deterministic name: `agent-exec-{sha256(workspace_path)[:12]}`
- Reused across calls within same workspace
- Idle timeout (default 600s, configurable)
- State persistence (pip packages) survives only within idle timeout
- Image rebuilt only when `build=True`

### Installing Packages at Runtime
Inside a container with `writable_home: true`:
```python
# First call — install
DockerCodeRunner(command="pip install --user colorama")

# Second call — use
DockerCodeRunner(command="python3 -c 'import colorama; print(colorama.__version__)'")
```
Package goes to `/home/agent/.local`. Available on subsequent calls within idle timeout.

### Configuration (Tool Parameters)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| command | str | – | Shell command to execute |
| timeout | int | 30 | Max execution seconds |
| working_dir | str | /workspace | Working directory inside container |
| environment | dict | None | Environment variables |
| build | bool | False | Force rebuild Docker image |
| image | str | "agent-executor" | Docker image name |
| mem_limit | str | "512m" | Memory limit |
| cpu_quota | int | 50000 | CPU quota (µs per 100ms period) |
| idle_timeout | int | 600 | Seconds of inactivity before teardown |
| script | str | None | Multi-line script (alternative to command) |
| interpreter | str | "bash" | Interpreter for script |

### Return Value
JSON-formatted string with: `success`, `exit_code`, `stdout`, `stderr`, `command`, `duration`, `timed_out`, `error` (on failure).

### Limitations
- No apt-get or system package installation at runtime (requires `build=True` and root)
- No GUI — container has no display/X11
- No persistent home — pip packages ephemeral (lost on container recreation)
- No multi-container orchestration — one container per workspace at a time
- No Docker socket inside container

### Troubleshooting
| Symptom | Likely Cause |
|---------|--------------|
| `pip install --user` fails with permission error | `writable_home` not true in policy |
| pip cannot reach PyPI | `docker_network_allowed` not true |
| Package disappears between calls | Idle timeout exceeded, or policy mismatch |
| Container name changes between calls | Workspace path not normalized (absolute, no trailing slash) |
