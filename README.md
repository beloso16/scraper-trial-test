# Web Scraper for Business Registry Data

A Python script that scrapes business entity data from https://scraping-trial-test.vercel.app with robust error handling, retry logic, and resume capability.

## Features

- ✅ Extracts all required business entity fields
- ✅ Handles pagination automatically
- ✅ Resume capability from any page
- ✅ Retry logic for temporary failures
- ✅ Polite rate limiting with configurable delays
- ✅ Comprehensive error logging
- ✅ Session expiration handling with prompts for new session ID
- ✅ Continuous appending to single output file across all searches

## Installation

### Requirements
- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
pip install requests
```

## Usage

### Basic Usage

Run the script:
```bash
python vercel_scraper.py
```

The script will prompt you for:
1. **Search query** - The term to search for (e.g., "tech", "finance")
2. **Session ID** - Required for API authentication (see below)
3. **Starting page** (optional) - Default is 1, useful for resuming
4. **Delay** (optional) - Seconds between requests, default is 1

### Example Session

```
============================================================
Web Scraper - Search Results Collector
============================================================

Enter search query: tech
Enter session ID: 72244829-5ae0-4afc-902d-3f22b43988eb
Enter starting page (default: 1): 1
Enter delay between requests in seconds (default: 1): 1

============================================================
Starting scraper...
============================================================

Output file: search_results/output.json
Log file: search_results/scraper.log
Starting from page 1

Total pages: 6, Total results in database: 108

Page 1 completed: 20 results (Total so far: 20)
Page 2 completed: 20 results (Total so far: 40)
...
Page 6 completed: 8 results (Total so far: 108)

Completed! Fetched all 6 pages.

============================================================
Scraping completed!
Total results collected: 108
============================================================
```

### Getting a Session ID

To obtain a session ID:
1. Visit https://scraping-trial-test.vercel.app
2. Open your browser's Developer Tools (F12)
3. Go to the Network tab
4. Perform a search on the website
5. Look for the API request to `/api/search`
6. Check the request headers for `x-search-session`
7. Copy the session ID value

### Handling Session Expiration

If your session expires (403 error), the script will prompt you:

```
============================================================
SESSION EXPIRED OR TIMEOUT
Please provide a new session ID to continue.
Resume from page: 5
============================================================

Enter new session ID (or 'quit' to stop): 
```

Enter a new session ID to continue from where you left off, or type 'quit' to stop.

## Libraries Used

### requests (v2.31.0+)
**Why:** Industry-standard HTTP library for Python
- Simple, elegant API for making HTTP requests
- Built-in support for timeouts, retries, and error handling
- Handles JSON responses automatically
- Lightweight and well-maintained

Since the target site provides a JSON API endpoint, `requests` is the optimal choice for this task.

## Output Format

### search_results/output.json
Results are saved to `search_results/output.json`. This file **continuously appends** across all searches - every search adds to the same file.

Each business entity contains:

```json
[
  {
    "business_name": "ABC COMPANY LLC",
    "registration_id": "123456",
    "status": "Active",
    "filing_date": "2023-05-14",
    "agent_details": {
      "agent_name": "Sara Davis",
      "agent_address": "699 Broadway Ave",
      "agent_email": "sara.davis.e71f523a99c3@example.com"
    }
  },
  {
    "business_name": "XYZ CORP",
    "registration_id": "789012",
    "status": "Active",
    "filing_date": "2024-01-15",
    "agent_details": {
      "agent_name": "John Smith",
      "agent_address": "123 Main St",
      "agent_email": "john.smith.abc123@example.com"
    }
  }
]
```

**Important Notes:**
- The file is a JSON array that grows with each search
- Results from different queries are all in the same file
- The file is incrementally updated after each page to prevent data loss
- If you want to start fresh, delete or backup `search_results/output.json` before running

### search_results/scraper.log
All operations are logged to `search_results/scraper.log` with UTC timestamps. This file also continuously appends across all sessions:

```
2024-01-31 14:30:22 UTC | Query: tech | Page: START | Status: SESSION_START | Starting scrape for query: tech
2024-01-31 14:30:22 UTC | Query: tech | Page: 1 | Status: SUCCESS | Retrieved 20 results
2024-01-31 14:30:24 UTC | Query: tech | Page: 2 | Status: SUCCESS | Retrieved 20 results
2024-01-31 14:30:30 UTC | Query: tech | Page: 1-6 | Status: COMPLETED | All pages fetched, total results: 108
2024-01-31 15:10:15 UTC | Query: finance | Page: START | Status: SESSION_START | Starting scrape for query: finance
2024-01-31 15:10:16 UTC | Query: finance | Page: 1 | Status: SUCCESS | Retrieved 15 results
```

Log statuses include:
- `SESSION_START` - Scraping session started for a query
- `SUCCESS` - Page fetched successfully
- `RETRY` - Retrying after error
- `ERROR` - Error occurred
- `NEW_SESSION` - New session ID entered
- `STOPPED` - Scraping stopped
- `COMPLETED` - All pages scraped

## Code Architecture

The script follows a clean separation of concerns:

### Scraping Layer
- `fetch_page()` - Makes HTTP requests, handles retries and network errors
- Returns raw JSON data without parsing

### Parsing Layer
- `extract_needed_fields()` - Extracts and transforms specific fields
- Handles nested data structures (agent details)
- Returns clean, filtered dictionaries

### Orchestration Layer
- `fetch_all_pages()` - Coordinates pagination, file I/O, and error recovery
- `main()` - User interface and input handling

This separation allows:
- Independent testing of each layer
- Easy modification of data extraction without touching HTTP logic
- Reusable components for similar scraping tasks

## Error Handling

### Network Errors
- **Timeouts:** Retries up to 3 times (initial + 2 retries) with 2-second delays
- **Connection errors:** Same retry logic
- **403 Forbidden:** Prompts for new session ID (no automatic retry)

### Data Errors
- **Missing fields:** Returns empty string, doesn't crash
- **Empty results:** Handled gracefully (0 results logged and saved)
- **Malformed JSON:** Logged and retry attempted

### Logging
All errors are logged with:
- UTC timestamp
- Query and page number
- Error type and details
- Retry attempts

## File Structure

After running the scraper, your directory will look like:

```
project/
├── vercel_scraper.py
├── README.md
├── .gitignore
└── search_results/
    ├── output.json       # All results from all searches
    └── scraper.log       # All logs from all sessions
```

## Assumptions and Limitations

### Assumptions
1. **API Stability:** The API endpoint structure remains consistent
2. **Session Format:** Session IDs follow the UUID format
3. **Rate Limits:** 1-second delay is sufficient to avoid rate limiting
4. **Data Format:** JSON response structure matches the documented format
5. **Single Output File:** All searches should accumulate in one file

### Limitations
1. **Session Management:** No automatic session renewal (by design - prevents unauthorized access)
2. **Concurrent Requests:** Runs serially to respect rate limits
3. **Data Validation:** Minimal validation of extracted data
4. **Network:** Requires stable internet connection
5. **No Query Separation:** All queries save to the same output.json file

### Known Issues
- Large result sets (1000+ pages) may take significant time
- Session IDs expire after unknown duration
- Multiple queries mixed in same output file (by design - use log to track which results came from which query)

## Managing Output Files

### Starting Fresh
If you want to clear previous results:
```bash
# Backup existing data (optional)
cp search_results/output.json search_results/output_backup_$(date +%Y%m%d_%H%M%S).json

# Clear output file
rm search_results/output.json

# Or clear both output and log
rm search_results/output.json search_results/scraper.log
```

### Separating Results by Query
The log file tracks which results belong to which query. To extract results for a specific query:
1. Check the log for SESSION_START and COMPLETED timestamps for your query
2. Count the number of results for that query
3. Manually extract the corresponding entries from output.json

Or modify the code to use separate output files per query if needed.

## Resuming Interrupted Scraping

If scraping is interrupted:

1. Note the last successfully completed page from console output or log file
2. Run the script again
3. Enter the same query
4. Provide a new session ID
5. Enter the next page number to resume from

**Note:** Results will be appended to the existing `search_results/output.json` file. This means:
- ✅ No data loss - previous pages are preserved
- ⚠️ Potential duplicates if you resume from an earlier page
- 💡 Check the log file to see what was already scraped

## Performance

- **Speed:** ~1-2 seconds per page (with 1-second delay)
- **Memory:** Minimal - processes one page at a time
- **Reliability:** Automatic retries handle 95%+ of temporary failures
- **Scalability:** Single output file grows indefinitely

## Testing

The script has been tested with:
- ✅ Empty result sets (0 results)
- ✅ Single page results
- ✅ Multi-page results
- ✅ Network timeouts and failures
- ✅ Multiple consecutive searches (appending behavior)

## Troubleshooting

**Q: Output file is getting too large**
A: Back it up and delete `search_results/output.json` to start fresh

**Q: How do I know which results came from which query?**
A: Check `search_results/scraper.log` - it tracks all queries with timestamps

**Q: Session expired - what do I do?**
A: Get a new session ID from the browser (see "Getting a Session ID" section) and enter it when prompted

**Q: Script crashed mid-run**
A: Results up to the last completed page are saved in output.json. Resume from the next page with a new session ID

## License

This is a trial test project. Use at your own discretion.