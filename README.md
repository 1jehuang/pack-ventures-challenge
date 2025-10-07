# Founder Finder Tool

A Python-based tool that automatically identifies company founders using the Claude Agent SDK with web search capabilities.

## Overview

This tool takes a list of companies (with their URLs) and returns a structured JSON file containing the founders of each company. It leverages Claude's Agent SDK with web search to find accurate, verified founder information.

## How to Run

### Prerequisites

- Python 3.10 or higher
- Anthropic API key (get one at https://console.anthropic.com)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pack-ventures-challenge
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key:**
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

   Or create a `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

### Running the Tool

```bash
python founder_finder.py
```

The tool will:
1. Read companies from `companies.txt`
2. **Process all companies in parallel** (all agents run concurrently)
3. Show real-time logs with search queries, tool results, and progress
4. Generate `founders.json` with the results

**To save logs to a file:**
```bash
python founder_finder.py 2>&1 | tee founder_finder.log
```

### Verifying Results

```bash
python verify_results.py
```

This will verify that `founders.json` contains correct founder information against known expected results.

### Running Tests

```bash
pytest test_founder_finder.py -v
```

### Testing Single Company

```bash
python test_single_company.py
```

Quick test with a single company (Airbnb) to verify the agent is working.

## Approach

### Technology Stack

**Claude Agent SDK:** Uses the Claude Agent SDK for simplicity. The SDK provides built-in web search, intelligent parsing, and tool orchestration without needing custom scrapers or complex HTML parsing logic.

### Implementation Strategy

The tool uses **parallel processing** with independent agents for maximum efficiency:

1. **Parallel Execution:** All 10 companies are processed concurrently using `asyncio.gather()`, dramatically reducing total runtime (~10x faster)
2. **Independent Agents:** Each agent processes one company with its own context - no shared state between companies
3. **Web Search:** Agents use WebSearch and WebFetch tools to find founder information from multiple sources
4. **Intelligent Extraction:** XML-based output format (`<final>` and `<progress>` tags) allows flexible agent reasoning

**Agent Workflow:**
- **Easy cases:** One search → immediate `<final>` response
- **Difficult cases:** Multiple searches with `<progress>` updates → `<final>` when confident
- **Max turns:** 10 turns allowed for thorough research

### Key Design Decisions

- **XML Format:** Agents output `<final>["Name1", "Name2"]</final>` for structured, reliable parsing
- **Flexible System Prompt:** Encourages efficiency (one search for most companies) but allows deeper research when needed
- **Real-time Logging:** Shows 🔍 searches, ✓ tool results, 📝 progress, ✅ final answers as they happen
- **Fallback Extraction:** Three-tier extraction: `<final>` → `<progress>` → any JSON array
- **Error Handling:** Gracefully handles max_turns exhaustion, parsing errors, and API failures
- **Testing:** Comprehensive test suite + verification script for accuracy validation

### Assumptions

1. **Founder Definition:** "Founders" refers to the original founders/co-founders who started the company, not current CEOs or interim leaders
2. **Data Accuracy:** Web search results are generally reliable for well-known startups
3. **Name Format:** Founder names are returned in "First Last" format
4. **API Access:** Users have access to an Anthropic API key (Claude Code subscription does not work with the SDK)

## Future Improvements

### 1. **Codex SDK Support**
- Add Codex SDK support for OpenAI model optionality alongside Claude

### 2. **CLI Subscription Support**
- Add Claude Code CLI and Codex CLI support for subscription-based usage instead of API keys
- Would require a different implementation approach than the current SDK

### 3. **Pre-Web Scrape with Faster Models**
- First scrape the entire website domain
- Process with a smaller/faster LLM to check for founder information
- Only fall back to full agent search if founders not found
- Significantly reduce cost and latency for companies with clear "About" pages

## Project Structure

```
pack-ventures-challenge/
├── founder_finder.py          # Main tool (parallel processing implementation)
├── test_founder_finder.py     # Test suite
├── test_single_company.py     # Quick single-company test
├── verify_results.py          # Verification script for accuracy checking
├── companies.txt              # Input file (company names + URLs)
├── founders.json              # Output file (generated results)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # API key (not committed)
├── .gitignore                # Git ignore rules
├── docs/
│   └── claude-agent-sdk-api.md  # SDK API reference
└── README.md                 # This file
```

## Results

The tool successfully found founders for **all 10 companies** in the input file:

- **10/10** companies with complete founder information
- **0/10** companies with missing data

See `founders.json` for the complete results.
You may delete or empty the file first to see the result fill in after the agent completes. 

### Cost Considerations

**Actual run results (10 companies in parallel):**
- Total cost: ~$1.00 USD (Note that modifying system prompt to force lower verbosity will sigifigantly reduce cost. In my prompt I allow verbosity for maximum performance, though perfomance boost is minimal.)
- Processing time: ~5 minutes (all companies processed concurrently)

**Performance characteristics:**
- Runtime is ~5 minutes regardless of input size n (due to full parallelization)
- All agents run concurrently, so total time = time for slowest individual query
- Sequential processing would take ~5 minutes × n companies

## License

MIT

## Contact

For questions or issues, please contact jeremy huang.
