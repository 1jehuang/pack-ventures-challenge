# Claude Agent SDK - Python API Reference

This document provides a quick reference for using the Claude Agent SDK in Python.

## Installation

```bash
pip install claude-agent-sdk
```

**Requirements:**
- Python 3.10+
- ANTHROPIC_API_KEY environment variable (cannot use Claude Code subscription)

## Authentication

The SDK requires an API key (pay-per-use model):

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

⚠️ **Important:** You cannot use your Claude Code/Pro/Max subscription with the SDK. You must use an API key with pay-per-token billing.

## Basic Usage

### Simple Query (One-shot)

For simple, stateless queries:

```python
import anyio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

### Query with Options

Enable tools and configure the agent:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch", "WebFetch"],
        system_prompt="You are a helpful research assistant.",
        model="claude-sonnet-4-5-20250929",
        max_turns=5
    )

    async for message in query(
        prompt="Find the founders of Airbnb",
        options=options
    ):
        # Extract text from assistant messages
        if hasattr(message, 'role') and message.role == 'assistant':
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'type') and block.type == 'text':
                        print(block.text)

anyio.run(main)
```

## ClaudeAgentOptions

Common configuration options:

| Option | Type | Description |
|--------|------|-------------|
| `allowed_tools` | `list[str]` | List of tools to enable (e.g., `["WebSearch", "WebFetch", "Read", "Write"]`) |
| `disallowed_tools` | `list[str]` | List of tools to explicitly disable |
| `system_prompt` | `str` | Custom system prompt for the agent |
| `model` | `str` | Model ID (e.g., `"claude-sonnet-4-5-20250929"`) |
| `max_turns` | `int` | Maximum number of conversation turns |
| `permission_mode` | `str` | Permission handling: `"default"`, `"acceptEdits"`, `"bypassPermissions"` |
| `cwd` | `str \| Path` | Working directory for file operations |

## Available Tools

Built-in tools you can enable via `allowed_tools`:

- **WebSearch** - Search the web for information
- **WebFetch** - Fetch content from URLs
- **Read** - Read files
- **Write** - Write files
- **Edit** - Edit files
- **Bash** - Execute bash commands
- **Glob** - Find files matching patterns
- **Grep** - Search file contents

## When to Use query() vs ClaudeSDKClient

### Use `query()` when:
- Simple one-off questions
- Batch processing of independent prompts
- Stateless interactions
- You know all inputs upfront

### Use `ClaudeSDKClient` when:
- Interactive conversations with follow-ups
- Need bidirectional communication
- Long-running sessions with state
- Need to interrupt or send follow-up messages

## Example: Research Assistant

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def research_company(company_name: str, url: str):
    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch", "WebFetch"],
        system_prompt="""You are a research assistant.
Return only facts in JSON format.""",
        model="claude-sonnet-4-5-20250929",
        max_turns=3
    )

    prompt = f"Research {company_name} at {url} and return key facts as JSON"

    response = ""
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, 'role') and message.role == 'assistant':
            for block in message.content:
                if block.type == 'text':
                    response += block.text

    return response
```

## Error Handling

```python
try:
    async for message in query(prompt="...", options=options):
        # Process messages
        pass
except Exception as e:
    print(f"Error: {e}")
    # Handle errors (API errors, network issues, etc.)
```

## Resources

- Official Docs: https://docs.claude.com/en/docs/claude-code/sdk/sdk-python
- GitHub: https://github.com/anthropics/claude-agent-sdk-python
- Blog Post: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk

## Key Differences from Claude Code CLI

| Feature | Claude Code CLI | Claude Agent SDK |
|---------|----------------|------------------|
| Authentication | Subscription OR API key | API key only |
| Billing | Flat subscription fee | Pay-per-token |
| Use Case | Interactive development | Embedded in applications |
| Installation | `npm install -g @anthropic-ai/claude-code` | `pip install claude-agent-sdk` |
