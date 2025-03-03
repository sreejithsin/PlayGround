import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy, CacheMode

async def main():

    session_name = "amazon_mobile_phone";

    # Data Schema
    schema = {
        "name": "Product Block",
        "baseSelector": 'a.a-link-normal',
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "price", "selector": "span.a-price", "type": "text"},
        ]        
    }

    # Browser configuration
    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1280,
        viewport_height=720,
        verbose=True,
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        session_id=session_name
    )

    # Run the crawler
    async with AsyncWebCrawler(config=browser_config) as crawler: 

        # Pagination JavaScript
        load_nextpage_js = ["document.getElementsByClassName('s-pagination-item s-pagination-next')[0].click();"]            
        # Wait for 
        wait_for_code = """() => document.getElementsByClassName('s-main-slot s-result-list s-search-results sg-row')[0].childElementCount > 10"""

        # Crawl multiple pages
        for page in range(3):

            # Crawler configuration
            crawler_config = CrawlerRunConfig(
                js_code=load_nextpage_js if page > 0 else None,
                js_only=True if page > 0 else False,
                extraction_strategy=JsonCssExtractionStrategy(schema),
                session_id=session_name,
                wait_for=wait_for_code if page > 0 else None,
                cache_mode=CacheMode.BYPASS
            )

            # Crawl
            result = await crawler.arun(
                url="https://www.amazon.com/s?k=mobile+phone&crid=370OJ37JU1BF1&sprefix=mobile+pho%2Caps%2C353&ref=nb_sb_noss_2",
                config=crawler_config
            )

            # Data
            if result.success:
                print (f"Success: Page {page+1}")
                products = json.loads(result.extracted_content)
                print(products[:5])
            else:
                print("Error:", result.error_message)   

if __name__ == "__main__":
    asyncio.run(main())