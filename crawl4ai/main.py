import os
import asyncio
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy, CacheMode, LLMExtractionStrategy


# Pydantic model for data schema, for LLM Extraction Strategy
class ProductData(BaseModel):
    name: str
    price: str

# Data Schema for CSS Extraction Strategy
schema = {
    "name": "Product Block",
    "baseSelector": 'a.a-link-normal',
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": "span.a-price", "type": "text"},
    ]        
}    

async def main():

    # Product listings page which we need to scrape
    amazon_product_URL = "https://www.amazon.com/s?k=mobile+phone&crid=370OJ37JU1BF1&sprefix=mobile+pho%2Caps%2C353&ref=nb_sb_noss_2";

    # Load the .env file
    load_dotenv()

    # True for LLM Extraction, False for CSS Extraction
    use_llm = False

    # Browser configuration
    session_name = "amazon_mobile_phone"
    browser_config = BrowserConfig(
        headless=False,
        viewport_width=1280,
        viewport_height=720,
        verbose=True,
    )

    # LLM Extraction Strategy
    llm_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY"),
            schema=ProductData.model_json_schema(),
            extraction_type="schema",
            instruction="Extract product name and price from the content.",
            chunk_token_threshold=1000,
            overlap_rate=0.0,
            apply_chunking=True,
            input_format="markdown",
            extra_args={"temperature": 0.1, "max_tokens": 800},        
        )    

    # Local LLM Extraction Strategy
    # Chunking does not seem to work well with local LLM
    local_llm_strategy = LLMExtractionStrategy(
            provider="openai/text-completion",
            schema=ProductData.model_json_schema(),
            extraction_type="schema",
            instruction="Extract product name and price from the content.",
            api_base="http://localhost:1234/v1",
            model="qwen2.5-coder-14b-instruct",  
            chunk_token_threshold=1000,
            overlap_rate=0.0,
            apply_chunking=True,
            input_format="markdown",
            extra_args={"temperature": 0.1, "max_tokens": 800},        
        )         

    # Init the web crawler with the browser configuration
    async with AsyncWebCrawler(config=browser_config) as crawler: 

        # Pagination JavaScript
        load_nextpage_js = ["document.getElementsByClassName('s-pagination-item s-pagination-next')[0].click();"]    

        # Wait for 
        wait_for_code = """() => document.getElementsByClassName('s-main-slot s-result-list s-search-results sg-row')[0].childElementCount > 10"""

        # Crawl multiple pages
        for page in range(3):

            # Crawler configuration
            crawler_config = CrawlerRunConfig(
                js_only=True if page > 0 else False,
                js_code=load_nextpage_js if page > 0 else None,
                extraction_strategy= llm_strategy if use_llm else JsonCssExtractionStrategy(schema),
                css_selector='div[role="listitem"]',
                session_id=session_name,
                wait_for=wait_for_code if page > 0 else None,
                cache_mode=CacheMode.BYPASS,
                exclude_external_links=True,
                exclude_social_media_links=True
            )

            # Crawl
            result = await crawler.arun(
                url=amazon_product_URL,
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