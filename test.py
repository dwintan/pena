from scraper.kabar import scrape_search

df = scrape_search(
    keyword="stunting",
    start_date="2026-01-01",
    end_date="2026-08-31"
)

print(df.head())