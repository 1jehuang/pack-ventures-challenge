#!/usr/bin/env python3
"""
Founder Finder Tool
Uses Claude Agent SDK to automatically find founder names for a list of companies.
"""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import List, Dict
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Load .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value


def parse_companies_file(filepath: str) -> List[Dict[str, str]]:
    """
    Parse the companies.txt file to extract company names and URLs.

    Args:
        filepath: Path to the companies.txt file

    Returns:
        List of dicts with 'name' and 'url' keys
    """
    companies = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Extract company name and URL using regex
            # Format: "Company Name (https://url.com)"
            match = re.match(r'^(.+?)\s*\((.+?)\)$', line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                companies.append({'name': name, 'url': url})
            else:
                # Fallback: treat entire line as company name
                companies.append({'name': line, 'url': ''})

    return companies


def setup_conversation_log(company_name: str) -> Path:
    """Create a conversation log file for a company"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Sanitize company name for filename
    safe_name = company_name.replace(" ", "_").replace("/", "_")
    log_file = logs_dir / f"{safe_name}_conversation.log"

    # Clear existing log file
    with open(log_file, 'w') as f:
        f.write(f"=== Conversation Log for {company_name} ===\n")
        f.write(f"Started at: {Path(__file__).parent}\n\n")

    return log_file


def log_to_file(log_file: Path, message: str):
    """Write a message to the log file with auto-flush"""
    with open(log_file, 'a') as f:
        f.write(message + "\n")
        f.flush()  # Force write to disk immediately


async def find_founders(company_name: str, company_url: str) -> List[str]:
    """
    Use Claude Agent SDK to find founders for a given company.

    Approach:
    - Uses the Claude Agent SDK's query() function with web search enabled
    - The agent searches for founder information online
    - Parses the response to extract a clean list of names

    Args:
        company_name: Name of the company
        company_url: URL of the company website

    Returns:
        List of founder names (empty list if not found)
    """
    # Configure agent options with web search capabilities
    # allowed_tools: Enable WebSearch and WebFetch for finding founder info online
    # system_prompt: Allows agent to think and show intermediate progress
    # model: Use Claude Sonnet 4.5 for high-quality responses
    # max_turns: Allow up to 10 turns for thorough research
    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch", "WebFetch"],
        system_prompt="""You are a research assistant specialized in finding company founders.

Your task: Find the names of the original founders/co-founders of companies.

Rules:
- Find ONLY actual founders/co-founders (people who started the company)
- Do NOT include advisors, investors, board members, or employees
- Focus on current/original founders, not interim CEOs or replacements

Most companies should be easy to find - search once and return your final answer immediately.
If you're struggling to find clear information, you can search multiple times and show progress as you go.

Output format - use XML tags:
- When you find all founders: <final>["Founder1", "Founder2", ...]</final>
- If searching multiple times, show progress: <progress>["Founder1", ...]</progress> then <final>[...]</final>
- If no founders found: <final>[]</final>

Example (easy case):
<final>["John Doe", "Jane Smith"]</final>

Example (difficult case):
<progress>["John Doe"]</progress>
<progress>["John Doe", "Jane Smith"]</progress>
<final>["John Doe", "Jane Smith", "Bob Johnson"]</final>""",
        model="claude-sonnet-4-5-20250929",
        max_turns=10
    )

    # Create the prompt for the agent
    prompt = f"""Find the founders of {company_name} ({company_url}).

Research using web search. Output your answer in XML format: <final>[...]</final>"""

    # Set up conversation logging
    log_file = setup_conversation_log(company_name)
    log_to_file(log_file, f"PROMPT:\n{prompt}\n")
    log_to_file(log_file, "=" * 60)

    try:
        # Track all responses and extract intermediate/final answers
        all_text = ""
        latest_progress = None
        final_answer = None
        turn_count = 0

        async for message in query(prompt=prompt, options=options):
            # Log intermediate steps for debugging
            msg_type = type(message).__name__

            # Track turns
            if isinstance(message, AssistantMessage):
                turn_count += 1
                log_to_file(log_file, f"\n--- Turn {turn_count} (AssistantMessage) ---")

            # Log tool usage and extract text
            if isinstance(message, AssistantMessage):
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for block in message.content:
                        # Log when agent uses a tool
                        if hasattr(block, 'name') and hasattr(block, 'input'):
                            tool_name = block.name
                            tool_input = block.input
                            if tool_name == 'WebSearch':
                                query_text = tool_input.get('query', '')
                                print(f"    🔍 Searching: \"{query_text}\"")
                                log_to_file(log_file, f"TOOL USE: WebSearch")
                                log_to_file(log_file, f"  Query: {query_text}")
                            elif tool_name == 'WebFetch':
                                url = tool_input.get('url', '')
                                print(f"    🌐 Fetching: {url}")
                                log_to_file(log_file, f"TOOL USE: WebFetch")
                                log_to_file(log_file, f"  URL: {url}")

                        # Collect text responses
                        if isinstance(block, TextBlock):
                            text = block.text
                            all_text += text + "\n"

                            # Log agent text output
                            log_to_file(log_file, f"AGENT OUTPUT:")
                            log_to_file(log_file, text)

                            # Extract <progress> tags
                            progress_matches = re.findall(r'<progress>\s*(\[.*?\])\s*</progress>', text, re.DOTALL)
                            for match in progress_matches:
                                try:
                                    latest_progress = json.loads(match)
                                    print(f"    📝 Progress: Found {len(latest_progress)} founder(s) so far")
                                    log_to_file(log_file, f"EXTRACTED PROGRESS: {latest_progress}")
                                except json.JSONDecodeError:
                                    pass

                            # Extract <final> tag
                            final_matches = re.findall(r'<final>\s*(\[.*?\])\s*</final>', text, re.DOTALL)
                            for match in final_matches:
                                try:
                                    final_answer = json.loads(match)
                                    print(f"    ✅ Final answer: {len(final_answer)} founder(s)")
                                    log_to_file(log_file, f"EXTRACTED FINAL: {final_answer}")
                                except json.JSONDecodeError:
                                    pass

            # Log when tool results come back
            elif msg_type == 'UserMessage':
                print(f"    ✓ Tool results received")
                log_to_file(log_file, "TOOL RESULTS RECEIVED")

                # Log tool result content (truncated if too long)
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, 'content'):
                            content = str(block.content)
                            if len(content) > 500:
                                content = content[:500] + "... (truncated)"
                            log_to_file(log_file, f"  {content}")

        # Determine final result
        if final_answer is not None:
            # Agent provided <final> answer
            founders = final_answer
        elif latest_progress is not None:
            # Agent hit max_turns but had <progress> answer
            print(f"    ⚠️  Max turns reached - using latest <progress>")
            founders = latest_progress
        else:
            # Try to extract any JSON array from the response
            print(f"    ⚠️  No <progress> or <final> tags found - attempting fallback extraction")
            json_arrays = re.findall(r'\[(?:[^\[\]]|"[^"]*")*\]', all_text)
            if json_arrays:
                try:
                    # Try the last JSON array found
                    founders = json.loads(json_arrays[-1])
                    if isinstance(founders, list):
                        print(f"    ℹ️  Extracted from text: {len(founders)} founder(s)")
                    else:
                        founders = []
                except json.JSONDecodeError:
                    print(f"    ❌ Could not parse any founder data")
                    founders = []
            else:
                print(f"    ❌ No founder data found in response")
                founders = []

        # Validate all items are strings
        founders = [str(f) for f in founders if f and isinstance(f, str)]

        return founders

    except Exception as e:
        print(f"    ❌ Error finding founders for {company_name}: {e}")
        return []


async def find_founders_with_logging(company: Dict[str, str], index: int, total: int) -> tuple[str, List[str]]:
    """
    Wrapper around find_founders that adds logging for parallel execution.

    Args:
        company: Dict with 'name' and 'url' keys
        index: Company index (1-based)
        total: Total number of companies

    Returns:
        Tuple of (company_name, founders_list)
    """
    name = company['name']
    url = company['url']

    print(f"[{index}/{total}] Starting search for {name}...")
    founders = await find_founders(name, url)
    print(f"[{index}/{total}] ✓ {name}: Found {len(founders)} founders")

    return (name, founders)


async def main():
    """Main entry point for the founder finder tool."""

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your API key: export ANTHROPIC_API_KEY=your_key")
        return

    # Parse input file
    companies_file = 'companies.txt'
    if not os.path.exists(companies_file):
        print(f"Error: {companies_file} not found")
        return

    companies = parse_companies_file(companies_file)
    total = len(companies)

    print(f"Found {total} companies to process")
    print(f"Running in parallel mode - all companies processed concurrently\n")

    # Create tasks for all companies to run in parallel
    # Each agent gets only one company and runs independently
    tasks = [
        find_founders_with_logging(company, i + 1, total)
        for i, company in enumerate(companies)
    ]

    # Execute all tasks concurrently
    print("Starting parallel execution...\n")
    results_list = await asyncio.gather(*tasks)

    # Convert list of tuples to dict
    results = dict(results_list)

    # Write results to JSON file
    output_file = 'founders.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✓ Results saved to {output_file}")
    print(f"\nSummary:")
    print(f"  Total companies: {len(results)}")
    print(f"  Companies with founders: {sum(1 for f in results.values() if f)}")
    print(f"  Companies without founders: {sum(1 for f in results.values() if not f)}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    asyncio.run(main())
