# Token Sniper & Research Bot — Project Description

**Short summary**
A compact Telegram bot + scraper that tracks newly listed token pairs on Dexscreener and provides fast, on-demand analysis. The project combines a Playwright scraper for discovering new pairs, a Telegram front-end for interaction and wallet management, and a pluggable “deep research” step that runs an LLM to summarize token risk and credibility. Built as a developer tool for research and education — not financial advice.

## Why this project exists

There’s a lot of noise around new token listings. This repo collects the useful signals (age, volume, buys/sells, contract link) and surfaces them into a lightweight Telegram workflow so you can:

* Spot new listings quickly
* Keep an auditable list of tokens you checked
* Run a quick automated analysis from an LLM
* Manage wallets for testing (with strong warnings and safeguards)

This is intended for researchers, security auditors, and devs who want a repeatable pipeline to study new-token behavior and scams.

## Key features

* **Realtime scraping** of Dexscreener’s “new pairs” page with Playwright.
* **Telegram bot UI** to start/stop research, browse discovered tokens, and request deep analysis.
* **Per-user state** for scraped results (paging, token selection).
* **Wallet management**: temporary wallet addresses can be created and tracked in an on-disk database for convenience (private keys must be handled securely).
* **Deep research** integration: calls an LLM to summarize token purpose, credibility, risks and a final verdict.
* **Buy button (safe)** that links users to the Dexscreener pair page — no automatic trading by default.
* **Privacy & safety-first** approach: opt-in wallet usage, warnings, and an explicit disclaimer that this tool does not provide investment advice.

## How it works (high level)

1. **Scraper (Playwright)** visits Dexscreener new-pairs, extracts rows (name, pair, price, volume, buys/sells, contract href), and returns structured JSON.
2. **Telegram bot** stores the results per-user and provides a paged interface to inspect tokens.
3. When the user requests **deep research**, the bot composes a prompt from token fields and sends it to an LLM to receive a readable analysis. The bot filters model thinking traces so only the final analysis is delivered.
4. The **Buy** action opens the Dexscreener link so the user can complete the trade in their wallet (no direct on-chain transactions performed by the bot).

## Safety, legality, and ethics

* **Research-only:** This project is meant to help developers understand token launch mechanics and detect scams — not to enable market manipulation or illicit behavior.
* **No custody:** The default behavior is not to hold funds for users. If you add automated wallet creation/funding features, treat private keys as extremely sensitive (encrypt, never log).
* **Compliance:** Using automated trading or interacting with smart contracts can have legal and regulatory implications depending on your jurisdiction. Do not use this project to perform unlawful activities.
* **Responsible use:** Sniper/front-run bots can harm other traders and the broader market. Use this code for learning, auditing, or on private testnets only.

## Security notes

* Never hardcode API tokens, private keys, or third-party secrets in source. Use environment variables and encrypted secrets for CI.
* If you add on-chain trading, require multi-layer confirmations and withdraw-only hot wallets, or better: integrate with user-controlled wallets (walletconnect, metamask) rather than custodial wallets.
* Sanitize all external inputs and treat scraped content as untrusted.

## Quick start (developer-focused)

* Clone repository
* Create a virtual environment and install dependencies (`playwright`, `aiogram`, `web3` if you add blockchain features, etc.)
* Set environment variables for the Telegram bot token and any LLM API tokens
* Run the scraper module to test scraping, run the bot module to start the Telegram interface

## Typical project structure

```
/bot.py            # Telegram bot and handlers
/g.py              # Playwright scraper that returns structured token data
/llm_client.py     # Thin adapter for calling the chosen LLM provider
/db.sqlite         # SQLite store for user wallets (optional)
README.md
```

## Limitations & known issues

* Dexscreener page structure may change; scraper selectors require maintenance.
* LLM outputs can contain internal reasoning traces; the bot strips known markers but results are not guaranteed perfect.
* The bot does not perform on-chain trades by default. If you add that capability, expect to implement careful security controls.

## Contribution & roadmap

* Improve scraping stability and pagination support
* Add optional rate-limiting and user quotas
* Add safe, opt-in wallet integration that delegates signing to user-controlled wallets (recommended)
* Add better logging, observability, and test coverage

## Disclaimer (put this prominently in README and UI)

**This project is for educational and research purposes only. It is not financial advice.** Using automated trading tools, particularly sniper/bots, may be illegal in some jurisdictions and can cause financial loss. Always test on public testnets and handle private keys with extreme care.

---


