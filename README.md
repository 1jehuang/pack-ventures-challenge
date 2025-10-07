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

Given more time, here are enhancements I would add:

### 1. **Caching and Rate Limiting**
- Implement Redis/file-based caching to avoid re-querying the same companies
- Add intelligent rate limiting to manage API costs
- Store intermediate results to enable resume-on-failure

### 2. **Data Validation and Confidence Scoring**
- Cross-reference multiple sources (Crunchbase API, LinkedIn, PitchBook)
- Assign confidence scores based on source reliability
- Flag founders with conflicting information for manual review
- Validate founder names against common patterns (avoid AI hallucinations)

### 3. **Enhanced Output Formats**
- Include additional metadata (founding year, roles like CEO/CTO, LinkedIn profiles)
- Support multiple output formats (CSV, Excel, Database export)
- Generate summary statistics and visualizations
- Add LinkedIn/Twitter handles for each founder

### 4. **Monitoring and Observability**
- Save detailed conversation logs to files (currently only stdout)
- Track API usage and costs per query
- Add Sentry/Datadog integration for error tracking
- Create dashboard showing success rates, average query time, etc.

### 5. **Specialized Handling**
- Detect acquired companies and handle founder transitions
- Handle international companies with non-Latin characters
- Support stealth mode companies with limited public info
- Add fallback to Crunchbase/LinkedIn APIs when web search fails

### 6. **User Experience Improvements**
- Add CLI interface with `click` or `typer` for better UX
- Support reading from CSV/Excel, not just text files
- Interactive mode to confirm uncertain results
- Web UI for non-technical users
- Add progress bar for parallel execution

### 7. **Quality Assurance**
- Implement human-in-the-loop review for low-confidence results
- Add integration tests with real company data
- Create benchmark dataset for accuracy measurement
- A/B test different system prompts for better extraction

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

## Technical Notes

### Why Claude Agent SDK?

While I could have used:
- **Web scraping (BeautifulSoup):** Fragile, requires per-site parsers
- **API services (Crunchbase, Clearbit):** Cost money, rate-limited, incomplete data
- **GPT-4 with function calling:** More setup, less integrated tooling

The Claude Agent SDK provides the best balance of:
- ✅ Accuracy (AI understands context)
- ✅ Reliability (handles different website structures)
- ✅ Ease of use (built-in web search and tool orchestration)
- ✅ Cost-effectiveness (pay only for what you use)

### Cost Considerations

Each founder query uses approximately:
- 1-3 web searches (most companies need only 1)
- 0-1 web fetches (when agent needs to verify from company website)
- ~1,000-3,000 tokens per company

**Actual run results (10 companies in parallel):**
- Total cost: ~$0.08 USD
- Processing time: ~5 minutes (all companies processed concurrently)
- Cache hits improve cost on subsequent runs

**Performance characteristics:**
- Runtime is ~5 minutes regardless of input size n (due to full parallelization)
- All agents run concurrently, so total time = time for slowest individual query
- Sequential processing would take ~5 minutes × n companies

## License

MIT

## Contact

For questions or issues, please contact jeremy huang.
