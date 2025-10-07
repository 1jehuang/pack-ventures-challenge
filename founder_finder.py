#!/usr/bin/env python3
"""
Founder Finder Tool
Uses Claude Agent SDK to automatically find founder names for a list of companies.
"""

import asyncio
import json
import os
import re
from typing import List, Dict
from claude_agent_sdk import query, ClaudeAgentOptions


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
            # Extract text content from assistant messages
            if hasattr(message, 'role') and message.role == 'assistant':
                if hasattr(message, 'content') and isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, 'type') and block.type == 'text':
                            response_text += block.text

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
    print(f"Found {len(companies)} companies to process\n")

    # Find founders for each company
    results = {}

    for i, company in enumerate(companies, 1):
        name = company['name']
        url = company['url']

        print(f"[{i}/{len(companies)}] Finding founders for {name}...")
        founders = await find_founders(name, url)
        results[name] = founders
        print(f"  → Found: {founders}\n")

    # Write results to JSON file
    output_file = 'founders.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results saved to {output_file}")
    print(f"\nSummary:")
    print(f"  Total companies: {len(results)}")
    print(f"  Companies with founders: {sum(1 for f in results.values() if f)}")
    print(f"  Companies without founders: {sum(1 for f in results.values() if not f)}")


if __name__ == '__main__':
    asyncio.run(main())
