# 🏗️ SOP: WEB SCRAPING

## 1. Principles
- **Deterministic:** Retry logic (3 attempts with exponential backoff) is mandatory.
- **Respectful:** 2-5 second random delay between requests.
- **Atomic Save:** Save raw HTML/JSON to `.tmp/` immediately after fetch.

## 2. Coursera Strategy
- **Base URL:** `https://www.coursera.org/search?query=data%20science` (Example)
- **Pagination:**
    - Type: URL Parameters (`&page=1`, `&page=2`) OR "Next" Button.
    - Approach: Iterate URL parameter `page` from 1 to N.
- **Selectors (Hypothetical - To be verified):**
    - Container: `li.ais-Hits-item` or `div.rc-CourseCard` or `div[data-e2e="search-card"]`
    - Title: `h2` or `h3`
    - Partner/Institution: `span.partner-name`
    - Rating: `span.ratings-text` or `span[data-test="ratings-count-without-stars"]`
    - Metadata: `div.metadata` (Duration, Level)

## 3. Error Handling
- **403/Forbidden:** Stop immediately and alert user.
- **Timeout:** Retry 3 times.
- **Empty DOM:** Log warning, dump HTML to `.tmp/debug/`, and skip.

## 4. Output Format
- Save as JSON Lines (`.jsonl`) or JSON Array.
- Filename: `.tmp/data/raw_coursera_{timestamp}.json`
