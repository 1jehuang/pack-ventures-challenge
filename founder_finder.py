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
    # system_prompt: Instructs the agent to return only founder names in JSON format
    # model: Use Claude Sonnet 4.5 for high-quality responses
    # max_turns: Limit to 5 turns to keep queries efficient
    options = ClaudeAgentOptions(
        allowed_tools=["WebSearch", "WebFetch"],
        system_prompt="""You are a research assistant specialized in finding company founders.

Your task: Find the names of the original founders/co-founders of companies.

Rules:
- Return ONLY the names of actual founders/co-founders (people who started the company)
- Do NOT include advisors, investors, board members, or employees
- Focus on current/original founders, not interim CEOs or replacements
- If you cannot find reliable founder information, return an empty response

Output format: Return ONLY a JSON array of founder names, nothing else.
Example: ["John Doe", "Jane Smith"]
If no founders found: []

Be concise and factual. Use web search to verify information.""",
        model="claude-sonnet-4-5-20250929",
        max_turns=5
    )

    # Create the prompt for the agent
    prompt = f"""Find the founders of {company_name} ({company_url}).

Return ONLY a JSON array of founder names. Example: ["Name1", "Name2"]
If no founders found, return: []

No explanation needed, just the JSON array."""

    try:
        # Collect all responses from the agent
        response_text = ""
        async for message in query(prompt=prompt, options=options):
            # Log intermediate steps for debugging
            msg_type = type(message).__name__

            # Log tool usage
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
                            elif tool_name == 'WebFetch':
                                url = tool_input.get('url', '')
                                print(f"    🌐 Fetching: {url}")

                        # Collect text responses
                        if isinstance(block, TextBlock):
                            response_text += block.text
                            print(f"    💬 Agent responded with text ({len(block.text)} chars)")

            # Log when tool results come back
            elif msg_type == 'UserMessage':
                print(f"    ✓ Tool results received")

        # Clean up the response
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        response_text = response_text.strip()

        # Parse JSON
        founders = json.loads(response_text)

        # Validate it's a list
        if not isinstance(founders, list):
            print(f"Warning: Response for {company_name} is not a list: {response_text}")
            return []

        # Validate all items are strings
        founders = [str(f) for f in founders if f]

        return founders

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {company_name}: {e}")
        print(f"Response was: {response_text}")
        return []
    except Exception as e:
        print(f"Error finding founders for {company_name}: {e}")
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
