# Detailed Data Collection Analysis (Note on Scraping)

This document details the **Data Collection** phase of the project, which involves sophisticated web scraping strategies to harvest course data from Coursera and Udemy. The system leverages **Playwright (Async API)** to handle the dynamic, JavaScript-heavy nature of these modern web applications.

## 1. Core Technology: Playwright & Asyncio

Unlike traditional scraping (e.g., `requests` + `BeautifulSoup`), this project uses a headless browser automation approach.
*   **Asynchronous Execution**: Built on Python's `asyncio` to perform non-blocking I/O operations, allowing efficient waiting for network responses and DOM updates.
*   **Headless Chromium**: Simulates a real user environment (rendering CSS/JS) without the graphical overhead, though `HEADLESS_MODE` can be toggled in `config.py` for debugging.
*   **Context Isolation**: Each scrape session runs in a fresh browser context, ensuring no cookie leakage between runs.

## 2. Coursera Scraper (`scrapers/coursera_scraper.py`)

### 2.1 Target & Challenges
*   **Target**: `https://www.coursera.org/search?query={category}`
*   **Challenge**: Coursera uses "Infinite Scrolling" / Lazy Loading. Content is not present in the initial HTML response but is loaded via AJAX as the user scrolls down.

### 2.2 Implementation Details
*   **Scrolling Logic**:
    The scraper injects JavaScript to programmatically scroll the window:
    ```python
    await self.page.evaluate('window.scrollBy(0, window.innerHeight)')
    ```
    It repeats this action multiple times (`scroll_count=5`) with pauses to allow the React application to fetch and render new course cards.

*   **Consent Management**:
    A robust `handle_cookie_consent` method attempts to click "Accept" or "Accepter" buttons to clear the viewport. It targets multiple known selector variations (`button[data-testid="accept-cookies"]`, `#onetrust-accept-btn-handler`) to be resilient to UI A/B testing.

*   **Redundant Selectors**:
    To prevent breakage when Coursera updates their class names (which are often obfuscated, e.g., `css-0`), the scraper tries a hierarchy of selectors:
    1.  `li.cds-9.css-0...` (Specific)
    2.  `div[data-testid="search-result-card"]` (Semantic/Stable)
    3.  `li[class*="ais-Hits-item"]` (Fallback)

## 3. Udemy Scraper (`scrapers/udemy_scraper.py`)

### 3.1 Target & Challenges
*   **Target**: `https://www.udemy.com/courses/search/?q={topic}`
*   **Challenge**: Udemy has strict bot detection (checking for automation flags) and complex pagination that varies (sometimes using `<a>` tags, sometimes `<button>` tags).

### 3.2 Implementation Details
*   **Stealth Configuration**:
    The scraper modifies the browser fingerprint to hide its automated nature:
    ```python
    args=["--disable-blink-features=AutomationControlled"]
    # ...
    await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    ```
    This prevents scripts from detecting the `navigator.webdriver` flag commonly used to block bots.

*   **Production-Grade Pagination**:
    Instead of guessing URLs (`page=2`), the scraper physically interacts with the "Next" pagination element.
    *   **Logic**: It searches for the "Next" element using a list of selectors (handling both semantic `nav` elements and generic buttons).
    *   **Validation**: Checks `aria-disabled` attributes to determine if the last page has been reached.
    *   **Flow**: `Scroll to Bottom` -> `Find Next` -> `Click` -> `Wait for Network Idle`.

*   **Card-Based Extraction**:
    Data is extracted using strict structural queries relative to the card element:
    *   **Title**: `h2 a div` (Handles nested structure).
    *   **Metadata**: Parses the `ul.tag-list` to separate "Reviews", "Duration", and "Lectures" using Regex.
    *   **Pricing**: Distinguishes between current price (`data-purpose="course-price-text"`) and original price (for calculating implied discounts).

## 4. Error Handling & Resilience
Both scrapers implement defensive programming patterns:
*   **Try/Except Blocks**: Applied at the per-field level. If extracting a "Rating" fails, the scraper logs it and continues extracting the "Title" rather than crashing the entire session.
*   **Timeouts**: Explicit waits (`timeout=30000`) and sleep intervals (`asyncio.sleep`) prevent race conditions where code executes before the DOM is ready.
