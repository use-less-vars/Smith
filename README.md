# ThoughtMachine v1.0

An AI agent framework that can execute code securely inside Docker containers.

## Quick Start

1. **Clone the repo** and write your API key into `.env`
2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```
3. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```
4. **Set up Docker** (for secure code execution):
   - Install Docker on your system
   - Build the Docker image:
   ```bash
   docker build -f docker/executor.Dockerfile -t agent-executor .
   ```
5. **Launch the GUI:**
   ```bash
   python3 run_gui.py
   ```
   Configure your provider (base URL, API key from `.env` or enter directly, and choose a model).

6. **Set the workspace** — this directory is mounted into the container and is where the agent can read/write files.

---

## Docker Configuration for Runtime `pip install`

By default, the Docker container has **no network** and a **read‑only home directory**. This is secure but prevents the agent from installing Python packages on the fly (`pip install` fails).

To allow the agent to install packages quickly (seconds, not minutes), you need to **opt‑in** by creating a small JSON policy file on your **host machine**. The file tells the Docker tool which workspaces are trusted to have internet and a writable home.

### Step 1 – Create the security policy file

Create a file at:

- **Linux / macOS / WSL2:** `~/.thoughtmachine/security_policy.json`
- **Windows (native cmd/PowerShell without WSL):** `%USERPROFILE%\.thoughtmachine\security_policy.json`  
  *However, the ThoughtMachine application is designed for Unix‑like paths; we strongly recommend using WSL2 on Windows.*

**File content** (adjust the workspace path pattern to match your project directories):

```json
{
  "/home/your_username/your_workspace_root/*": {
    "docker_network_allowed": true,
    "writable_home": true
  },
  "default": {
    "docker_network_allowed": false,
    "writable_home": false
  }
}
```

- Replace `/home/your_username/your_workspace_root/*` with the actual path where you keep your projects.  
  For example: `/home/joe/ThoughtMachineProjects/*` or `/home/joe/PycharmProjects/*`
- The `*` glob matches any subdirectory. You can also use an exact path (no `*`) for a single project.
- The `default` entry applies to any workspace not matched — it keeps the secure defaults (no network, no writable home).

### Step 2 – Build the Docker image (once)

From the project root, run:

```bash
docker build -t agent-executor -f docker/executor.Dockerfile .
```

The provided Dockerfile is already lean — it contains only system tools (e.g., LaTeX) and **no Python packages**. The agent will install Python packages at runtime as needed.

### Step 3 – Restart the ThoughtMachine application

Stop the agent and start it again so that the Docker tool reads the new policy file.

### Step 4 – Verify it works

Ask the agent to run:

```
pip install --user colorama
```

Then immediately ask:

```
python3 -c "import colorama; print(colorama.__version__)"
```

Both commands should succeed. The installed package will persist across consecutive tool calls within the **idle timeout** (default 600 seconds / 10 minutes).

---

## Advanced: Changing the idle timeout

If your agent needs longer than 10 minutes between commands before the container is destroyed, you can increase the `idle_timeout` parameter when calling `DockerCodeRunner`:

```python
DockerCodeRunner(command="...", idle_timeout=1800)   # 30 minutes
```

---

## Security note

The policy file is **manually created** — the agent cannot modify it. Only workspaces you explicitly list gain internet access and a writable home. All other paths stay locked down. This gives you full control without a GUI.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip install` still says "permission denied" | Check that `writable_home` is `true` for your workspace and that the path pattern matches exactly. Restart the agent. |
| `pip install` cannot reach PyPI | Ensure `docker_network_allowed` is `true` and the container network is `bridge`. Run `docker logs` on the container if needed. |
| Package disappears after a few minutes | The idle timeout expired (default 600s). Increase `idle_timeout`. |
| Workspace path not recognised | Use an absolute path in the policy file. The agent normalises paths (removes trailing slashes). |
