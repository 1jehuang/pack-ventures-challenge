#!/usr/bin/env python3
"""Test the two companies that failed in the previous run"""

import asyncio
import os
from pathlib import Path
from founder_finder import find_founders

# Load .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

async def test():
    print("=" * 60)
    print("Testing previously failed companies")
    print("=" * 60)
    print()

    # Test the two companies that failed
    companies = [
        ("Read AI", "https://www.read.ai/"),
        ("Casium", "https://www.casium.com/")
    ]

    for name, url in companies:
        print(f"Finding founders for {name}...")
        founders = await find_founders(name, url)
        print(f"  → Found: {founders}")
        print(f"  → Conversation log: logs/{name.replace(' ', '_')}_conversation.log")
        print()

    print("=" * 60)
    print("Check logs/ directory for detailed conversation logs")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test())
