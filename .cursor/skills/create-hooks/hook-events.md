# Hook Event Reference

Detailed input/output schemas for each hook event.

## sessionStart

Called when a new conversation is created.

```json
// Input
{
  "session_id": "string",
  "is_background_agent": boolean,
  "composer_mode": "agent" | "ask" | "edit"
}

// Output
{
  "env": { "KEY": "value" },           // Set env vars for session
  "additional_context": "string",       // Add to system context
  "continue": true | false,             // Block session if false
  "user_message": "string"              // Show if blocked
}
```

## sessionEnd

Fire-and-forget when conversation ends.

```json
// Input
{
  "session_id": "string",
  "reason": "completed" | "aborted" | "error" | "window_close" | "user_close",
  "duration_ms": number,
  "is_background_agent": boolean,
  "error_message": "string"  // if reason is "error"
}
```

## preToolUse

Before any tool execution. Use matcher to filter by tool type.

```json
// Input
{
  "tool_name": "Shell" | "Read" | "Write" | "Grep" | "LS" | "Delete" | "MCP" | "Task",
  "tool_input": { ... },
  "tool_use_id": "string",
  "cwd": "string",
  "agent_message": "string"
}

// Output
{
  "decision": "allow" | "deny",
  "reason": "string",              // Shown to agent if denied
  "updated_input": { ... }         // Modified tool input
}
```

## postToolUse

After successful tool execution.

```json
// Input
{
  "tool_name": "string",
  "tool_input": { ... },
  "tool_output": "string",
  "tool_use_id": "string",
  "duration": number
}

// Output
{
  "updated_mcp_tool_output": { ... }  // MCP tools only
}
```

## postToolUseFailure

After tool failure.

```json
// Input
{
  "tool_name": "string",
  "tool_input": { ... },
  "error_message": "string",
  "failure_type": "timeout" | "error" | "permission_denied",
  "duration": number,
  "is_interrupt": boolean
}
```

## subagentStart

Before spawning a Task tool subagent.

```json
// Input
{
  "subagent_type": "generalPurpose" | "explore" | "shell",
  "prompt": "string",
  "model": "string"
}

// Output
{
  "decision": "allow" | "deny",
  "reason": "string"
}
```

## subagentStop

When subagent completes.

```json
// Input
{
  "subagent_type": "string",
  "status": "completed" | "error",
  "result": "string",
  "duration": number,
  "agent_transcript_path": "string"
}

// Output
{
  "followup_message": "string"  // Auto-continue with this message
}
```

## beforeShellExecution

Before shell command runs.

```json
// Input
{
  "command": "string",
  "cwd": "string",
  "timeout": number
}

// Output
{
  "permission": "allow" | "deny" | "ask",
  "user_message": "string",
  "agent_message": "string"
}
```

## afterShellExecution

After shell command completes.

```json
// Input
{
  "command": "string",
  "output": "string",
  "duration": number
}
```

## beforeMCPExecution

Before MCP tool runs. **Fail-closed** - blocks on hook failure.

```json
// Input
{
  "tool_name": "string",
  "tool_input": "string (json)",
  "url": "string",      // or
  "command": "string"
}

// Output
{
  "permission": "allow" | "deny" | "ask",
  "user_message": "string",
  "agent_message": "string"
}
```

## afterMCPExecution

After MCP tool completes.

```json
// Input
{
  "tool_name": "string",
  "tool_input": "string",
  "result_json": "string",
  "duration": number
}
```

## beforeReadFile

Before agent reads a file. **Fail-closed**.

```json
// Input
{
  "file_path": "string",
  "content": "string",
  "attachments": [{ "type": "file" | "rule", "filePath": "string" }]
}

// Output
{
  "permission": "allow" | "deny",
  "user_message": "string"
}
```

## afterFileEdit

After agent edits a file.

```json
// Input
{
  "file_path": "string",
  "edits": [{ "old_string": "string", "new_string": "string" }]
}
```

## beforeSubmitPrompt

Before user prompt is sent.

```json
// Input
{
  "prompt": "string",
  "attachments": [{ "type": "file" | "rule", "filePath": "string" }]
}

// Output
{
  "continue": boolean,
  "user_message": "string"  // Shown if blocked
}
```

## preCompact

Before context window compaction. Observational only.

```json
// Input
{
  "trigger": "auto" | "manual",
  "context_usage_percent": number,
  "context_tokens": number,
  "context_window_size": number,
  "message_count": number,
  "messages_to_compact": number,
  "is_first_compaction": boolean
}

// Output
{
  "user_message": "string"
}
```

## stop

When agent loop ends.

```json
// Input
{
  "status": "completed" | "aborted" | "error",
  "loop_count": number  // Times followup already triggered
}

// Output
{
  "followup_message": "string"  // Auto-submit as next user message
}
```

Max 5 auto follow-ups enforced. Can override with `"loop_limit": null` in config.

## afterAgentResponse

After assistant message completes.

```json
// Input
{
  "text": "string"
}
```

## afterAgentThought

After thinking block completes.

```json
// Input
{
  "text": "string",
  "duration_ms": number
}
```

## Tab-Specific Hooks

### beforeTabFileRead

Before Tab reads a file for completions.

```json
// Input
{ "file_path": "string", "content": "string" }

// Output
{ "permission": "allow" | "deny" }
```

### afterTabFileEdit

After Tab edits a file.

```json
// Input
{
  "file_path": "string",
  "edits": [{
    "old_string": "string",
    "new_string": "string",
    "range": {
      "start_line_number": number,
      "start_column": number,
      "end_line_number": number,
      "end_column": number
    },
    "old_line": "string",
    "new_line": "string"
  }]
}
```
