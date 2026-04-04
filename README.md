# Redis Operator MCP Server

Exposes [Redis Operator](https://github.com/jarmstrong158/redis-operator) as an MCP server, giving Claude direct control over your local task orchestration platform.

## What this enables

Instead of clicking through the dashboard, tell Claude what you want:

> "Add a worker that runs my backup script every day at 9am and 5pm"
> "Chain these three scripts together — run the first two in parallel, then the third after both finish"
> "Show me everything that errored in the last hour"
> "Create a folder watcher that moves .pdf files to my Documents folder"

Claude reads the current state, takes action, and confirms the result.

## Requirements

- Redis Operator running at http://127.0.0.1:5000
- Python 3.10+
- Claude Desktop app with MCP support

## Setup

### Automatic (recommended)

If you installed Redis Operator v3.0.2+, the MCP server is **already bundled and auto-registered**. Just:

1. Launch Redis Operator (it writes the MCP entry to Claude Desktop's config on startup)
2. Restart Claude Desktop
3. Done — Claude now has the Redis Operator tools

### Manual

If you need to set it up manually:

**1. Clone or download this MCP server**

```
git clone https://github.com/jarmstrong158/redis-operator-mcp
```

Or just copy `server.py` somewhere convenient.

**2. Add to Claude Desktop config**

Open your Claude Desktop config file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add the MCP server:

```json
{
  "mcpServers": {
    "redis-operator": {
      "command": "python",
      "args": ["C:\\path\\to\\server.py"]
    }
  }
}
```

Replace the path with wherever you put `server.py`.

**3. Start Redis Operator first, then restart Claude Desktop**

Redis Operator must be running before Claude can use the tools. The MCP server connects to it at http://127.0.0.1:5000.

## Available tools

| Tool | What it does |
|------|-------------|
| `list_workers` | Show all workers and chains with status |
| `create_worker` | Register a new scheduled worker |
| `update_worker` | Modify an existing worker |
| `delete_worker` | Remove a worker |
| `pause_worker` | Toggle pause/resume |
| `run_worker_now` | Fire immediately (logged as MANUAL) |
| `get_worker_history` | Last 10 runs for a worker |
| `pause_all_workers` | Pause everything |
| `delete_all_workers` | Wipe all workers and chains |
| `list_chains` | Show all chains |
| `create_chain` | Build a new pipeline |
| `run_chain_now` | Fire a chain immediately |
| `delete_chain` | Remove a chain |
| `get_chain_history` | Last 10 runs for a chain |
| `list_groups` | Show all groups |
| `create_group` | Create a group |
| `delete_group` | Remove a group (unassigns members) |
| `create_worker_from_template` | Use a built-in template |
| `export_all` | Export everything as JSON |
| `get_logs` | Read the debug log |
| `get_redis_status` | Check Redis connection |
| `check_for_update` | Check for newer Redis Operator version |

## Schedule formats

- **fixed**: `"09:00"` or `"09:00,14:30,17:00"` — fires daily at those times
- **interval**: `"2h"`, `"30m"`, `"1h 30m"` — repeating loop
- **cron**: `"0 9 * * 1-5"` — full cron expression

## Parallel chain steps

Assign the same stage number to steps you want to run simultaneously:

```
Stage 0: step A ──┐
Stage 0: step B ──┤ (both run at once, chain waits for both)
                  ↓
Stage 1: step C   (runs after A and B both finish)
```

Default behavior is fully sequential (each step gets its own unique stage).
