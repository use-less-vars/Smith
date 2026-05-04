DockerCodeRunner – Technical Reference (v1.0)
Overview

DockerCodeRunner is a ThoughtMachine tool that executes shell commands inside a secure, isolated Docker container. It is designed to be fast, secure, and agent‑friendly – especially for installing Python packages at runtime without rebuilding the image.
Key Capabilities

    Run any shell command inside a container (bash, python, pip, etc.).

    Runtime pip install --user – install Python packages on the fly (seconds, not minutes).

    Persistent container – reuse the same container across sequential calls (up to idle timeout).

    Network on demand – controlled by a simple JSON policy file (default: no network).

    Writable home directory – /home/agent is a tmpfs mount, owned by the agent user (UID 1000).

    Read‑only root filesystem – system directories cannot be modified.

    No CAP_CHOWN needed – ownership of tmpfs set via uid/gid mount options.

Security Model
Feature	Default	Policy‑controlled
Network	none	bridge if docker_network_allowed: true
Home directory	read‑only	writable tmpfs if writable_home: true
Root access	none (user agent)	root not available
Capabilities	all dropped (cap_drop=["ALL"])	–
Workspace mount	/workspace (read‑write)	always mounted

The security policy is read from a JSON file on the host (~/.thoughtmachine/security_policy.json). The file uses a flat format:
json

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

Path patterns support * globs. The first matching pattern applies; fallback to "default".

The policy file is not inside the workspace – the agent cannot modify it. The user (human) controls it.
Container Lifecycle

    Container name deterministic: agent-exec-{sha256(workspace_path)[:12]}.

    Reused across consecutive tool calls (same workspace).

    Idle timeout (default 600 seconds, configurable). After no activity, container is stopped and removed.

    State persistence (installed pip packages) survives across calls only within idle timeout. After timeout, a fresh container is created; packages must be reinstalled.

    Image rebuilt only when build=True (rarely needed now).

Installing Python Packages at Runtime

Inside a container with writable_home: true, the agent can run:
bash

pip install --user <package>

The package is installed into /home/agent/.local. On subsequent calls (before idle timeout), the package remains available.

Example:
python

# First call – install
DockerCodeRunner(command="pip install --user colorama")

# Second call – use
DockerCodeRunner(command="python3 -c 'import colorama; print(colorama.__version__)'")

Configuration (Tool Parameters)
Parameter	Type	Default	Description
command	str	–	Shell command to execute
timeout	int	30	Max execution seconds (command‑only, not build)
working_dir	str	/workspace	Working directory inside container (absolute under /workspace)
environment	dict	None	Environment variables
build	bool	False	Force rebuild Docker image (rarely needed)
image	str	"agent-executor"	Docker image name
mem_limit	str	"512m"	Memory limit
cpu_quota	int	50000	CPU quota (µs per 100ms period)
idle_timeout	int	600	Seconds of inactivity before container is destroyed
script	str	None	Multi‑line script (alternative to command)
interpreter	str	"bash"	Interpreter for script
Return Value

Returns a JSON‑formatted string:
json

{
  "success": bool,
  "exit_code": int,
  "stdout": str,
  "stderr": str,
  "command": str,
  "duration": float,
  "timed_out": bool,
  "error": str (only on failure)
}

Limitations

    No apt-get or system package installation at runtime – requires rebuild (build=True) and root (cap_drop prevents it).

    No GUI – container has no display, no X11 socket.

    No persistent home – pip packages are ephemeral (lost on container recreation).

    No multi‑container orchestration – one container per workspace at a time.

    No Docker socket inside container – container cannot create child containers.

Troubleshooting Checklist
Symptom	Likely cause
pip install --user fails with permission error	writable_home not true in policy, or container recreated before second call
pip install cannot reach PyPI	docker_network_allowed not true in policy, or network not bridge
Package disappears between calls	Idle timeout exceeded, or policy mismatch causing container recreation
ModuleNotFoundError after install	Same as above – container reused incorrectly
Container name changes between calls	Workspace path not normalized (absolute, no trailing slash)
Interaction with Other ThoughtMachine Components

    Security layer (CapabilityRegistry) – only checks whether the whole DockerCodeRunner tool is allowed. Does not inspect individual parameters.

    File tools – cannot write to host paths outside workspace; policy file must be placed manually by user.

    Workspace jail – container only sees /workspace (the mounted project directory). No access to other host directories.

This document describes the state after all fixes (May 2026). For questions, refer to the code in tools/docker_code_runner.py and docker_executor.py.