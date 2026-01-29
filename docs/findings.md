# 🔎 FINDINGS & DISCOVERIES

## 🟢 Initialization Phase
- Project directory initialized.
- Memory files created.
- Discovery questions answered by user.

## 🏗️ Blueprint Phase

### Research: Web Scraping (Coursera & Udemy)
*   **Playwright is mandatory** for handling dynamic content.
*   **Anti-Detection:**
    *   **Coursera:** Accessible with standard Playwright (Verified).
    *   **Udemy:** BLOCKED (Status 403). Standard Playwright AND `playwright-stealth` were both intercepted by Cloudflare.
    *   **Recommendation:** User may need to provide `cookies.txt` or run scraper in "Headed" mode with manual intervention for Udemy.

### Research: Recommendation System
*   **Approach:** Content-Based Filtering (TF-IDF + Cosine Similarity).

## ⚡ Phase 2: Link
*   **Coursera:** Connection 200 OK.
*   **Udemy:** Connection 403 Forbidden (Cloudflare).
