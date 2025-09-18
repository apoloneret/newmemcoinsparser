from playwright.async_api import async_playwright
import asyncio
import json
import logging
import re

async def scrape():
    async with async_playwright() as p:
        # Launch browser with additional anti-detection settings
        browser = await p.chromium.launch(
            headless=True,  # Keep headless=False if you want it run headless set that to True
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York"
        )
        page = await context.new_page()
        base_url = "https://dexscreener.com"
        url = "https://dexscreener.com/new-pairs?rankBy=pairAge&order=asc"

        try:
            logging.info(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded")
            logging.info("Waiting for table rows to load")
            await page.wait_for_selector(".ds-dex-table-row", timeout=30000)  #Timeout 30s
            
            logging.info("Scrolling to load more content")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)") #scroll to load all 100 elements
            await asyncio.sleep(2)  

            rows = []
            table_rows = await page.locator("a.ds-dex-table-row").all()

            for row in table_rows:
                try:
                    href = await row.get_attribute("href")
                    if not href:
                        continue
                    match = re.search(r'/(?:solana|ethereum|base|bnb|avalanche)/([0-9a-zA-Z]+)', href)
                    contract_address = match.group(1) if match else "N/F"

                    trading_name = await row.locator(".ds-dex-table-row-base-token-symbol").inner_text() + "/" + \
                                   await row.locator(".ds-dex-table-row-quote-token-symbol").inner_text()
                    name = await row.locator(".ds-dex-table-row-base-token-name-text").inner_text()
                    price = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-price").inner_text()
                    age = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-pair-age > span").inner_text()
                    buys = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-buys").inner_text()
                    sells = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-sells").inner_text()
                    volume = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-volume").inner_text()
                    makers = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-makers").inner_text()
                    five_minuter = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-price-change-m5 > span").inner_text()
                    six_hours = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-price-change-h6 > span").inner_text()
                    twentyfour_hours = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-price-change-h24 > span").inner_text()
                    liquidity = await row.locator(".ds-table-data-cell.ds-dex-table-row-col-liquidity").inner_text()

                    rows.append({
                        "trading_name": trading_name,
                        "name": name,
                        "price": price,
                        "contract_address": contract_address,
                        "href": href,
                        "link": base_url + href,
                        "age": age,
                        "buys": buys,
                        "sells": sells,
                        "volume": volume,
                        "makers": makers,
                        "five_minuter": five_minuter,
                        "six_hours": six_hours,
                        "twentyfour_hours": twentyfour_hours,
                        "liquidity": liquidity
                    })
                except Exception as e:
                    logging.error(f"Error processing row: {e}")
                    continue

            return rows

        except Exception as e:
            logging.error(f"Error during scraping: {e}")
            return []
        finally:
            await browser.close()

async def savetojson():
    data = await scrape()
    with open("tests.json", "w") as f:
        json.dump(data, f, indent=4)
    logging.info(f"Saved {len(data)} rows to tests.json")



if __name__ == "__main__":
    asyncio.run(savetojson())
