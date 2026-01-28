---
name: create-hooks
description: Create Cursor hooks to observe, control, and extend the agent loop. Use when the user asks about hooks, wants to run formatters after edits, add auditing, gate risky operations, or automate agent behavior.
---

# Creating Cursor Hooks

Hooks let you observe, control, and extend the agent loop using custom scripts.

## Quick Start

1. Create `hooks.json` at project level (`.cursor/hooks.json`) or user level (`~/.cursor/hooks.json`)
2. Create hook scripts in `.cursor/hooks/` (project) or `~/.cursor/hooks/` (user)
3. Make scripts executable: `chmod +x script.sh`
4. Restart Cursor

## Configuration

```json
{
  "version": 1,
  "hooks": {
    "afterFileEdit": [{ "command": ".cursor/hooks/format.sh" }]
  }
}
```

**Path rules:**
- Project hooks (`.cursor/hooks.json`): paths relative to project root (`.cursor/hooks/script.sh`)
- User hooks (`~/.cursor/hooks.json`): paths relative to `~/.cursor/` (`./hooks/script.sh`)

## Hook Types

### Command-Based (default)
Execute shell scripts that receive JSON via stdin and return JSON via stdout.

```json
{
  "command": ".cursor/hooks/script.sh",
  "timeout": 30,
  "matcher": "curl|wget"
}
```

**Exit codes:** `0` = success, `2` = block action, other = fail-open

## CRITICAL: JSON Output Requirements

**All stdout from hook scripts must be valid JSON.** The agent parses stdout as JSON - any non-JSON output (command output, error messages, debug prints) will corrupt parsing and break the hook.

**Rules:**
1. **Suppress all command output** - redirect both stdout AND stderr: `command >/dev/null 2>&1`
2. **Capture output safely** - if you need command output, capture it and encode as JSON:
   ```bash
   output=$(some_command 2>&1)
   if [[ $? -ne 0 ]]; then
     echo "{\"status\": \"error\", \"output\": $(echo "$output" | jq -Rs .)}"
     exit 1
   fi
   ```
3. **Every exit path must output JSON** - even for skipped/no-op cases, return `{}` or a status object
4. **Use `jq -Rs .`** to safely escape strings for JSON (handles newlines, quotes, special chars)

**Common mistake:**
```bash
# BAD - ruff output goes to stdout, corrupts JSON
ruff format "$file_path"
echo '{"status": "okay"}'

# GOOD - output suppressed, only JSON goes to stdout  
ruff format "$file_path" >/dev/null 2>&1
echo '{"status": "okay"}'
```

### Prompt-Based
Use LLM to evaluate a condition:

```json
{
  "type": "prompt",
  "prompt": "Does this command look safe? Only allow read-only operations.",
  "timeout": 10
}
```

## Available Hook Events

| Event | When | Can Block |
|-------|------|-----------|
| `sessionStart` | Conversation created | Yes |
| `sessionEnd` | Conversation ends | No |
| `preToolUse` | Before any tool | Yes |
| `postToolUse` | After tool success | No |
| `postToolUseFailure` | After tool fails | No |
| `subagentStart` | Before Task tool spawns | Yes |
| `subagentStop` | After subagent completes | No |
| `beforeShellExecution` | Before shell command | Yes |
| `afterShellExecution` | After shell command | No |
| `beforeMCPExecution` | Before MCP tool | Yes (fail-closed) |
| `afterMCPExecution` | After MCP tool | No |
| `beforeReadFile` | Before reading file | Yes (fail-closed) |
| `afterFileEdit` | After editing file | No |
| `beforeSubmitPrompt` | Before sending prompt | Yes |
| `preCompact` | Before context compaction | No |
| `stop` | Agent loop ends | No (can followup) |
| `beforeTabFileRead` | Before Tab reads file | Yes |
| `afterTabFileEdit` | After Tab edits file | No |

## Common Input Fields (all hooks)

```json
{
  "conversation_id": "string",
  "generation_id": "string", 
  "model": "string",
  "hook_event_name": "string",
  "workspace_roots": ["<path>"]
}
```

## Hook Recipes

### Formatter after edits

```bash
#!/bin/bash
# .cursor/hooks/format.sh
input=$(cat)
file_path=$(echo "$input" | jq -r '.file_path')

# Skip non-Python files
if [[ "$file_path" != *.py ]]; then
  echo '{"status": "skipped"}'
  exit 0
fi

# Run formatter, capture output for error reporting
output=$(ruff format "$file_path" 2>&1)
if [[ $? -ne 0 ]]; then
  echo "{\"status\": \"error\", \"tool\": \"ruff\", \"output\": $(echo "$output" | jq -Rs .)}"
  exit 1
fi

echo '{"status": "okay"}'
exit 0
```

```json
{ "hooks": { "afterFileEdit": [{ "command": ".cursor/hooks/format.sh" }] } }
```

### Audit logging

```bash
#!/bin/bash
# .cursor/hooks/audit.sh
json_input=$(cat)
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$timestamp] $json_input" >> /tmp/agent-audit.log
echo '{"status": "logged"}'
exit 0
```

### Block dangerous commands

```bash
#!/bin/bash
# .cursor/hooks/block-dangerous.sh
input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

# Block rm -rf, drop table, etc.
if [[ "$command" =~ rm[[:space:]]+-rf ]] || [[ "$command" =~ DROP[[:space:]]+TABLE ]]; then
  cat << EOF
{"permission": "deny", "user_message": "Dangerous command blocked", "agent_message": "This command was blocked by a safety hook."}
EOF
  exit 0
fi

echo '{"permission": "allow"}'
```

```json
{
  "hooks": {
    "beforeShellExecution": [{ "command": ".cursor/hooks/block-dangerous.sh" }]
  }
}
```

### Ask permission for git commands

```bash
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

if [[ "$command" =~ ^git[[:space:]] ]]; then
  cat << EOF
{"permission": "ask", "user_message": "Git command requires approval: $command"}
EOF
else
  echo '{"permission": "allow"}'
fi
```

### Auto-retry on failure (stop hook)

```json
// Input: { "status": "completed|aborted|error", "loop_count": 0 }
// Output: { "followup_message": "..." } to auto-continue
```

```bash
#!/bin/bash
input=$(cat)
status=$(echo "$input" | jq -r '.status')
loop_count=$(echo "$input" | jq -r '.loop_count')

if [[ "$status" == "error" ]] && [[ "$loop_count" -lt 2 ]]; then
  echo '{"followup_message": "Please try again with a different approach."}'
else
  echo '{}'
fi
```

## Permission Responses

For `beforeShellExecution`, `beforeMCPExecution`, `beforeReadFile`:

```json
{
  "permission": "allow" | "deny" | "ask",
  "user_message": "<shown to user>",
  "agent_message": "<sent to agent>"
}
```

## Matchers

Filter when hooks run:

```json
{
  "hooks": {
    "preToolUse": [{ "command": "./validate.sh", "matcher": "Shell|Write" }],
    "beforeShellExecution": [{ "command": "./check.sh", "matcher": "curl|wget" }],
    "subagentStart": [{ "command": "./validate.sh", "matcher": "explore|shell" }]
  }
}
```

## Environment Variables

Available to all hooks:
- `CURSOR_PROJECT_DIR` - Workspace root
- `CURSOR_VERSION` - Cursor version
- `CURSOR_USER_EMAIL` - User email (if logged in)

## Debugging

- Check **Cursor Settings > Hooks** tab for configured/executed hooks
- Check **Hooks** output channel for errors
- Restart Cursor after changing `hooks.json`
