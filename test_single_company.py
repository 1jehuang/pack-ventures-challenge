#!/usr/bin/env python3
"""Test the founder finder with a single company"""

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
    print("Testing founder finder with single company")
    print("=" * 60)
    print()

    # Test with Airbnb (easy case - well known)
    company = "Airbnb"
    url = "https://www.airbnb.com"

    print(f"Finding founders for {company}...\n")
    founders = await find_founders(company, url)

    print()
    print("=" * 60)
    print(f"Result: {founders}")
    print(f"Found {len(founders)} founder(s)")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test())
