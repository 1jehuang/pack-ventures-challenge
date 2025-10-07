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
2. Search for founders of each company using web search
3. Generate `founders.json` with the results

### Running Tests

```bash
pytest test_founder_finder.py -v
```

## Approach

### Technology Stack

**Claude Agent SDK:** I chose the Claude Agent SDK over building a custom scraper or using traditional APIs for several key reasons:

1. **Robustness:** Web scraping is fragile and breaks when websites change structure. The SDK uses AI to understand context, making it resilient to different website layouts.

2. **Web Search Integration:** The SDK provides built-in web search capabilities, allowing the agent to query multiple sources (news articles, Crunchbase, LinkedIn, company websites) automatically.

3. **Intelligent Parsing:** Instead of writing complex regex patterns or HTML parsers, the AI agent understands founder information contextually and can distinguish between founders, advisors, and employees.

4. **Production-Ready:** The SDK includes error handling, context management, and tool orchestration out-of-the-box.

### Implementation Strategy

The tool uses a two-step approach for each company:

1. **Web Search:** The agent searches for "[Company Name] founders" using the WebSearch and WebFetch tools
2. **Information Extraction:** The agent parses search results to extract founder names, filtering out non-founders

### Key Design Decisions

- **System Prompt:** Carefully crafted to ensure the agent returns ONLY founder/co-founder names, excluding advisors, investors, and employees
- **JSON Output:** Agent is instructed to return clean JSON arrays for easy parsing and validation
- **Error Handling:** Gracefully handles cases where founder info is unavailable (returns empty array)
- **Testing:** Comprehensive test suite validates parsing logic, error handling, and output format

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

### 3. **Batch Processing and Parallelization**
- Process multiple companies concurrently using `asyncio.gather()`
- Implement a queue system for large-scale batch jobs
- Add progress tracking with `tqdm` or similar
- Support resume-from-checkpoint for interrupted runs

### 4. **Enhanced Output Formats**
- Include additional metadata (founding year, roles like CEO/CTO, LinkedIn profiles)
- Support multiple output formats (CSV, Excel, Database export)
- Generate summary statistics and visualizations
- Add LinkedIn/Twitter handles for each founder

### 5. **Monitoring and Observability**
- Integrate logging (structlog) for debugging and auditing
- Track API usage and costs per query
- Add Sentry/Datadog integration for error tracking
- Create dashboard showing success rates, average query time, etc.

### 6. **Specialized Handling**
- Detect acquired companies and handle founder transitions
- Handle international companies with non-Latin characters
- Support stealth mode companies with limited public info
- Add fallback to Crunchbase/LinkedIn APIs when web search fails

### 7. **User Experience Improvements**
- Add CLI interface with `click` or `typer` for better UX
- Support reading from CSV/Excel, not just text files
- Interactive mode to confirm uncertain results
- Web UI for non-technical users

### 8. **Quality Assurance**
- Implement human-in-the-loop review for low-confidence results
- Add integration tests with real company data
- Create benchmark dataset for accuracy measurement
- A/B test different system prompts for better extraction

## Project Structure

```
pack-ventures-challenge/
├── founder_finder.py          # Main tool implementation
├── test_founder_finder.py     # Test suite
├── companies.txt              # Input file (company names + URLs)
├── founders.json              # Output file (generated results)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
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
- ~2-3 web searches
- ~1-2 web fetches
- ~1,000-3,000 tokens

For 10 companies, estimated cost: **$0.10 - $0.30** (as of October 2025)

## License

MIT

## Contact

For questions or issues, please contact jeremy huang.
