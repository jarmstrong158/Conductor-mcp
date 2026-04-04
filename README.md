# Conductor MCP Server

Gives Claude direct control over [Conductor](https://github.com/jarmstrong158/conductor) — your local task orchestration platform. Instead of clicking through a dashboard, tell Claude what you want automated and it does it.

## What this looks like

> **You:** Set up a nightly backup of my Documents folder. Keep the last 5 copies. Email me a summary when it runs.
>
> **Claude:** *(creates a Folder Backup worker with summary_email, schedules it for 2 AM daily)*
> Done — "Nightly Docs Backup" will run at 2:00 AM, keep 5 copies, and email you a confirmation each time.

> **You:** My metrics script at C:\scripts\report.py produces output.xlsx. Run it every weekday at 8:30 PM and email the file to me.
>
> **Claude:** *(uses the Run + Email template, sets cron to weekdays, wires up Gmail)*
> Worker "Daily Metrics Report" created. Firing it now to test... check your email.

> **You:** What failed today?
>
> **Claude:** *(checks logs, pulls worker history)*
> Worker #3 "Uptime Check" failed twice — the target URL returned 503. Last error was at 2:15 PM.

No coding. No config files. No dashboard clicks. Just conversation.

## Setup

### Automatic (recommended)

If you installed Conductor v3.0.2+, the MCP server is **already bundled and auto-registered**:

1. Launch Conductor (it writes the MCP entry to Claude Desktop's config on startup)
2. Restart Claude Desktop
3. Done — Claude now has the Conductor tools

### Manual

1. Clone this repo or copy `server.py` somewhere

```
git clone https://github.com/jarmstrong158/conductor-mcp
```

2. Add to Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "conductor": {
      "command": "python",
      "args": ["C:\\path\\to\\server.py"]
    }
  }
}
```

3. Start Conductor first, then restart Claude Desktop

## Requirements

- Conductor running at http://127.0.0.1:5000
- Python 3.10+
- Claude Desktop with MCP support

## Available Tools

| Tool | What it does |
|------|-------------|
| `list_workers` | Show all workers and chains with status |
| `create_worker` | Register a new scheduled worker |
| `update_worker` | Modify an existing worker |
| `delete_worker` | Remove a worker |
| `pause_worker` | Toggle pause/resume |
| `run_worker_now` | Fire immediately |
| `get_worker_history` | Run history for a worker |
| `pause_all_workers` | Pause everything |
| `delete_all_workers` | Wipe all workers and chains |
| `list_chains` | Show all chains |
| `create_chain` | Build a multi-step pipeline |
| `run_chain_now` | Fire a chain immediately |
| `delete_chain` | Remove a chain |
| `get_chain_history` | Run history for a chain |
| `list_groups` | Show all groups |
| `create_group` | Create a group |
| `delete_group` | Remove a group |
| `create_worker_from_template` | Use a built-in template |
| `export_all` | Export everything as JSON |
| `get_logs` | Read the debug log |
| `get_redis_status` | Check Redis connection |
| `check_for_update` | Check for newer version |

## Schedule Formats

- **Fixed**: `"09:00"` or `"09:00,14:30,17:00"` — fires daily at those times
- **Interval**: `"2h"`, `"30m"`, `"1h 30m"` — repeating loop
- **Cron**: `"0 9 * * 1-5"` — full cron expression

## Parallel Chain Steps

```
Stage 0: step A ──┐
Stage 0: step B ──┤ (both run at once)
                  ↓
Stage 1: step C   (runs after A and B finish)
```

## Templates

| Type | Config | Email |
|------|--------|-------|
| `folder_backup` | source, dest, keep | summary_email |
| `file_cleanup` | folder, pattern, days | summary_email |
| `folder_watcher` | watch, rules [{ext, dest, email_to}] | Per-rule |
| `uptime_check` | url, log_file | alert_email |
| `open_url` | url | — |
| `run_and_email` | script_path, output_file, email_to | Sends file |
