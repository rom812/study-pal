"""Simple test to debug the scraper issue."""

from dotenv import load_dotenv
from agents.quote_scraper import WebSearchQuoteScraper

load_dotenv(override=True)

def main():
    scraper = WebSearchQuoteScraper()

    print("Testing quote scraper...")
    quotes = scraper.scrape_quotes("Kim Kardeshian", limit=2)

    print(f"\nReturned type: {type(quotes)}")
    print(f"Number of quotes: {len(quotes)}")

    for i, quote in enumerate(quotes, 1):
        print(f"\n--- Quote {i} ---")
        print(f"Type: {type(quote)}")
        print(f"Quote object: {quote}")
        if hasattr(quote, 'text'):
            print(f"Text: {quote.text}")
            print(f"Persona: {quote.persona}")
            print(f"Tags: {quote.tags}")
        else:
            print(f"WARNING: Not a Quote object!")

if __name__ == "__main__":
    main()
